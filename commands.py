from utils.py import is_owner, scrape_website
from discord.ext import commands
import discord
import json
import os


intents = discord.Intents.default()
intents.typing = False  # Optional: set to True if your bot needs to detect typing status
# Optional: set to True if your bot needs to detect presence status
intents.presences = False
intents.members = True  # Required for server members intent
intents.message_content = True  # Required to read and send messages

bot = commands.Bot(command_prefix='?', intents=intents)

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
                    status = [f"{EMOJIS.get(cell, '')} {
                        cell}" for cell in status]
                table += f"| {nation_name:<14} | {', '.join(status):<14} |\n"
            if EMOJI_MODE:
                table += EMOJISPACER2
            else:
                table += SPACER2
            output = f"```\n{game_name}\n{table}\n{table_text}\n```"
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
