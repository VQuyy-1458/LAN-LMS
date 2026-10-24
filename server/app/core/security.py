import hashlib
import secrets
import time
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request

from .database import AuthSession, User

hasher = PasswordHasher()
COOKIE = 'lan_lms_session'


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def verify(encoded, password):
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def fail(status, code, detail):
    raise HTTPException(status, {'code': code, 'detail': detail})


def check_origin(request):
    if request.headers.get('origin') not in request.app.state.settings.allowed_origins:
        fail(403, 'INVALID_ORIGIN', 'Origin không được phép')


@dataclass
class Principal:
    user_id: int
    username: str
    role: str
    must_change_password: bool
    session_hash: str


def lookup(app, token):
    if not token:
        return None
    with app.state.sessions() as db:
        session = db.get(AuthSession, digest(token))
        if not session or session.expires_at <= time.time():
            return None
        user = db.get(User, session.user_id)
        if not user or not user.active:
            return None
        return Principal(user.id, user.username, user.role, user.must_change_password, session.token_hash)


def current_user(request: Request):
    principal = lookup(request.app, request.cookies.get(COOKIE))
    if not principal:
        fail(401, 'UNAUTHENTICATED', 'Vui lòng đăng nhập')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        check_origin(request)
        with request.app.state.sessions() as db:
            session = db.get(AuthSession, principal.session_hash)
            supplied = request.headers.get('x-csrf-token', '')
            if not session or session.expires_at <= time.time():
                fail(401, "UNAUTHENTICATED", "Vui lòng đăng nhập")
            if not session.csrf_hash or not secrets.compare_digest(session.csrf_hash, digest(supplied)):
                fail(403, 'INVALID_CSRF', 'CSRF token không hợp lệ')
    return principal


def learning_user(user=Depends(current_user)):
    if user.must_change_password:
        fail(403, 'PASSWORD_CHANGE_REQUIRED', 'Cần đổi mật khẩu trước')
    return user


def require_role(role):
    def dependency(user=Depends(learning_user)):
        if user.role != role:
            fail(403, 'FORBIDDEN', 'Không có quyền thực hiện')
        return user
    return dependency


def require_course_access(request: Request, course_id: int, user=Depends(learning_user)):
    # Member 3 registers this authoritative DB policy when the course module is integrated.
    policy = request.app.state.course_access
    if policy is None:
        fail(503, 'MODULE_NOT_READY', 'Module khóa học chưa tích hợp')
    if not policy(user, course_id):
        fail(403, 'FORBIDDEN', 'Không có quyền truy cập khóa học')
    return user
