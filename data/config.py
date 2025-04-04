import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))
DATABASE_URL = Path('data/restaurant.sqlite3')

PROMO_CODES = {
    'PYTHON10': 0.1,  # 10% discount
    'PYTHON20': 0.2,  # 20% discount
}