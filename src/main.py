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

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
PRIVATE_CHANNEL_ID = int(os.getenv('PRIVATE_CHANNEL_ID'))
DEFAULT_THRESHOLD = float(os.getenv('DEFAULT_THRESHOLD', 6.0))

# Ensure data directory exists at project root (parent of src/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up to project root
DATA_DIR = os.path.join(project_root, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
PROMPT_FILE = os.path.join(DATA_DIR, 'prompt.txt')

# Initialize clients
client = openai.OpenAI(api_key=OPENAI_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Runtime config (loaded from persistent storage)
config = {
    'threshold': DEFAULT_THRESHOLD,
    'prompt': None  # Custom prompt stored here
}

# ============================================================================
# PERSISTENT CONFIG FUNCTIONS
# ============================================================================

def load_config():
    """Load threshold and prompt from config.json. Create with defaults if missing."""
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                config['threshold'] = loaded.get('threshold', DEFAULT_THRESHOLD)
                config['prompt'] = loaded.get('prompt', None)
                logger.info(f"Config loaded from {CONFIG_FILE}: threshold={config['threshold']}, custom_prompt={'Yes' if config['prompt'] else 'No'}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}. Using defaults.")
            config['threshold'] = DEFAULT_THRESHOLD
            config['prompt'] = None
    else:
        logger.info(f"No config file found. Creating {CONFIG_FILE} with defaults.")
        save_config()

def save_config():
    """Save threshold and prompt to config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def load_prompt():
    """
    Load system prompt in order of priority:
    1. Custom prompt from config.json
    2. Prompt from prompt.txt file
    3. Hardcoded fallback
    """
    # Priority 1: Custom prompt in config.json
    if config.get('prompt'):
        logger.info("Using custom prompt from config.json")
        return config['prompt']
    
    # Priority 2: Prompt file
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, 'r') as f:
                prompt = f.read().strip()
                if prompt:
                    logger.info(f"Using prompt from {PROMPT_FILE}")
                    return prompt
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
    
    # Priority 3: Fallback
    logger.warning("Using fallback prompt")
    return "You are a critical game design reviewer. Rate the following game suggestion on a scale of 0-10. Be honest and direct. Respond with: Score: X/10\nReasoning: ..."

# ============================================================================
# CRITICAL ERROR ALERT
# ============================================================================

async def send_critical_alert(error_title: str, error_detail: str):
    """
    Send a critical error alert to the private channel.
    Used for API quota exhaustion, auth failures, etc.
    """
    try:
        private_channel = bot.get_channel(PRIVATE_CHANNEL_ID)
        if not private_channel:
            logger.error(f"Cannot send critical alert: private channel {PRIVATE_CHANNEL_ID} not found")
            return
        
        embed = discord.Embed(
            title=f"🚨 CRITICAL ERROR: {error_title}",
            description=error_detail,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="Action Required",
            value="Bot cannot rate suggestions until this issue is resolved.",
            inline=False
        )
        
        await private_channel.send(embed=embed)
        logger.error(f"Critical alert sent: {error_title}")
    
    except Exception as e:
        logger.error(f"Failed to send critical alert: {e}")

def is_critical_error(error: Exception) -> bool:
    """
    Determine if an OpenAI error is critical (should halt rating).
    Returns True for auth, quota, rate limit, and model errors.
    """
    error_str = str(error).lower()
    critical_keywords = [
        'invalid api key',
        'authentication',
        'quota exceeded',
        'insufficient_quota',
        'rate limit',
        'billing',
        'api_error',
        'model_not_found',
        'internal_error'
    ]
    return any(keyword in error_str for keyword in critical_keywords)

# ============================================================================
# AI RATING FUNCTION
# ============================================================================

async def rate_suggestion(title: str, content: str) -> dict:
    """
    Send suggestion to OpenAI for rating.
    Returns: {'score': float, 'reasoning': str, 'success': bool}
    """
    try:
        system_prompt = load_prompt()
        user_message = f"Suggestion Title: \n{title}\n\nSuggestion Content:\n{content}"
        
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
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
        error_msg = str(e)
        logger.error(f"OpenAI API error: {error_msg}")
        
        # Check if this is a critical error that requires alerting
        if is_critical_error(e):
            logger.critical(f"CRITICAL OpenAI error detected: {error_msg}")
            return {'score': None, 'reasoning': error_msg, 'success': False, 'critical': True}
        
        return {'score': None, 'reasoning': error_msg, 'success': False, 'critical': False}

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
        
        # Handle critical errors
        if rating.get('critical', False):
            await send_critical_alert(
                error_title="OpenAI API Failure",
                error_detail=f"**Error:** {rating['reasoning']}\n\n**Action:** Check API key, billing, and quota at https://platform.openai.com/account/billing/overview"
            )
            return
        
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
# COMMAND: Set Threshold
# ============================================================================

@bot.command(name='threshold')
@commands.is_owner()
async def set_threshold(ctx, value: float):
    """
    Set the rating threshold. Only bot owner can use.
    Usage: !threshold 7.0
    Persists across restarts.
    """
    if value < 0 or value > 10:
        await ctx.send("Threshold must be between 0 and 10.")
        return
    
    config['threshold'] = value
    save_config()
    logger.info(f"Threshold updated to {value} by {ctx.author}")
    await ctx.send(f"✓ Threshold updated to **{value}/10** (saved)")

# ============================================================================
# COMMAND: Set Custom Prompt
# ============================================================================

@bot.command(name='prompt')
@commands.is_owner()
async def set_prompt(ctx):
    """
    Set a custom rating prompt. Only bot owner can use.
    Usage: !prompt <your prompt text here>
    
    The prompt will be saved to config.json and used for all future ratings.
    Multi-line prompts are supported.
    """
    # Get everything after "!prompt "
    prompt_text = ctx.message.content[len(ctx.prefix) + len('prompt'):].strip()
    
    if not prompt_text:
        await ctx.send(
            "❌ Please provide a prompt.\n"
            f"Usage: `!prompt <your prompt text>`\n\n"
            f"Current prompt source: "
            f"{'Custom (config.json)' if config.get('prompt') else 'Fallback/prompt.txt'}"
        )
        return
    
    if len(prompt_text) > 2000:
        await ctx.send("❌ Prompt is too long (max 2000 characters).")
        return
    
    config['prompt'] = prompt_text
    save_config()
    logger.info(f"Custom prompt set by {ctx.author}")
    
    await ctx.send(
        f"✓ Custom prompt saved to config.json\n\n"
        f"**Preview:** {prompt_text[:150]}{'...' if len(prompt_text) > 150 else ''}"
    )

# ============================================================================
# COMMAND: View Current Prompt
# ============================================================================

@bot.command(name='promptinfo')
@commands.is_owner()
async def prompt_info(ctx):
    """
    View the current prompt being used.
    """
    current_prompt = load_prompt()
    prompt_source = "Custom (config.json)" if config.get('prompt') else "Default/prompt.txt"
    
    embed = discord.Embed(
        title="Current Rating Prompt",
        description=current_prompt[:2048],
        color=discord.Color.blue()
    )
    embed.add_field(name="Source", value=prompt_source, inline=False)
    embed.add_field(name="Length", value=f"{len(current_prompt)} characters", inline=False)
    
    await ctx.send(embed=embed)

# ============================================================================
# BOT READY
# ============================================================================

@bot.event
async def on_ready():
    load_config()  # Load saved threshold and prompt
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Monitoring forum channel: {FORUM_CHANNEL_ID}")
    logger.info(f"Forwarding to private channel: {PRIVATE_CHANNEL_ID}")
    logger.info(f"Current threshold: {config['threshold']}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Custom prompt active: {bool(config.get('prompt'))}")

# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    load_config()  # Load on startup
    bot.run(DISCORD_TOKEN)