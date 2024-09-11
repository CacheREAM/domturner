import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import logging
from config import TOKEN, OWNER_IDS
import json
import os

EMOJIS = {
    'dead': '\u274E',
    'computer': '\u274E',
    'unfinished': '❌',
    'submitted': '\u2705',
    'unsubmitted': '❌'
}

EMOJI_MODE = True

SPACER1 = "+----------------+----------------+\n| Nation Name    | Status         |\n+----------------+----------------+\n"
SPACER2 = "+----------------+----------------+\n"
EMOJISPACER1 = "+----------------+-----------------+\n| Nation Name    | Status          |\n+----------------+-----------------+\n"
EMOJISPACER2 = "+----------------+-----------------+\n"

intents = discord.Intents.default()
intents.typing = False  # Optional: set to True if your bot needs to detect typing status
intents.presences = False  # Optional: set to True if your bot needs to detect presence status
intents.members = True  # Required for server members intent
intents.message_content = True  # Required to read and send messages

bot = commands.Bot(command_prefix='?', intents=intents)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Check if user is owner
def is_owner(ctx):
    return ctx.author.id in OWNER_IDS

# Event to log commands
@bot.event
async def on_command(ctx):
    logger.info(f"Command '{ctx.command}' ran by user {ctx.author} with ID {ctx.author.id} at {ctx.message.created_at}")

# Channels file name
CHANNELS_FILE = 'channels.json'

def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            channels_json = json.load(f)
            channels = {}
            for channel_id, channel_data in channels_json.items():
                # Validate channel data
                if 'url' not in channel_data or 'nations' not in channel_data:
                    logging.warning(f"Invalid channel data for channel {channel_id}: {channel_data}")
                    continue
                channel_data['nations'] = {nation_name: nation_data for nation_name, nation_data in channel_data['nations'].items() if nation_name is not None}
                if 'options' not in channel_data:
                    channel_data['options'] = {
                        'minutes_per_check': 15,  # Default value
                        'current_turn': 0,  # Default value
                        'min_unready_before_warn': 5  # Default value
                    }
                channels[int(channel_id)] = channel_data
            return channels
    except json.JSONDecodeError as e:
        logging.error(f"Error loading channels: {e}")
        return {}

# Load channels from file
if os.path.exists(CHANNELS_FILE):
    channels = load_channels()
else:
    channels = {}

# Function to save channels to file
def save_channels(channels_param):
    try:
        channels_param_to_write = {}
        for channel_id, channel_data in channels_param.items():
            # Validate channel data before saving
            if 'url' not in channel_data or 'nations' not in channel_data:
                logger.warning(f"Invalid channel data for channel {channel_id}: {channel_data}")
                continue
            channel_data_to_write = {
                'url': channel_data['url'],
                'role': channel_data.get('role', None),
                'nations': {}
            }
            if 'options' in channel_data:
                channel_data_to_write['options'] = {
                    'minutes_per_check': channel_data['options']['minutes_per_check'],
                    'current_turn': channel_data['options']['current_turn'],
                    'min_unready_before_warn': channel_data['options']['min_unready_before_warn']
                }
            for nation_name, nation_data in channel_data['nations'].items():
                if nation_name is not None:
                    channel_data_to_write['nations'][nation_name] = {
                        'status': nation_data['status'],
                        'user': nation_data['user']
                    }
            channels_param_to_write[str(channel_id)] = channel_data_to_write
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels_param_to_write, f)
    except Exception as e:
        logger.error(f"Error saving channels: {e}")

# Command to bind a channel to a URL
@bot.command()
@commands.check(is_owner)
async def bind(ctx, url: str, role: discord.Role):
    channel_id = ctx.channel.id
    channels[channel_id] = {'url': url, 'nations': {}, 'role': str(role.id)}
    save_channels(channels)
    await ctx.send(f"Bound channel {ctx.channel.mention} to URL {url} with role {role.mention}")

# Command to remove a bound channel
@bot.command()
@commands.check(is_owner)
async def unbind(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        del channels[channel_id]
        save_channels(channels)
        await ctx.send(f"Unbound channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")

# Function to scrape website
def scrape_website(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # Set encoding to UTF-8
        soup = BeautifulSoup(response.text, 'html.parser')
        nation_name_cells = soup.find_all('td', class_='nation-name wide-column')
        scraped_data = []
        nations_data = {}
        for cell in nation_name_cells:
            nation_name = cell.find('b').text.strip() if cell.find('b') else None
            status_cells = cell.parent.find_all('td', class_=lambda x: x in ['submitted', 'unsubmitted', 'unfinished', 'computer', 'dead'])
            status = [cell.text.strip() for cell in status_cells]
            scraped_data.append((nation_name, status))
            nations_data[nation_name] = {'status': status, 'user': None}
        # Get the text from the striped-table inside the pane status div
        striped_table = soup.find('div', class_='pane status').find('table', class_='striped-table')
        table_text = ''
        for row in striped_table.find_all('tr'):
            cells = row.find_all('td')
            for cell in cells:
                table_text += cell.text.strip() + '\n'
        # Get the game name
        game_name = soup.find('h1').text.strip()
        return scraped_data, table_text, game_name, nations_data
    except Exception as e:
        logger.error(f'Error: {e}')
        return None, None, None, None

# Command to scrape website
@bot.command()
async def unchecked(ctx):
    global EMOJI_MODE
    channel_id = ctx.channel.id
    if channel_id in channels:
        url = channels[channel_id]['url']
        scraped_data, table_text, game_name, nations_data = scrape_website(url)
        if scraped_data is not None and table_text is not None and game_name is not None:
            channels[channel_id]['nations'] = nations_data
            save_channels(channels)
            if EMOJI_MODE:
                table = EMOJISPACER1
            else:
                table = SPACER1
            for nation_name, status in scraped_data:
                if nation_name is None:
                    nation_name = 'Failed to scrape nation name'
                if EMOJI_MODE:
                    status = [f"{EMOJIS.get(cell, '')} {cell}" for cell in status]
                table += f"| {nation_name:<14} | {', '.join(status):<14} |\n"
            if EMOJI_MODE:
                table += EMOJISPACER2
            else:
                table += SPACER2
            output = f"```\n{game_name}\n{table}\n{table_text}\n```"
            if len(output) > 2000:
                logger.warning(f"Attempting to send large message, may exceed limits. Message length: {len(output)}")
                messages = [output[i:i + 2000] for i in range(0, len(output), 2000)]
                for message in messages:
                    await ctx.send(message)
            else:
                await ctx.send(output)
        else:
            await ctx.send('Failed to scrape website')
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")

# Command to add a nation to a user
@bot.command()
@commands.check(is_owner)
async def addnation(ctx, nation_name: str, user: discord.Member):
    channel_id = ctx.channel.id
    if channel_id in channels:
        if nation_name in channels[channel_id]['nations']:
            channels[channel_id]['nations'][nation_name]['user'] = str(user.id)
            save_channels(channels)
            await ctx.send(f"Added nation {nation_name} to user {user.mention}")
        else:
            await ctx.send(f"Nation {nation_name} not found in channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")

# Command to toggle emoji mode
@bot.command()
@commands.check(is_owner)
async def emojimode(ctx):
    global EMOJI_MODE
    EMOJI_MODE = not EMOJI_MODE
    await ctx.send(f"Emoji mode is now {'enabled' if EMOJI_MODE else 'disabled'}")

# Run the bot
bot.run(TOKEN)
