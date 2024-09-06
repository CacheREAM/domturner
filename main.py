import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import logging
from config import TOKEN, OWNER_IDS

intents = discord.Intents.default()
intents.typing = False  # Optional: set to True if your bot needs to detect typing status
intents.presences = False  # Optional: set to True if your bot needs to detect presence status
intents.members = True  # Required for server members intent
intents.message_content = True  # Required to read and send messages

bot = commands.Bot(command_prefix='?', intents=intents)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Function to scrape website
def scrape_website(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # Set encoding to UTF-8
        soup = BeautifulSoup(response.text, 'html.parser')
        nation_name_cells = soup.find_all('td', class_='nation-name wide-column')
        scraped_data = []
        for cell in nation_name_cells:
            nation_name = cell.find('b').text.strip() if cell.find('b') else None
            status_cells = cell.parent.find_all('td', class_=lambda x: x in ['submitted', 'unsubmitted', 'unfinished', 'computer', 'dead'])
            status = [cell.text.strip() for cell in status_cells]
            scraped_data.append((nation_name, status))
        return scraped_data
    except Exception as e:
        logger.error(f'Error: {e}')
        return None

# Check if user is owner
def is_owner(ctx):
    return ctx.author.id in OWNER_IDS

# Command to scrape website
@bot.event
async def on_command(ctx):
    logger.info(f"Command '{ctx.command}' ran by user {ctx.author} with ID {ctx.author.id} at {ctx.message.created_at}")

# Command to scrape website
@bot.command()
@commands.check(is_owner)
async def scrape(ctx, url: str):
    scraped_data = scrape_website(url)
    if scraped_data is not None:
        data_to_send = ''
        for nation_name, status in scraped_data:
            if nation_name is None:
                data_to_send += 'Failed to scrape nation name\n'
            else:
                data_to_send += f'Nation Name: {nation_name}\nStatus: {", ".join(status)}\n\n'
        if len(data_to_send) > 2000:
            logger.warning(f"Attempting to send large message, may exceed limits. Message length: {len(data_to_send)}")
            messages = [data_to_send[i:i + 2000] for i in range(0, len(data_to_send), 2000)]
            for message in messages:
                await ctx.send(message)
        else:
            await ctx.send(data_to_send)
    else:
        await ctx.send('Failed to scrape website')

# Run the bot
bot.run(TOKEN)
