from typing import Any
import os

DATABASE_PATH = os.getenv('DATABASE_PATH', 'tickerpulse.db')
API_KEY = os.getenv('API_KEY', 'your_api_key_here')