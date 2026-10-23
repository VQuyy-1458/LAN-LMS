import time

from sqlalchemy import CheckConstraint, ForeignKey, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('teacher','student')", name='valid_user_role'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True)
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(String(16))
    must_change_password: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)


class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    csrf_hash: Mapped[str | None]
    expires_at: Mapped[float]


class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[float] = mapped_column(default=time.time)


def database(url):
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite:') else {})
    if url.startswith('sqlite:'):
        @event.listens_for(engine, 'connect')
        def configure(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('PRAGMA busy_timeout=5000')
    return engine, sessionmaker(engine, expire_on_commit=False)
