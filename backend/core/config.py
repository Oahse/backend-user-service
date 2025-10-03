import os
from typing import List, Literal
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file located in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env.production')
load_dotenv(ENV_PATH)

def parse_cors(value: str) -> List[str]:
    """
    Parses CORS origins. Accepts comma-separated string or list-like string.
    Example: "http://localhost,http://127.0.0.1" → ["http://localhost", "http://127.0.0.1"]
    """
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            return [i.strip().strip("'\"") for i in value[1:-1].split(",")]
        return [i.strip() for i in value.split(",")]
    raise ValueError("Invalid CORS format")

class Settings:
    # Environment
    DOMAIN: str = os.getenv('DOMAIN', 'localhost')
    ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv('ENVIRONMENT', 'local')

    KAFKA_BOOTSTRAP_SERVERS : List[str] = parse_cors(os.getenv('KAFKA_BOOTSTRAP_SERVERS', "[kafka:9092]"))
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'products_topic')
    KAFKA_GROUP: str = os.getenv('KAFKA_GROUP', 'product_group')
    KAFKA_HOST: str = os.getenv('KAFKA_HOST', 'kafka')
    KAFKA_PORT: str = os.getenv('KAFKA_PORT', '9092')
    
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_CACHE_TTL: int = int(os.getenv('REDIS_CACHE_TTL', '3600'))  # default 3600 seconds (1 hour)

    # SMS
    # SMS_API_KEY: Optional[str] = os.getenv('SMS_API_KEY')
    # SMS_API_URL: Optional[str] = os.getenv('SMS_API_URL')

    # Push Notifications
    # FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv('FIREBASE_CREDENTIALS_JSON','')

    # Celery
    CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # PostgreSQL
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', '0ZTftS7B0Bsf3tlzddQs')
    POSTGRES_SERVER: str = os.getenv('POSTGRES_SERVER', 'banwee-db.c2po20oyum9p.us-east-1.rds.amazonaws.com')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'banwee_db')
    POSTGRES_DB_URL: str = os.getenv('POSTGRES_DB_URL', "postgresql+asyncpg://postgres:0ZTftS7B0Bsf3tlzddQs@banwee-db.c2po20oyum9p.us-east-1.rds.amazonaws.com:5432/banwee_db")
    
    # SQLite (fallback if needed)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')

    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'changeme-super-secret-key')
    ALGORITHM: str = os.getenv('ALGORITHM', "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 7))
    RESEND_API_KEY: str = os.getenv('RESEND_API_KEY', "re_J9sfHbqG_Go1YUSTfYS14y6Te1L2jNEUj") 

    # CORS
    RAW_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    BACKEND_CORS_ORIGINS: List[str] = parse_cors(RAW_CORS_ORIGINS)

    SMTP_HOSTNAME: str = os.getenv('SMTP_HOSTNAME', '')
    SMTP_USER: str = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')

    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    WHATSAPP_ACCESS_TOKEN: str = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    PHONE_NUMBER_ID: str = os.getenv('PHONE_NUMBER_ID', '')

    # GOOGLE_SERVICE_ACCOUNT_TYPE: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_TYPE', '')
    # GOOGLE_SERVICE_ACCOUNT_PROJECT: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_PROJECT', '')
    # GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID', '')
    # GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY', '')
    # GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL', '')
    # GOOGLE_SERVICE_ACCOUNT_CLIENT_ID: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_CLIENT_ID', '')

    # @property
    # def google_service_account_info(self) -> dict:
    #     """
    #     Returns the parsed JSON content of the Google service account key,
    #     or raises an error if it's missing or invalid.
    #     """

    #     GOOGLE_SERVICE_ACCOUNT_JSON={
    #         "type": "service_account",
    #         "project_id": self.GOOGLE_SERVICE_ACCOUNT_PROJECT,
    #         "private_key_id": self.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID,
    #         "private_key": self.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY,
    #         "client_email": self.GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL,
    #         "client_id": self.GOOGLE_SERVICE_ACCOUNT_CLIENT_ID,
    #     }

    #     return GOOGLE_SERVICE_ACCOUNT_JSON
    
    # @property
    # def firebase_service_account_info(self) -> dict:
    #     """
    #     Returns the parsed JSON content of the Google service account key,
    #     or raises an error if it's missing or invalid.
    #     """
    #     if not self.FIREBASE_CREDENTIALS_JSON:
    #         raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable is not set")
    #     try:
    #         return json.loads(self.FIREBASE_CREDENTIALS_JSON)
    #     except json.JSONDecodeError as e:
    #         raise ValueError(f"Invalid JSON in FIREBASE_CREDENTIALS_JSON: {e}")
    @property
    def server_host(self) -> str:
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.ENVIRONMENT in ["local"]:
            # return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
            # if self.POSTGRES_DB_URL:
            #     return self.POSTGRES_DB_URL
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.ENVIRONMENT in ["staging", "production"]:
            # for docker
            # return 'postgresql+asyncpg://postgres:postgres@users-db:5432/users_db'

            # if self.POSTGRES_DB_URL:
            #     return self.POSTGRES_DB_URL
            # for supabase
            return 'postgresql+asyncpg://postgres:fAdvot-vyggeg-1rysku@db.htvauholjqlrfihihszd.supabase.co:5432/postgres'

            # return (
            #     f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            #     f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            # )
        else:
            raise ValueError("Invalid ENVIRONMENT for database connection")

# Instantiate the settings object
settings = Settings()


