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
                if 'url' not in channel_data or 'nations' not in channel_data:
                    logger.warning(f"Invalid channel data for channel {
                                   channel_id}: {channel_data}")
                    continue
                channels[int(channel_id)] = channel_data
            return channels
    except json.JSONDecodeError as e:
        logger.error(f"Error loading channels: {e}")
        return {}


def save_channels(channels_param):
    channels_to_write = {}
    for channel_id, channel_data in channels_param.items():
        if 'url' not in channel_data or 'nations' not in channel_data:
            logger.warning(f"Invalid channel data for channel {
                           channel_id}: {channel_data}")
            continue
        channel_data_to_write = {
            'url': channel_data['url'],
            'role': channel_data.get('role', None),
            'nations': channel_data['nations'],
            'options': {
                'minutes_per_check': channel_data.get('minutes_per_check', 15),
                'current_turn': channel_data.get('current_turn', 0),
                'min_unready_before_warn': channel_data.get('min_unready_before_warn', 1),
                'warned_unready': channel_data.get('warned_unready', False),
                'warned_timeleft': channel_data.get('warned_timeleft', False),
                'min_time_before_warn': channel_data.get('min_time_before_warn', 60),
                'emoji_mode': channel_data.get('options', {}).get('emoji_mode', True)
            }
        }
        channels_to_write[channel_id] = channel_data_to_write
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels_to_write, f)
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
