import asyncio
from database import save_channels
from logger import get_logger
from bot import bot
from utils import scrape_website
from channels import channels

logger = get_logger()
tasks = {}


# Function to handle autocheck for a channel
async def handle_autocheck(channel_id):
    if channel_id in tasks and not tasks[channel_id].done():
        tasks[channel_id].cancel()
    tasks[channel_id] = asyncio.create_task(_handle_autocheck(channel_id))


async def _handle_autocheck(channel_id):
    channel_data = channels[channel_id]
    url = channel_data['url']
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

        # Get the channel object
        channel = bot.get_channel(channel_id)

        # Get the role object
        role_id = channel_data.get('role')
        if role_id:
            role = channel.guild.get_role(int(role_id))

        if 'previous_turn' in channel_data and channel_data['previous_turn'] is not None and channel_data['previous_turn'] < channel_data['turn']:
            if role:
                await channel.send(f"{role.mention} New turn! The turn number is: {channel_data['turn']}")
            channel_data['options']['warned_timeleft'] = False
            channel_data['options']['warned_unready'] = False
        channel_data['previous_turn'] = channel_data['turn']

        # Check if minutes left is lower than the channel's min_time_before_warn
        if not channel_data['options']['warned_timeleft'] and channel_data['minutes_left'] < channel_data['options']['min_time_before_warn']:
            # Ping the role
            if role:
                await channel.send(f"{role.mention} Time is running out!")
            # Ping the users attached to the nations that are currently unsubmitted and unfinished
            for nation_id, nation_data in channel_data['nations'].items():
                if nation_data['status'] in ['unsubmitted', 'unfinished', '-', 'Turn unfinished']:
                    user_id = nation_data.get('user')
                    if user_id:
                        await channel.send(f"<@{user_id}> Time is running out!")
            channel_data['options']['warned_timeleft'] = True

        # Check if the combined amount of unsubmitted and unfinished nations are lower than min_unready_before_warn
        unready_nations = sum(1 for nation_id, nation_data in channel_data['nations'].items(
        ) if nation_data['status'] in ['unsubmitted', 'unfinished', '-', 'Turn unfinished'])
        if not channel_data['options']['warned_unready'] and unready_nations < channel_data['options']['min_unready_before_warn']:
            # Ping the role
            if role:
                await channel.send(f"{role.mention} {unready_nations} players are not ready!")
            # Ping the users attached to the nations that are currently unsubmitted and unfinished
            for nation_id, nation_data in channel_data['nations'].items():
                if nation_data['status'] in ['unsubmitted', 'unfinished', '-', 'Turn unfinished']:
                    user_id = nation_data.get('user')
                    if user_id:
                        await channel.send(f"<@{user_id}> Your nation is not ready!")
            channel_data['options']['warned_unready'] = True

        # Save the updated channel data
        save_channels(channels)

    # Schedule the next autocheck
    minutes_per_check = channel_data['options']['minutes_per_check']
    await asyncio.sleep(5)  # perhaps this will fix it
    await asyncio.sleep(minutes_per_check * 60)
    await handle_autocheck(channel_id)


async def toggle_channel_autocheck(channel_id):
    if channel_id in channels:
        channels[channel_id]['options']['autocheck'] = not channels[channel_id]['options']['autocheck']
        save_channels(channels)
        if channels[channel_id]['options']['autocheck']:
            try:
                await handle_autocheck(channel_id)
            except Exception as e:
                logger.error(f"Failed to start autocheck for channel {
                             channel_id}: {str(e)}")


# Function to start autocheck for all channels
async def start_autocheck():
    for channel_id, channel_data in channels.items():
        if channel_data['options']['autocheck']:
            try:
                await handle_autocheck(channel_id)
            except Exception as e:
                logger.error(f"Failed to start autocheck for channel {
                             channel_id}: {str(e)}")
