"""TV1: validated settings; environment is read per instance, never at import time."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / 'server' / '.env')


def env_bool(name, default=False):
    value = os.getenv(name, str(default)).strip().lower()
    if value not in ('true', 'false'):
        raise ValueError(f'{name} must be true or false')
    return value == 'true'


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv(
        'DATABASE_URL', f'sqlite:///{PROJECT_ROOT / "database" / "lan_lms.db"}'))
    allowed_origins: tuple[str, ...] = field(default_factory=lambda: tuple(
        part.strip() for part in os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',') if part.strip()))
    secure_cookie: bool = field(default_factory=lambda: env_bool('SECURE_COOKIE'))
    public_origin: str | None = field(default_factory=lambda: os.getenv('PUBLIC_ORIGIN') or None)
    https_origin: str | None = field(default_factory=lambda: os.getenv('HTTPS_ORIGIN') or None)
    lan_ca_certificate: str | None = field(default_factory=lambda: os.getenv('LAN_CA_CERTIFICATE') or None)
    session_seconds: int = 8 * 60 * 60
    heartbeat_seconds: float = 15
    heartbeat_timeout: float = 10

    def __post_init__(self):
        if not self.allowed_origins:
            raise ValueError('ALLOWED_ORIGINS must contain at least one exact web origin')
        for origin in (*self.allowed_origins, *((self.public_origin,) if self.public_origin else ()), *((self.https_origin,) if self.https_origin else ())):
            parsed = urlsplit(origin)
            try:
                parsed.port
            except ValueError:
                raise ValueError('ALLOWED_ORIGINS contains an invalid port') from None
            if (parsed.scheme not in ('http', 'https') or not parsed.hostname or '*' in origin
                    or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
                raise ValueError('ALLOWED_ORIGINS requires exact http(s) origins without paths or wildcards')
        if self.session_seconds <= 0 or self.heartbeat_seconds <= 0 or self.heartbeat_timeout <= 0:
            raise ValueError('Session and heartbeat durations must be positive')
        try:
            url = make_url(self.database_url)
        except Exception:
            raise ValueError('DATABASE_URL is invalid; check the server environment file') from None
        if url.drivername.startswith('sqlite') and url.database not in (None, '', ':memory:'):
            path = Path(url.database)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            if not path.parent.is_dir():
                raise ValueError('DATABASE_URL parent directory does not exist; create it before starting')
            self.database_url = url.set(database=str(path.resolve())).render_as_string(hide_password=False)
