from config.py import OWNER_IDS
from bs4 import BeautifulSoup
from logger import get_logger
import requests


logger = get_logger()


# Check if user is owner
def is_owner(ctx):
    return ctx.author.id in OWNER_IDS


# Function to scrape website
def scrape_website(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # Set encoding to UTF-8
        soup = BeautifulSoup(response.text, 'html.parser')
        nation_name_cells = soup.find_all(
            'td', class_='nation-name wide-column')
        scraped_data = []
        nations_data = {}
        for cell in nation_name_cells:
            nation_name = cell.find(
                'b').text.strip() if cell.find('b') else None
            status_cells = cell.parent.find_all('td', class_=lambda x: x in [
                                                'submitted', 'unsubmitted', 'unfinished', 'computer', 'dead'])
            status = [cell.text.strip() for cell in status_cells]
            scraped_data.append((nation_name, status))
            nations_data[nation_name] = {'status': status, 'user': None}
        # Get the text from the striped-table inside the pane status div
        striped_table = soup.find('div', class_='pane status').find(
            'table', class_='striped-table')
        table_text = ''
        for row in striped_table.find_all('tr'):
            cells = row.find_all('td')
            for cell in cells:
                table_text += cell.text.strip() + '\n'
        # Get the game name
        game_name = soup.find('h1').text.strip()
        return scraped_data, table_text, game_name, nations_data
    except Exception as e:
        logger.error(f'Error: {e}')
        return None, None, None, None
