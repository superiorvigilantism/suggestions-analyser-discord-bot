# Import discord API library
import discord
from discord.ext import commands


# Initialize discord client
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
