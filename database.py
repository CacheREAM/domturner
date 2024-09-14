import json
from logger import get_logger
import os

logger = get_logger()

# Channels file name
CHANNELS_FILE = 'channels.json'

# Load channels from file
if os.path.exists(CHANNELS_FILE):
    channels = load_channels()
else:
    channels = {}


def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            channels_json = json.load(f)
            channels = {}
            for channel_id, channel_data in channels_json.items():
                # Validate channel data
                if 'url' not in channel_data or 'nations' not in channel_data:
                    logger.warning(f"Invalid channel data for channel {
                        channel_id}: {channel_data}")
                    continue
                channel_data['nations'] = {nation_name: nation_data for nation_name,
                                           nation_data in channel_data['nations'].items() if nation_name is not None}
                if 'options' not in channel_data:
                    channel_data['options'] = {
                        'minutes_per_check': 15,  # Default value
                        'current_turn': 0,  # Default value
                        'min_unready_before_warn': 1,  # Default value
                        'warned_unready': False,  # Default value
                        'warned_timeleft': False,  # Default value
                        'min_time_before_warn': 60  # Default value
                    }
                channels[int(channel_id)] = channel_data
            return channels
    except json.JSONDecodeError as e:
        logger.error(f"Error loading channels: {e}")
        return {}


# Function to save channels to file


def save_channels(channels_param):
    try:
        channels_param_to_write = {}
        for channel_id, channel_data in channels_param.items():
            # Validate channel data before saving
            if 'url' not in channel_data or 'nations' not in channel_data:
                logger.warning(f"Invalid channel data for channel {
                               channel_id}: {channel_data}")
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
                    'min_unready_before_warn': channel_data['options']['min_unready_before_warn'],
                    'warned_unready': channel_data['options']['warned_unready'],
                    'warned_timeleft': channel_data['options']['warned_timeleft'],
                    'min_time_before_warn': channel_data['options']['min_time_before_warn']
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
