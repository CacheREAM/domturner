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
                channel_data['options'] = channel_data.get('options', {})
                nations = {}
                for nation_id, nation_data in channel_data.get('nations', {}).items():
                    nation_data['user'] = nation_data.get('user', None)
                    nations[int(nation_id)] = nation_data
                channels[int(channel_id)] = {
                    'url': channel_data['url'],
                    'role': channel_data.get('role', None),
                    'nations': nations,
                    'options': channel_data.get('options', {}),
                    'status': channel_data.get('status', None),
                    'address': channel_data.get('address', None),
                    'next_turn': channel_data.get('next_turn', None),
                    'game_name': channel_data.get('game_name', None),
                    'minutes_left': channel_data.get('minutes_left', None),
                    'turn': channel_data.get('turn', None),
                    'previous_turn': channel_data.get('previous_turn', None),
                    'warned_timeleft': channel_data.get('warned_timeleft', False),
                    'warned_unready': channel_data.get('warned_unready', False)
                }
            return channels
    except json.JSONDecodeError as e:
        logger.error(f"Error loading channels: {e}")
        return {}


def save_channels(channels_param):
    channels_to_write = {}
    for channel_id, channel_data in channels_param.items():
        nations_to_write = {}
        for nation_id, nation_data in channel_data['nations'].items():
            nations_to_write[nation_id] = {
                'name': nation_data['name'],
                'status': nation_data['status'],
                'user': nation_data.get('user', None)
            }
        channel_data_to_write = {
            'url': channel_data['url'],
            'role': channel_data.get('role', None),
            'nations': nations_to_write,
            'options': channel_data.get('options', {}),
            'status': channel_data.get('status', None),
            'address': channel_data.get('address', None),
            'next_turn': channel_data.get('next_turn', None),
            'game_name': channel_data.get('game_name', None),
            'minutes_left': channel_data.get('minutes_left', None),
            'turn': channel_data.get('turn', None),
            'previous_turn': channel_data.get('previous_turn', None),
            'warned_timeleft': channel_data.get('warned_timeleft', False),
            'warned_unready': channel_data.get('warned_unready', False)
        }
        channels_to_write[channel_id] = channel_data_to_write
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels_to_write, f)
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
