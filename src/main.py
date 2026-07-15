# Load logger object from init_logger.py
from init_logger import logger

# Import discord API library
import discord
from discord.ext import commands

# Import bot object from init_discord.py
from init_discord import bot

# Import env vars from fetch_creds.py
from fetch_creds import DISCORD_TOKEN

# Import config functions "load" and "save" and config var from config.py
from config import load_config, save_config, config

# Import discord commands from discord_cmds.py
from discord_cmds import set_threshold, set_prompt, prompt_info

# Import function on_thread_create from read_send_msgs.py
from read_send_msgs import on_thread_create

# Import env vars from fetch_creds.py
from fetch_creds import FORUM_CHANNEL_ID, PRIVATE_CHANNEL_ID, DATA_DIR


# ============================================================================
# DECORATING FUNCTIONS
# ============================================================================

# DECORATING EVENT: New Forum Post (Thread)

# @bot.event
on_thread_create = bot.event(on_thread_create)

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
# FUNCTION: Bot ready up
# ==================================================

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Monitoring forum channel: {FORUM_CHANNEL_ID}")
    logger.info(f"Forwarding to private channel: {PRIVATE_CHANNEL_ID}")
    logger.info(f"Current threshold: {config['threshold']}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Custom prompt active: {bool(config.get('prompt'))}")

# ==================================================
# * * *
# ==================================================

if __name__ == '__main__':
    # Load the config on startup
    load_config()
    bot.run(DISCORD_TOKEN)
