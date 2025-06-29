from pydantic_settings import BaseSettings, SettingsConfigDict  # Import for configuration management with Pydantic
from typing import Annotated, Literal, Any  # Various typing utilities for annotations
from pydantic import (
    AnyUrl,  # Import for handling URLs in validation
    BeforeValidator,  # Import for custom validators before setting the value
    computed_field,  # Import for computed fields (i.e., derived values)
    PostgresDsn,  # Import for Postgres DSN type
    Field  # Field validation tool in Pydantic
)
from pydantic_core import MultiHostUrl  # Import for handling multi-host URLs (not used in this example)
import os
from dotenv import load_dotenv

# Function to parse CORS origins, handling both string and list types
def parse_cors(v: Any) -> list[list[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]  # Split string into a list of URLs
    elif isinstance(v, (list, str)):  # If input is already a list or string
        return v  # Return as is
    raise ValueError(v)  # If the input is neither, raise a ValueError

# Load the .env file from the parent directory
parent_dir = os.path.dirname(os.path.dirname(__file__))
env_file = os.path.join(parent_dir, '.env')
print(f"Trying to load .env from: {env_file}")

# Load the .env file
result = load_dotenv(env_file, verbose=True)
if not result:
    print("Failed to load .env file.")
else:
    print("Successfully loaded .env file.")

class Settings:
    """
    This class defines all the settings that are required for your application.
    It uses environment variables loaded by `dotenv` from a .env file.
    """
    
    # Basic settings like domain and environment.
    DOMAIN: str = os.getenv('DOMAIN', 'localhost')  # Default to 'localhost' if not defined in .env
    ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv('ENVIRONMENT', 'local')  # Default to 'local' if not defined in .env

    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: str = os.getenv('REDIS_PORT', '6379')
    
    # PostgreSQL settings
    POSTGRES_USER: str = os.getenv('POSTGRES_USER')  # The username for PostgreSQL
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')  # The password for PostgreSQL
    POSTGRES_SERVER: str = os.getenv('POSTGRES_SERVER','users-db')  # The server where PostgreSQL is hosted
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))  # Default to 5432 if not defined
    POSTGRES_DB: str = os.getenv('POSTGRES_DB','users_db')  # The name of the PostgreSQL database

    # SQLite settings (fallback to SQLite for local development)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')  # Default path for the SQLite database

    # CORS settings (for allowing specific origins to access the API)
    BACKEND_CORS_ORIGINS: list[AnyUrl] = os.getenv('BACKEND_CORS_ORIGINS', '').split(',')  # Parsing CORS origins (comma-separated)

    # Secret key for cryptography or JWT encoding/decoding
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'django-insecure-i-i^&f9-=cdt+k478)**l!uy2olm)&24&_(-bqo&1+=oh5^5pu')

    @computed_field
    @property
    def server_host(self) -> str:
        """
        Dynamically computes the server host URL depending on the environment.
        - In 'local' environment, it returns a 'http://' URL.
        - In 'staging' or 'production', it returns a 'https://' URL.
        """
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"  # Local environment uses HTTP
        return f"https://{self.DOMAIN}"  # Production/staging environments use HTTPS

    @computed_field  # Type: ignore[misc]  # Ignore type checking for this field (Pydantic allows this)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Based on the environment, return the appropriate database URI.
        Supports both SQLite for local development and PostgreSQL for production or staging.
        """
        if self.ENVIRONMENT == "local":
            # Use SQLite when in local environment
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
            
            # return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}" \
            #        f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"  # PostgreSQL URI
        elif self.ENVIRONMENT in ["staging", "production"]:
            # Use PostgreSQL in production or staging environments
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}" \
                   f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"  # PostgreSQL URI
        else:
            raise ValueError("Unsupported environment for database connection")  # Raise an error for unsupported environments
    

# Initialize settings by reading from environment or .env file
settings = Settings()
