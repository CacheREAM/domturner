import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.message_content = True
intents.guilds = True  # Required to cache guilds, needed for role mentions
intents.bans = False  # Optional
intents.emojis = True  # Optional
intents.integrations = False  # Optional
intents.invites = False  # Optional
intents.voice_states = False  # Optional
intents.reactions = True  # Required to cache messages and reactions
intents.messages = True  # Optional, enables cache for messages
intents.emojis_and_stickers = True  # Required for emoji and sticker intents

bot = commands.Bot(command_prefix='?', intents=intents)
