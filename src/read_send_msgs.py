import discord

# Import bot object from init_discord.py
from init_discord import bot

# For timestamps in embed discord messages
from datetime import datetime

# Load logger object from init_logger.py
from init_logger import logger

# Import rate_suggestion function from rate_suggestion.py
from rate_suggestion import rate_suggestion

# Import get_server_data functions from database.py
from database import get_server_data

# Just for specifying expected class from config
from models import ServerData


# ============================================================================
# EVENT: New Forum Post (Thread)
# ============================================================================

async def on_thread_create(thread: discord.Thread):
    """
    Triggered when a new thread is created in the forum.
    Read the opening message, rate it, and forward if threshold met.
    """
    try:
        # Fetch the config of particular guild from which the thread came
        logger.info(f"Thread created: {thread}")
        config = await get_server_data(thread.guild.id)
        logger.info(f"Received guild row: {config}")
        # Check if the channels to listen and to forward to were specified, if not then ignore
        if (not config.forward_channel_id) and (not config.forum_channel_id):

            return
        logger.info(f"Channels are specified")
        # Verify this thread is in the target forum channel
        if thread.parent_id != config.forum_channel_id:
            logger.info(f"Thread not in the forum channel, {thread.parent_id} != {config.forum_channel_id}")
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
        rating = await rate_suggestion(config.prompt, title, content)
        
        # Abort rating the suggestion if a critical error occured
        if not rating.get('success', False):
            await send_to_forward_channel(
                forward_channel_id=config.forward_channel_id, 
                title=f"🚨 CRITICAL ERROR:", 
                author=None, 
                content=rating.get('reasoning', 'Unknown error'), 
                score=None, 
                reasoning=None, 
                thread_url=None, 
                is_error=True
                )
            return
        
        score = rating['score']
        reasoning = rating['reasoning']
        
        logger.info(f"Score: {score}/10 - "
                     "{'FORWARDING' if score >= config['threshold'] else 'REJECTED'}")
        
        # Check threshold and forward if approved
        if score >= config.threshold:
            await send_to_forward_channel(
                forward_channel_id=config.forward_channel_id,
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
async def send_to_forward_channel(forward_channel_id: int, title: str, author: discord.User, content: str, 
                                     score: float, reasoning: str, thread_url: str, is_error=False):
    """
    Send a message to the private channel. For now, it is either a suggestion forwarded or an error
    """
    try:
        channel = bot.get_channel(forward_channel_id)
        if not channel:
            logger.error(f"Private channel {forward_channel_id} not found")
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

            await channel.send(embed=embed)
            logger.info(f"Reported an error to the private channel.")

        else:
            # Build forward message
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
            
            await channel.send(embed=embed)
            logger.info(f"Forwarded '{title}' (score: {score}) to private channel")
    
    except Exception as e:
        logger.error(f"Error forwarding to private channel: {e}")
