import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db")
ALLOWED_HOSTS = ["*"]

SECRET_KEY = "aignite-secret-key"
ALGORITHM = "HS256"

TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://bhagavan:jnjnuh@localhost/aignite_db_test")