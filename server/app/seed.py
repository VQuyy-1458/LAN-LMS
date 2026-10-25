"""Interactive local teacher creation; never ship a default password."""
import getpass

from sqlalchemy import select

from .core.database import User
from .core.security import hasher
from .main import app
from .models import Teachers


def main():
    username = input('Teacher username: ').strip()
    password = getpass.getpass('Password (8-128 characters): ')
    confirm = getpass.getpass('Confirm password: ')
    if not username or len(username) > 128 or not 8 <= len(password) <= 128 or password != confirm:
        raise SystemExit('Invalid username/password or confirmation mismatch')
    with app.state.sessions() as db:
        if db.scalar(select(User).where(User.username == username)):
            raise SystemExit('Username already exists; no password changed')
        user=User(username=username, password_hash=hasher.hash(password), role='teacher')
        db.add(user);db.flush()
        db.add(Teachers(user_id=user.id,teacher_code=username,full_name=username))
        db.commit()
    print('Teacher created')


if __name__ == '__main__':
    main()
