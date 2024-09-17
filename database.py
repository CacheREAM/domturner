import json
from logger import get_logger
import os

logger = get_logger()

# Channels file name
CHANNELS_FILE = 'channels.json'


if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump({}, f)


def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            channels_json = json.load(f)
            channels = {}
            for channel_id, channel_data in channels_json.items():
                if 'url' not in channel_data or 'nations' not in channel_data or 'status' not in channel_data or 'address' not in channel_data or 'next_turn' not in channel_data or 'game_name' not in channel_data or 'minutes_left' not in channel_data:
                    logger.warning(f"Invalid channel data for channel {
                                   channel_id}: {channel_data}")
                    continue
                channel_data['options'] = channel_data.get('options', {})
                nations = {}
                for nation_id, nation_data in channel_data['nations'].items():
                    nations[int(nation_id)] = nation_data
                channels[int(channel_id)] = {
                    'url': channel_data['url'],
                    'role': channel_data.get('role', None),
                    'nations': nations,
                    'options': channel_data.get('options', {}),
                    'status': channel_data['status'],
                    'address': channel_data['address'],
                    'next_turn': channel_data['next_turn'],
                    'game_name': channel_data['game_name'],
                    'minutes_left': channel_data.get('minutes_left', None)
                }
            return channels
    except json.JSONDecodeError as e:
        logger.error(f"Error loading channels: {e}")
        return {}


def save_channels(channels_param):
    channels_to_write = {}
    for channel_id, channel_data in channels_param.items():
        if 'url' not in channel_data or 'nations' not in channel_data or 'status' not in channel_data or 'address' not in channel_data or 'next_turn' not in channel_data or 'game_name' not in channel_data or 'minutes_left' not in channel_data:
            logger.warning(f"Invalid channel data for channel {
                           channel_id}: {channel_data}")
            continue
        channel_data_to_write = {
            'url': channel_data['url'],
            'role': channel_data.get('role', None),
            'nations': {str(nation_id): nation_data for nation_id, nation_data in channel_data['nations'].items()},
            'options': channel_data.get('options', {}),
            'status': channel_data['status'],
            'address': channel_data['address'],
            'next_turn': channel_data['next_turn'],
            'game_name': channel_data['game_name'],
            'minutes_left': channel_data['minutes_left']
        }
        channels_to_write[channel_id] = channel_data_to_write
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels_to_write, f)
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
