from keys import OWNER_IDS, BANNED_IDS
from bs4 import BeautifulSoup
from logger import get_logger
import requests
import re

logger = get_logger()


# Check if user is owner
def is_owner(ctx):
    return ctx.author.id in OWNER_IDS


def is_not_banned(ctx):
    return ctx.author.id not in BANNED_IDS


def text_to_minutes(text):
    if text == "On submission":
        return 999999999  # Return a high number if text is "On submission"

    days_match = re.search(r"(\d+) days?", text)
    hours_match = re.search(r"(\d+) hours?", text)
    minutes_match = re.search(r"(\d+) minutes?", text)

    days = int(days_match.group(1)) if days_match else 0
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0

    total_minutes = (days * 24 * 60) + (hours * 60) + minutes

    return total_minutes


def text_to_turn(text):
    turn_match = re.search(r"(\d+)", text)

    turn = int(turn_match.group(1)) if turn_match else 0

    return turn


def scrape_website(url, existing_nations_data=None):
    try:
        if "illwinter.com" in url:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f'Failed to retrieve {url}. Status code: {
                               response.status_code}')
                return None, None, None, None, None, None, None, None
            response.encoding = 'utf-8'  # Set encoding to UTF-8
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                logger.warning(f'No table found at {url}')
                return None, None, None, None, None, None, None, None
            game_info = table.find('tr').find('td').text.strip()
            game_name, info = game_info.split(',', 1)
            game_name = game_name.strip()
            turn_info, time_info = info.split('(', 1)
            turn_info = turn_info.strip()
            time_info = time_info.strip(')')
            turn = text_to_turn(turn_info)
            next_turn = time_info.replace('time left: ', '')
            minutes_left = text_to_minutes(next_turn)
            scraped_data = []
            nations_data = {}
            nation_id = 1
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                nation_name = cells[0].text.strip().split(',')[0]
                status = cells[1].text.strip()
                scraped_data.append((nation_name, status))
                existing_nation_data = existing_nations_data.get(
                    str(nation_id), {}) if existing_nations_data else {}
                new_nation_data = {
                    'name': nation_name,
                    'status': status,
                    'user': existing_nation_data.get('user'),
                }
                existing_nation_data.update(new_nation_data)
                nations_data[str(nation_id)] = existing_nation_data
                nation_id += 1
            status = "UNKNOWN"
            address = url
            # Print status, address, and next_turn variables
            print(f"Status: {status}, Address: {address}, Next Turn: {
                  next_turn}, Minutes Left: {minutes_left}, Turn: {turn}")
            return scraped_data, status, address, next_turn, game_name, nations_data, minutes_left, turn

        else:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f'Failed to retrieve {url}. Status code: {
                               response.status_code}')
                return None, None, None, None, None, None, None, None
            response.encoding = 'utf-8'  # Set encoding to UTF-8
            soup = BeautifulSoup(response.text, 'html.parser')
            nation_name_cells = soup.find_all(
                'td', class_='nation-name wide-column')
            if not nation_name_cells:
                logger.warning(f'No nation name cells found at {url}')
                return None, None, None, None, None, None, None, None
            scraped_data = []
            nations_data = {}
            nation_id = 1
            for cell in nation_name_cells:
                nation_name = cell.find(
                    'b').text.strip() if cell.find('b') else None
                status_cells = cell.parent.find_all('td', class_=lambda x: x in [
                                                    'submitted', 'unsubmitted', 'unfinished', 'computer', 'dead'])
                status = [cell.text.strip() for cell in status_cells]
                scraped_data.append((nation_name, status))
                existing_nation_data = existing_nations_data.get(
                    str(nation_id), {}) if existing_nations_data else {}
                new_nation_data = {
                    'name': nation_name,
                    'status': status[0] if status else None,
                    'user': existing_nation_data.get('user'),
                }
                existing_nation_data.update(new_nation_data)
                nations_data[str(nation_id)] = existing_nation_data
                nation_id += 1
            # Get the text from the striped-table inside the pane status div
            striped_table = soup.find('div', class_='pane status').find(
                'table', class_='striped-table')
            if not striped_table:
                logger.warning(f'No striped table found at {url}')
                return None, None, None, None, None, None, None, None
            status = striped_table.find_all('tr')[0].find_all('td')[
                1].text.strip()
            address = striped_table.find_all('tr')[1].find_all('td')[
                1].text.strip()
            next_turn = striped_table.find_all(
                'tr')[2].find_all('td')[1].text.strip()
            minutes_left = text_to_minutes(next_turn)
            turn = text_to_turn(status)
            # Check if the data is empty
            if not scraped_data or not status or not address or not next_turn or not minutes_left or not turn:
                logger.warning('No data found, skipping this scrape')
                return None, None, None, None, None, None, None, None
            # Print status, address, and next_turn variables
            print(f"Status: {status}, Address: {address}, Next Turn: {
                  next_turn}, Minutes Left: {minutes_left}, Turn: {turn}")
            # Get the game name
            game_name = soup.find('h1').text.strip()
            return scraped_data, status, address, next_turn, game_name, nations_data, minutes_left, turn
    except requests.exceptions.RequestException as e:
        logger.error(f'Error: {e}')
        return None, None, None, None, None, None, None, None
    except Exception as e:
        logger.error(f'Error: {e}')
        return None, None, None, None, None, None, None, None
