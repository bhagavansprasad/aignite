import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db")
ALLOWED_HOSTS = ["*"]
