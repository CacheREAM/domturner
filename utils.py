from keys import OWNER_IDS
from bs4 import BeautifulSoup
from logger import get_logger
import requests


logger = get_logger()


# Check if user is owner
def is_owner(ctx):
    return ctx.author.id in OWNER_IDS


def scrape_website(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # Set encoding to UTF-8
        soup = BeautifulSoup(response.text, 'html.parser')
        nation_name_cells = soup.find_all(
            'td', class_='nation-name wide-column')
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
            nations_data[str(nation_id)] = {
                'name': nation_name,
                'status': status,
                'user': None
            }
            nation_id += 1
        # Get the text from the striped-table inside the pane status div
        striped_table = soup.find('div', class_='pane status').find(
            'table', class_='striped-table')
        status = striped_table.find_all('tr')[0].find_all('td')[1].text.strip()
        address = striped_table.find_all('tr')[1].find_all('td')[
            1].text.strip()
        next_turn = striped_table.find_all(
            'tr')[2].find_all('td')[1].text.strip()
        # Get the game name
        game_name = soup.find('h1').text.strip()
        return scraped_data, status, address, next_turn, game_name, nations_data
    except Exception as e:
        logger.error(f'Error: {e}')
        return None, None, None, None, None, None
