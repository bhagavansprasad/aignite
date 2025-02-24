import os
from typing import Dict

def pytest_configure(config):
    os.environ.setdefault('DATABASE_URL', 'postgresql://bhagavan:jnjnuh@localhost/aignite_db')

