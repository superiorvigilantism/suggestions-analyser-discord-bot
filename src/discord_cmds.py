import discord

# Load logger object from init_logger.py
from init_logger import logger

# Import the get_server_data and update_server_data functions from database.py
from database import get_server_data, update_server_data


async def cmd_help(ctx):
    """
    Command: <prefix>help
    View help on other commands
    """
    await ctx.send(
         "Command: <prefix>help\n"
         "View help on other commands"
        f"{set_forward_channel.__doc__}"
        f"{set_forum_channel.__doc__}"
        f"{set_threshold.__doc__}"
        f"{set_prompt.__doc__}"
        f"{prompt_info.__doc__}"
        # f"{.__doc__}"
    )


async def set_forward_channel(ctx, ch_link: str):
    """Command: <prefix>setforward <channel link or id>"""
    ch_id = ch_link.rstrip('/').split('/')[-1]
    if ch_id.isnumeric():
        channel = ctx.bot.get_channel(int(ch_id))
    else:
        await ctx.send(f"❌ Channel not found likely because of channel ID (last number in the link) "
                        "not being entirely numeric (impossible for correct IDs)")
        return
    if channel is not None:
        await ctx.send(f"Channel found: {channel.mention}")
        await update_server_data(ctx.guild.id, forward_channel_id=int(ch_id))
    else:
        await ctx.send("❌ Channel not found")



async def set_forum_channel(ctx, ch_link: str):
    """Command: <prefix>setforum <channel link>"""
    ch_id = ch_link.rstrip('/').split('/')[-1]
    if ch_id.isnumeric():
        channel = ctx.bot.get_channel(int(ch_id))
    else:
        await ctx.send(f"❌ Channel not found likely because of channel ID (last number in the link) "
                        "not being entirely numeric (impossible for correct IDs)")
        return
    if channel is not None:
        await ctx.send(f"Channel found: {channel.mention}.\n"
                       f"Be aware that if the channel is not a forum, "
                       f"this command will not work properly")
        await update_server_data(ctx.guild.id, forum_channel_id=int(ch_id))
    else:
        await ctx.send("❌ Channel not found")


async def set_threshold(ctx, value: float):
    """
    Command: <prefix>threshold <number>
    Set the rating threshold. Only bot owner can use.
    """
    if value < 0 or value > 10:
        await ctx.send("Threshold must be between 0 and 10.")
        return
    
    await update_server_data(ctx.guild.id, threshold=value)
    logger.info(f"Threshold updated to {value} by {ctx.author}")
    await ctx.send(f"✓ Threshold updated to **{value}/10**")


async def set_prompt(ctx):
    """
    Command: <prefix>prompt <text>
    Set a custom rating prompt. Only bot owner can use for now
    The prompt will be saved to config.json and used for all future ratings
    """
    prompt_text = ctx.message.content[len(ctx.prefix) + len('prompt'):].strip()
    
    if not prompt_text:
        await ctx.send(
            "❌ Please provide a prompt.\n"
            f"Usage: `<prefix>prompt <your prompt text>`\n\n"
            f"to view current prompt, run <prefix>promptinfo"
        )
        return
    
    if len(prompt_text) > 2048:
        await ctx.send("❌ Prompt is too long (max 2048 characters)."
                       "In future, "
                       "loading prompt with file to bypass discord symbol limit will be added")
        return
    
    await update_server_data(ctx.guild.id, prompt=prompt_text)
    logger.info(f"Custom prompt set by {ctx.author}")
    
    await ctx.send(
        f"✓ Custom prompt saved to database\n\n"
        f"**Preview:** {prompt_text[:150]}{'...' if len(prompt_text) > 150 else ''}"
    )


async def prompt_info(ctx):
    """
    View the current prompt being used.
    command: <prefix>promptinfo
    """
    current_prompt = await get_server_data(ctx.guild.id)
    print(current_prompt)
    current_prompt = current_prompt.prompt
    prompt_source = "Database"
    
    embed = discord.Embed(
        title="Current Rating Prompt",
        description=current_prompt[:4096],
        color=discord.Color.blue()
    )
    embed.add_field(name="Source", value=prompt_source, inline=False)
    embed.add_field(name="Length", value=f"{len(current_prompt)} characters", inline=False)
    
    await ctx.send(embed=embed)
