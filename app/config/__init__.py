import os
from dotenv import load_dotenv

# Carga el archivo .env desde la raíz del proyecto
load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL") 
PRIVATE_SECRET = os.getenv("PRIVATE_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
FERNET_KEY = os.getenv("FERNET_KEY")
AZURE_URL = os.getenv("AZURE_URL")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
APP_ENV = os.getenv("APP_ENV")
ID = os.getenv("ID")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY")
AWS_S3_BUCKET = os.getenv("AWS_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_BUCKET_REGION")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
SPELLCAST_VOICES_CACHE_TTL_SECONDS = os.getenv("SPELLCAST_VOICES_CACHE_TTL_SECONDS")