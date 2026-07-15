import discord

# Import bot object from init_discord.py
from init_discord import bot

# For timestamps in embed discord messages
from datetime import datetime

# Load logger object from init_logger.py
from init_logger import logger

# Import config from config.py
from config import config

# Import env vars from fetch_creds.py
from fetch_creds import FORUM_CHANNEL_ID, PRIVATE_CHANNEL_ID

# Import rate_suggestion function from rate_suggestion.py
from rate_suggestion import rate_suggestion




# ============================================================================
# EVENT: New Forum Post (Thread)
# ============================================================================

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
        
        # Abort rating the suggestion if a critical error occured
        if not rating.get('success', False):
            return
        
        score = rating['score']
        reasoning = rating['reasoning']
        
        logger.info(f"Score: {score}/10 - "
                     "{'FORWARDING' if score >= config['threshold'] else 'REJECTED'}")
        
        # Check threshold and forward if approved
        if score >= config['threshold']:
            await send_to_private_channel(
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
# FUNCTION: Send a message to the private channel, mostly validated suggestions
# ============================================================================

# This whole function is to be fundamentally rewritten in future versions
# as the bot gains more types of messages to send.

# (author, score, reasoning, thread_url) - can be None if the message to be sent is an error and 
# not a forwarded suggestion
async def send_to_private_channel(title: str, author: discord.User, content: str, 
                                     score: float, reasoning: str, thread_url: str, is_error=False):
    """
    Send a message to the private channel. For now, it is either a suggestion forwarded or an error
    """
    try:
        private_channel = bot.get_channel(PRIVATE_CHANNEL_ID)
        if not private_channel:
            logger.error(f"Private channel {PRIVATE_CHANNEL_ID} not found")
            return

        if is_error:
            # Build error message
            embed = discord.Embed(title=title,
                description=content[:2048] if len(content) <= 2048 else content[:2045] + "...",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Action Required",
                value="Bot cannot rate suggestions until this issue is resolved.",
                inline=False
            )

            await private_channel.send(embed=embed)
            logger.info(f"Reported an error to the private channel.")

        else:
            # Build forwarded message
            embed = discord.Embed(
                title=f"✓ Approved: {title}",
                description=content[:2048] if len(content) <= 2048 else content[:2045] + "...",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Score", value=f"{score:.1f}/10", inline=False)
            if len(reasoning) > 1024:
                reasoning = reasoning[:1021] + "..."
            embed.add_field(name="AI Reasoning", value=reasoning, inline=False)
            embed.add_field(name="Suggested By", value=f"{author.mention} ({author})", inline=False)
            embed.add_field(name="Original Post", value=f"[View in Forum]({thread_url})", inline=False)
            
            await private_channel.send(embed=embed)
            logger.info(f"Forwarded '{title}' (score: {score}) to private channel")
    
    except Exception as e:
        logger.error(f"Error forwarding to private channel: {e}")
