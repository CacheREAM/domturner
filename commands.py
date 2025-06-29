from utils import is_owner, is_not_banned, scrape_website, text_to_minutes
from discord.ext import commands
import discord
from database import save_channels
from config import SPACER1, SPACER2, EMOJISPACER1, EMOJISPACER2, EMOJIS
from logger import get_logger
from autocheck import toggle_channel_autocheck
from bot import bot
from channels import channels
import time


logger = get_logger()

usernames = {}


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
            'min_unready_before_warn': 2,
            'warned_unready': False,
            'warned_timeleft': False,
            'min_time_before_warn': 60,
            'emoji_mode': True,
            'autocheck': False
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


@bot.command(name='unchecked', aliases=['un', 'ue', 'uc', 'nations', 'status', 'undone', 'unfinished', 'unfinish', 'check', 'info'])
async def unchecked(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channel_data = channels[channel_id]
        if 'nations' in channel_data:
            nations_data = channel_data['nations']
            if len(nations_data) > 0:
                rows = []
                table_start = EMOJISPACER1 if channel_data['options']['emoji_mode'] else SPACER1
                table_end = EMOJISPACER2 if channel_data['options']['emoji_mode'] else SPACER2
                for nation_id, nation_info in nations_data.items():
                    status = nation_info['status']
                    user_id = nation_info['user']
                    user = bot.get_user(user_id)
                    if user_id in usernames:
                        username = usernames[user_id]
                    else:
                        if user:
                            username = user.name
                            usernames[user_id] = username
                        else:
                            try:
                                user = await bot.fetch_user(user_id)
                                username = user.name
                                usernames[user_id] = username
                            except discord.HTTPException:
                                username = "Unknown User"
                                usernames[user_id] = username
                    if channels[channel_id]['options']['emoji_mode']:
                        status_emoji = EMOJIS.get(status, '')
                        if status in ['unsubmitted', 'submitted', 'unfinished', 'dead', 'computer', '-', 'Turn played', 'Turn unfinished', 'Eliminated']:
                            status_text = status
                        else:
                            status_text = 'Unknown'
                        status = f"{status_emoji} {status_text}"
                    else:
                        if status in ['unsubmitted', 'submitted', 'unfinished', 'dead', 'computer', '-', 'Turn played', 'Turn unfinished', 'Eliminated']:
                            status_text = status
                        else:
                            status_text = 'Unknown'
                    row = f"| {nation_id:<4} | {nation_info['name']:<14} | {
                        username:<20} | {status:<14} |\n"
                    rows.append(row)
                max_message_length = 2000
                next_turn_info = f"\nCurrent turn: {channel_data['turn']}, Next turn in: {
                    channel_data['next_turn']}\n```"
                test_message = f"```\n{table_start}"
                max_rows = 0
                while True:
                    if max_rows < len(rows):
                        test_message += rows[max_rows]
                    else:
                        break
                    if len(test_message) + len(table_end) + len(next_turn_info) > max_message_length:
                        break
                    max_rows += 1
                chunk_size = max_rows
                messages = []
                for i in range(0, len(rows), chunk_size):
                    chunk = rows[i:i + chunk_size]
                    message = f"```\n{table_start}"
                    message += "".join(chunk)
                    message += table_end + next_turn_info
                    messages.append(message)
                for message in messages:
                    await ctx.send(message)
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
        existing_nations_data = channels[channel_id].get('nations', {})
        scraped_data, status, address, next_turn, game_name, nations_data, minutes_left, turn = scrape_website(
            url, existing_nations_data)
        if scraped_data is not None and status is not None and address is not None and next_turn is not None and game_name is not None and nations_data is not None and minutes_left is not None and turn is not None:
            channels[channel_id]['nations'] = nations_data
            channels[channel_id]['status'] = status
            channels[channel_id]['address'] = address
            channels[channel_id]['next_turn'] = next_turn
            channels[channel_id]['game_name'] = game_name
            channels[channel_id]['minutes_left'] = minutes_left
            channels[channel_id]['turn'] = turn
            save_channels(channels)
            await ctx.send(f"Scraped website and updated nation data for channel {ctx.channel.mention}")
        else:
            await ctx.send('Failed to scrape website')
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def adduser(ctx, nation_id: int, user: discord.Member):
    channel_id = ctx.channel.id
    if channel_id in channels:
        if str(nation_id) in channels[channel_id]['nations']:
            channels[channel_id]['nations'][str(
                nation_id)]['user'] = str(user.id)
            save_channels(channels)
            nation_name = channels[channel_id]['nations'][str(
                nation_id)]['name']
            await ctx.send(f"Added nation {nation_name} to user {user.mention}")
        else:
            await ctx.send(f"Nation {nation_id} not found in channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_owner)
async def deluser(ctx, nation_id: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        if str(nation_id) in channels[channel_id]['nations']:
            channels[channel_id]['nations'][str(nation_id)]['user'] = ''
            save_channels(channels)
            nation_name = channels[channel_id]['nations'][str(
                nation_id)]['name']
            await ctx.send(f"Removed user from nation {nation_name}")
        else:
            await ctx.send(f"Nation {nation_id} not found in channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
@commands.check(is_not_banned)
async def claim(ctx, nation_id: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        if str(nation_id) in channels[channel_id]['nations']:
            channels[channel_id]['nations'][str(
                nation_id)]['user'] = str(ctx.author.id)
            role_id = channels[channel_id].get('role')
            if role_id:
                role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                if role:
                    await ctx.author.add_roles(role)
            save_channels(channels)
            nation_name = channels[channel_id]['nations'][str(
                nation_id)]['name']
            await ctx.send(f"Claimed nation {nation_name} as {ctx.author.mention}")
        else:
            await ctx.send(f"Nation {nation_id} not found in channel {ctx.channel.mention}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command()
async def unclaim(ctx, nation_id: int):
    channel_id = ctx.channel.id
    if channel_id in channels:
        if str(nation_id) in channels[channel_id]['nations']:
            claimed_by = channels[channel_id]['nations'][str(
                nation_id)].get('user')
            if claimed_by and claimed_by == str(ctx.author.id):
                channels[channel_id]['nations'][str(nation_id)]['user'] = ''
                role_id = channels[channel_id].get('role')
                if role_id:
                    role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                    if role:
                        await ctx.author.remove_roles(role)
                save_channels(channels)
                nation_name = channels[channel_id]['nations'][str(
                    nation_id)]['name']
                await ctx.send(f"Unclaimed nation {nation_name} as {ctx.author.mention}")
            elif claimed_by:
                await ctx.send(f"Nation {nation_id} is claimed by <@{claimed_by}>.")
            else:
                await ctx.send(f"Nation {nation_id} is not claimed.")
        else:
            await ctx.send(f"Nation {nation_id} not found in channel {ctx.channel.mention}")
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
async def toggle_autocheck(ctx):
    channel_id = ctx.channel.id
    await toggle_channel_autocheck(channel_id)
    await ctx.send(f"Autocheck is now {'on' if channels[channel_id]['options']['autocheck'] else 'off'} for channel {ctx.channel.mention}")


@bot.command()
@commands.check(is_owner)
async def view_options(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        options = channels[channel_id]['options']
        output = f"Minutes per check: {options['minutes_per_check']}\n"
        output += f"Minimum unready before warn: {
            options['min_unready_before_warn']}\n"
        output += f"Minimum time before warn: {
            options['min_time_before_warn']}\n"
        output += f"Emoji mode: {'on' if options['emoji_mode'] else 'off'}\n"
        output += f"Autocheck: {'on' if options['autocheck'] else 'off'}"
        await ctx.author.send(f"Options for channel {ctx.channel.mention}:\n{output}")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")


@bot.command(name='turns')
async def turns(ctx, user: discord.Member = None):
    if user is None:
        user_id = ctx.author.id
    else:
        user_id = user.id

    output = ""
    for channel_id, channel_data in channels.items():
        unsubmitted_count = 0
        matching_nation = False
        for nation_id, nation_info in channel_data['nations'].items():
            if nation_info.get('status') in ['unsubmitted', 'unfinished', '-', 'Turn unfinished']:
                unsubmitted_count += 1
            if nation_info.get('user') == str(user_id):
                matching_nation = True
                if channel_data['options']['emoji_mode']:
                    status = f"{EMOJIS.get(nation_info['status'], '')} {
                        nation_info['status']}"
                else:
                    status = nation_info['status']
                output += f"{channel_data['game_name']} - Nation {
                    nation_id} ({nation_info['name']}): {status}\n"
                output += f"Turn: {channel_data.get('turn', 'N/A')}, Next Turn: {
                    channel_data.get('next_turn', 'N/A')}, <t:{int(time.time()) + (60 * text_to_minutes(channel_data.get('next_turn')))}:f>\n"
        if matching_nation:
            output += f"Unready nations in this game: {
                unsubmitted_count}\n\n"

    if output:
        await ctx.send(output)
    else:
        await ctx.send(f"No nations found for user {user.mention if user else ctx.author.mention}")


@bot.command()
@commands.check(is_owner)
async def channel_info(ctx):
    channel_id = ctx.channel.id
    if channel_id in channels:
        channel_data = channels[channel_id]
        await ctx.author.send(f"Info for channel {ctx.channel.mention}:\n```json\n{channel_data}\n```")
    else:
        await ctx.send(f"Channel {ctx.channel.mention} is not bound to a URL")
