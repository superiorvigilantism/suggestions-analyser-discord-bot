# Load logger object from init_logger.py
from init_logger import logger

# Import discord API library
import discord
from discord.ext import commands

# Import bot object from init_discord.py
from init_discord import bot

# Import env vars from fetch_creds.py
from fetch_creds import DISCORD_TOKEN

# Import discord commands from discord_cmds.py
from discord_cmds import cmd_help, set_forward_channel, set_forum_channel, set_threshold, set_prompt, prompt_info

# Import function on_thread_create from read_send_msgs.py
from read_send_msgs import on_thread_create

# Import database functions and update_server_data from database.py
from database import init_db, close_db, update_server_data

# Import env vars from fetch_creds.py
from fetch_creds import DATA_DIR


# ============================================================================
# DECORATING FUNCTIONS
# ============================================================================

# DECORATING EVENT: New Forum Post (Thread)

# @bot.event
on_thread_create = bot.event(on_thread_create)

# DECORATING COMMAND: Help

# @bot.command(name='help')
# @commands.is_owner()
cmd_help = commands.is_owner()(cmd_help)
cmd_help = bot.command(name='help')(cmd_help)


# DECORATING COMMAND: Set Forward Channel

# @bot.command(name='setforward')
# @commands.is_owner()
set_forward_channel = commands.is_owner()(set_forward_channel)
set_forward_channel = bot.command(name='setforward')(set_forward_channel)

# DECORATING COMMAND: Set Forum Channel

# @bot.command(name='setforum')
# @commands.is_owner()
set_forum_channel = commands.is_owner()(set_forum_channel)
set_forum_channel = bot.command(name='setforum')(set_forum_channel)

# DECORATING COMMAND: Set Threshold

# @bot.command(name='threshold')
# @commands.is_owner()
set_threshold = commands.is_owner()(set_threshold)
set_threshold = bot.command(name='threshold')(set_threshold)

# DECORATING COMMAND: Set Custom Prompt

# @bot.command(name='prompt')()
# @commands.is_owner()
set_prompt = commands.is_owner()(set_prompt)
set_prompt = bot.command(name='prompt')(set_prompt)

# DECORATING COMMAND: View Current Prompt

# @bot.command(name='promptinfo')
# @commands.is_owner()
prompt_info = commands.is_owner()(prompt_info)
prompt_info = bot.command(name='promptinfo')(prompt_info)

# ==================================================
# FUNCTIONS: on_ready, on_error, on_guild_join
# ==================================================

@bot.event
async def on_ready():
    # Init the db on startup
    try:
        await init_db()
        logger.info(f"Bot is running")
    except Exception as e:
        logger.error(f"Error occured: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    # Close the db in case of an error, not sure if KeyboardInterrupt and/or ctrl+C are supported
    await close_db()
    logger.error(f"Error occured in {event} {args} {kwargs}")

@bot.event
async def on_guild_join(guild):
    try:
        await update_server_data(guild.id)
        pass
    except discord.Forbidden:
        logger.error(f"Missing permissions in {guild.name}")
    except Exception as e:
        logger.error(f"Error occured: {e}")

# ==================================================
# * * *
# ==================================================

if __name__ == '__main__':
    logger.info('Initializing database')
    bot.run(DISCORD_TOKEN)
