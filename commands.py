from utils import is_owner, scrape_website
from discord.ext import commands
import discord
from database import load_channels, save_channels
from config import SPACER1, SPACER2, EMOJISPACER1, EMOJISPACER2, EMOJIS
from logger import get_logger

logger = get_logger()

channels = load_channels()

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


@bot.command()
@commands.check(is_owner)
async def bind(ctx, url: str, role: discord.Role = None):
    channel_id = ctx.channel.id
    channels[channel_id] = {
        'url': url,
        'nations': {},
        'role': str(role.id) if role else None,
        'options': {
            'minutes_per_check': 15,
            'current_turn': 0,
            'min_unready_before_warn': 1,
            'warned_unready': False,
            'warned_timeleft': False,
            'min_time_before_warn': 60,
            'emoji_mode': True
        }
    }
    save_channels(channels)
    await ctx.send(f"Bound channel {ctx.channel.mention} to URL {url}{' with role ' + role.mention if role else ''}")


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


@bot.command()
async def unchecked(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channel_data = channels[channel_id]
        print(channel_data)  # Add this line
        if 'nations' in channel_data:
            nations_data = channel_data['nations']
            if len(nations_data) > 0:
                if channel_data['options']['emoji_mode']:
                    table = EMOJISPACER1
                else:
                    table = SPACER1
                for nation_name, nation_info in nations_data.items():
                    status = nation_info['status']
                    if channels[channel_id]['options']['emoji_mode']:
                        status = [f"{EMOJIS.get(cell, '')} {
                            cell}" for cell in status]
                    table += f"| {'':<4} | {nation_name:<14} | {
                        ', '.join(status):<14} |\n"
                if channel_data['options']['emoji_mode']:
                    table += EMOJISPACER2
                else:
                    table += SPACER2
                output = f"```\n{table}\n```"
                if len(output) > 2000:
                    logger.warning(
                        f"Attempting to send large message, may exceed limits. Message length: {len(output)}")
                    messages = [output[i:i + 2000]
                                for i in range(0, len(output), 2000)]
                    for message in messages:
                        await ctx.send(message)
                else:
                    await ctx.send(output)
            else:
                await ctx.send('No nation data available')
        else:
            await ctx.send('No nation data available')
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def forcescrape(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        url = channels[channel_id]['url']
        scraped_data, table_text, game_name, nations_data = scrape_website(url)
        if scraped_data is not None and table_text is not None and game_name is not None:
            channels[channel_id]['nations'] = nations_data
            save_channels(channels)
            await ctx.send(f"Scraped website and updated nation data for channel {ctx.channel.mention}")
        else:
            await ctx.send('Failed to scrape website')
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


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


@bot.command()
@commands.check(is_owner)
async def set_minutes_per_check(ctx, minutes: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channels[channel_id]['options']['minutes_per_check'] = minutes
        save_channels(channels)
        await ctx.send(f"Set minutes per check to {minutes} for channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def set_current_turn(ctx, turn: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channels[channel_id]['options']['current_turn'] = turn
        save_channels(channels)
        await ctx.send(f"Set current turn to {turn} for channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def set_min_unready_before_warn(ctx, min_unready: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channels[channel_id]['options']['min_unready_before_warn'] = min_unready
        save_channels(channels)
        await ctx.send(f"Set minimum unready before warn to {min_unready} for channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def set_min_time_before_warn(ctx, minutes: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channels[channel_id]['options']['min_time_before_warn'] = minutes
        save_channels(channels)
        await ctx.send(f"Set minimum time before warn to {minutes} minutes for channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def toggle_emoji_mode(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channels[channel_id]['options']['emoji_mode'] = not channels[channel_id]['options']['emoji_mode']
        save_channels(channels)
        await ctx.send(f"Emoji mode is now {'on' if channels[channel_id]['options']['emoji_mode'] else 'off'} for channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def view_options(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        options = channels[channel_id]['options']
        output = f"Minutes per check: {options['minutes_per_check']}\n"
        output += f"Current turn: {options['current_turn']}\n"
        output += f"Minimum unready before warn: {
            options['min_unready_before_warn']}\n"
        output += f"Minimum time before warn: {
            options['min_time_before_warn']}\n"
        output += f"Emoji mode: {'on' if options['emoji_mode'] else 'off'}"
        await ctx.author.send(f"Options for channel {ctx.channel.mention}:\n{output}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")
