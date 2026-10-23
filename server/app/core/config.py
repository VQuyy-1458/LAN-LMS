import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / '.env')


@dataclass
class Settings:
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./database/lan_lms.db')
    allowed_origins: tuple[str, ...] = tuple(os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(','))
    secure_cookie: bool = os.getenv('SECURE_COOKIE', 'false').lower() == 'true'
    session_seconds: int = 8 * 60 * 60
    heartbeat_seconds: float = 15
    heartbeat_timeout: float = 10
