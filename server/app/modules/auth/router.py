import secrets
import time

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from ...core.database import AuthSession, LoginAttempt, User
from ...core.security import COOKIE, check_origin, current_user, digest, fail, hasher, verify

router = APIRouter(prefix='/api/auth', tags=['auth'])
# A valid hash prevents skipping the expensive password check for unknown usernames.
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


def user_data(user):
    return dict(user_id=user.user_id, username=user.username, role=user.role,
                must_change_password=user.must_change_password)


@router.post('/login')
def login(body: Login, request: Request, response: Response):
    check_origin(request)
    now = time.time()
    ip = request.client.host if request.client else 'unknown'
    with request.app.state.sessions() as db:
        # Reserve an attempt inside a SQLite write transaction; concurrent requests cannot bypass the cap.
        if db.bind.dialect.name == 'sqlite':
            from sqlalchemy import text
            db.execute(text('BEGIN IMMEDIATE'))
        db.execute(delete(LoginAttempt).where(LoginAttempt.created_at < now - 60))
        count = db.scalar(select(func.count()).select_from(LoginAttempt).where(LoginAttempt.ip == ip))
        if count >= 10:
            db.commit()
            fail(429, 'LOGIN_RATE_LIMIT', 'Thử lại sau một phút')
        attempt = LoginAttempt(ip=ip, created_at=now)
        db.add(attempt)
        db.commit()
        user = db.scalar(select(User).where(User.username == body.username))
        valid = verify(user.password_hash if user else DUMMY_HASH, body.password)
        if not valid or not user or not user.active:
            fail(401, 'INVALID_CREDENTIALS', 'Thông tin đăng nhập không hợp lệ')
        if hasher.check_needs_rehash(user.password_hash):
            user.password_hash = hasher.hash(body.password)
        db.delete(attempt)
        db.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
        token = secrets.token_urlsafe(32)
        db.add(AuthSession(token_hash=digest(token), user_id=user.id, expires_at=now + request.app.state.settings.session_seconds))
        db.commit()
        response.set_cookie(COOKIE, token, max_age=request.app.state.settings.session_seconds,
                            httponly=True, secure=request.app.state.settings.secure_cookie, samesite='lax', path='/')
        return {'user': dict(user_id=user.id, username=user.username, role=user.role, must_change_password=user.must_change_password)}


@router.get('/me')
def me(user=Depends(current_user)):
    return user_data(user)


@router.get('/csrf')
def csrf(request: Request, user=Depends(current_user)):
    token = secrets.token_urlsafe(32)
    with request.app.state.sessions() as db:
        session = db.get(AuthSession, user.session_hash)
        session.csrf_hash = digest(token)
        db.commit()
    return {'csrf_token': token}


@router.post('/logout', status_code=204)
def logout(request: Request, user=Depends(current_user)):
    with request.app.state.sessions() as db:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == user.session_hash))
        db.commit()
    response = Response(status_code=204)
    response.delete_cookie(COOKIE, path='/')
    return response


@router.post('/change-password', status_code=204)
def change_password(body: ChangePassword, request: Request, user=Depends(current_user)):
    with request.app.state.sessions() as db:
        record = db.get(User, user.user_id)
        if not verify(record.password_hash, body.current_password):
            fail(400, 'INVALID_PASSWORD', 'Mật khẩu hiện tại không đúng')
        if body.current_password == body.new_password:
            fail(400, 'PASSWORD_UNCHANGED', 'Mật khẩu mới phải khác mật khẩu cũ')
        record.password_hash = hasher.hash(body.new_password)
        record.must_change_password = False
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.user_id))
        db.commit()
    response = Response(status_code=204)
    response.delete_cookie(COOKIE, path='/')
    return response
