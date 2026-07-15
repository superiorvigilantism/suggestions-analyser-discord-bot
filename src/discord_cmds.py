import discord

# Load logger object from init_logger.py
from init_logger import logger

# Import save_config function and config var from config.py
from config import save_config, config


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
    await ctx.send(f"✓ Threshold updated to **{value}/10**")


async def set_prompt(ctx):
    """
    Set a custom rating prompt. Only bot owner can use for now
    The prompt will be saved to config.json and used for all future ratings
    """
    # Get everything after "!prompt "
    prompt_text = ctx.message.content[len(ctx.prefix) + len('prompt'):].strip()
    
    if not prompt_text:
        await ctx.send(
            "❌ Please provide a prompt.\n"
            f"Usage: `!prompt <your prompt text>`\n\n"
            f"Current prompt source: "
            f"{'Custom (config.json)' if config.get('prompt') else 'Default'}"
        )
        return
    
    if len(prompt_text) > 4096:
        await ctx.send("❌ Prompt is too long (max 2048 characters).")
        return
    
    config['prompt'] = prompt_text
    save_config()
    logger.info(f"Custom prompt set by {ctx.author}")
    
    await ctx.send(
        f"✓ Custom prompt saved to config.json\n\n"
        f"**Preview:** {prompt_text[:150]}{'...' if len(prompt_text) > 150 else ''}"
    )


async def prompt_info(ctx):
    """
    View the current prompt being used.
    """
    current_prompt = config.get('prompt')
    prompt_source = "Custom (config.json)" if config.get('prompt') else "Default/prompt.txt"
    
    embed = discord.Embed(
        title="Current Rating Prompt",
        description=current_prompt[:4096],
        color=discord.Color.blue()
    )
    embed.add_field(name="Source", value=prompt_source, inline=False)
    embed.add_field(name="Length", value=f"{len(current_prompt)} characters", inline=False)
    
    await ctx.send(embed=embed)
