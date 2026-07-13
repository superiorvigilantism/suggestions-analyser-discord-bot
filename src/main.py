import os
import json
import logging
from datetime import datetime
import discord
from discord.ext import commands
import openai

# ============================================================================
# SETUP & CONFIG
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GameBot')

# Load from environment variables

from dotenv import load_dotenv
import os

# Load .env file into system environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
PRIVATE_CHANNEL_ID = int(os.getenv('PRIVATE_CHANNEL_ID'))
DEFAULT_THRESHOLD = float(os.getenv('DEFAULT_THRESHOLD', 6.0))

# Initialize clients
client = openai.OpenAI(api_key=OPENAI_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Runtime config (threshold can be changed via command)
config = {
    'threshold': DEFAULT_THRESHOLD
}

# ============================================================================
# AI RATING FUNCTION
# ============================================================================

async def rate_suggestion(title: str, content: str) -> dict:
    """
    Send suggestion to OpenAI for rating.
    Returns: {'score': float, 'reasoning': str, 'success': bool}
    """

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        file_path = os.path.join(project_root, 'data', 'prompt.txt')

        with open(file_path, 'r') as file:
            system_prompt = file.read()

        
        user_message = f"Suggestion Title: \n{title}\n\nSuggestion Content:\n{content}"
        
        response = client.chat.completions.create(
            model='gpt-5.4-nano',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        # Parse response (expects format like "Score: 7/10\nReasoning: ...")
        response_text = response.choices[0].message.content.strip()
        lines = response_text.split('\n')
        
        score = None
        reasoning = response_text
        
        for line in lines:
            if 'score' in line.lower():
                try:
                    # Extract number from "Score: 7/10" or similar
                    parts = line.split(':')
                    if len(parts) > 1:
                        num_part = parts[1].strip().split('/')[0].strip()
                        score = float(num_part)
                        break
                except (ValueError, IndexError):
                    pass
        
        if score is None:
            logger.warning(f"Could not parse score from: {response_text}")
            return {'score': None, 'reasoning': response_text, 'success': False}
        
        return {'score': score, 'reasoning': reasoning, 'success': True}
    
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {'score': None, 'reasoning': str(e), 'success': False}

# ============================================================================
# EVENT: New Forum Post (Thread)
# ============================================================================

@bot.event
async def on_thread_create(thread: discord.Thread):
    """
    Triggered when a new thread is created in the forum.
    Read the opening message, rate it, and forward if threshold met.
    """
    try:
        # Verify this thread is in the target forum channel
        if thread.parent_id != FORUM_CHANNEL_ID:
            return
        
        logger.info(f"New forum post detected: '{thread.name}' by {thread.owner}")
        
        # Fetch the opening message (first message in thread)
        async for message in thread.history(limit=1, oldest_first=True):
            opening_message = message
            break
        
        if not opening_message:
            logger.warning(f"Could not fetch opening message for thread {thread.id}")
            return
        
        title = thread.name
        content = opening_message.content
        author = opening_message.author
        
        # Rate the suggestion
        logger.info(f"Rating suggestion: {title}")
        rating = await rate_suggestion(title, content)
        
        if not rating['success']:
            logger.error(f"Rating failed for {title}: {rating['reasoning']}")
            return
        
        score = rating['score']
        reasoning = rating['reasoning']
        
        logger.info(f"Score: {score}/10 - {'FORWARDING' if score >= config['threshold'] else 'REJECTED'}")
        
        # Check threshold and forward if approved
        if score >= config['threshold']:
            await forward_to_private_channel(
                title=title,
                author=author,
                content=content,
                score=score,
                reasoning=reasoning,
                thread_url=thread.jump_url
            )
    
    except Exception as e:
        logger.error(f"Error processing thread: {e}")

# ============================================================================
# FORWARDING FUNCTION
# ============================================================================

async def forward_to_private_channel(title: str, author: discord.User, content: str, 
                                     score: float, reasoning: str, thread_url: str):
    """
    Forward approved suggestion to private channel with rating info.
    """
    try:
        private_channel = bot.get_channel(PRIVATE_CHANNEL_ID)
        if not private_channel:
            logger.error(f"Private channel {PRIVATE_CHANNEL_ID} not found")
            return
        
        # Build forwarded message
        embed = discord.Embed(
            title=f"✓ Approved: {title}",
            description=content[:2048] if len(content) <= 2048 else content[:2045] + "...",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Score", value=f"{score:.1f}/10", inline=False)
        embed.add_field(name="AI Reasoning", value=reasoning[:1024] if len(reasoning) <= 1024 else reasoning[:1021] + "...", inline=False)
        embed.add_field(name="Suggested By", value=f"{author.mention} ({author})", inline=False)
        embed.add_field(name="Original Post", value=f"[View in Forum]({thread_url})", inline=False)
        
        await private_channel.send(embed=embed)
        logger.info(f"Forwarded '{title}' (score: {score}) to private channel")
    
    except Exception as e:
        logger.error(f"Error forwarding to private channel: {e}")

# ============================================================================
# COMMAND: Set Threshold (DM or command)
# ============================================================================

@bot.command(name='threshold')
@commands.is_owner()
async def set_threshold(ctx, value: float):
    """
    Set the rating threshold. Only bot owner can use.
    Usage: !threshold 7.0
    """
    if value < 0 or value > 10:
        await ctx.send("Threshold must be between 0 and 10.")
        return
    
    config['threshold'] = value
    logger.info(f"Threshold updated to {value} by {ctx.author}")
    await ctx.send(f"✓ Threshold updated to **{value}/10**")

# ============================================================================
# BOT READY
# ============================================================================

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Monitoring forum channel: {FORUM_CHANNEL_ID}")
    logger.info(f"Forwarding to private channel: {PRIVATE_CHANNEL_ID}")
    logger.info(f"Current threshold: {config['threshold']}")

# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
