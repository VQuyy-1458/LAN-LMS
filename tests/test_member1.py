import asyncio
import time

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.websockets import WebSocketDisconnect

from server.app.core.config import Settings
from server.app.core.database import AuthSession, Base, User
from server.app.core.security import hasher, require_course_access, require_role
from server.app.main import create_app

ORIGIN = {'origin': 'http://localhost:3000'}


@pytest.fixture
def app(tmp_path):
    app = create_app(Settings(database_url=f'sqlite:///{tmp_path / "test.db"}', heartbeat_seconds=0.05, heartbeat_timeout=0.1))
    Base.metadata.create_all(app.state.engine)
    with app.state.sessions() as db:
        for username, role, change in [('teacher', 'teacher', False), ('student', 'student', True)]:
            db.add(User(username=username, password_hash=hasher.hash('old-password'), role=role, must_change_password=change))
        db.commit()

    @app.get('/teacher-only')
    def teacher(user=Depends(require_role('teacher'))):
        return {'id': user.user_id}

    @app.get('/course/{course_id}')
    def course(user=Depends(require_course_access)):
        return {'id': user.user_id}
    yield app
    app.state.engine.dispose()


def login(client, username='teacher'):
    return client.post('/api/auth/login', json={'username': username, 'password': 'old-password'}, headers=ORIGIN)


def csrf(client):
    return {**ORIGIN, 'x-csrf-token': client.get('/api/auth/csrf').json()['csrf_token']}


def test_login_logout_and_cookie(app):
    with TestClient(app) as c:
        assert c.get('/api/auth/me').status_code == 401
        response = login(c)
        assert response.status_code == 200
        assert 'HttpOnly' in response.headers['set-cookie']
        assert 'password_hash' not in response.json()['user']
        assert 'old-password' not in response.text
        assert c.get('/api/auth/me').json()['role'] == 'teacher'
        assert c.post('/api/auth/logout', headers=ORIGIN).status_code == 403
        assert c.post('/api/auth/logout', headers=csrf(c)).status_code == 204
        assert c.get('/api/auth/me').status_code == 401


def test_change_password_revokes_all_sessions(app):
    with TestClient(app) as c, TestClient(app) as other:
        login(c, 'student'); login(other, 'student')
        assert c.get('/teacher-only').json()['code'] == 'PASSWORD_CHANGE_REQUIRED'
        assert c.post('/api/auth/change-password', headers=csrf(c), json={'current_password': 'wrong', 'new_password': 'new-password'}).status_code == 400
        assert c.post('/api/auth/change-password', headers=csrf(c), json={'current_password': 'old-password', 'new_password': 'new-password'}).status_code == 204
        assert other.get('/api/auth/me').status_code == 401
        assert login(c, 'student').status_code == 401
        assert c.post('/api/auth/login', headers=ORIGIN, json={'username': 'student', 'password': 'new-password'}).status_code == 200
        assert c.get('/teacher-only').status_code == 403


def test_origin_validation_and_errors(app):
    with TestClient(app) as c:
        assert c.post('/api/auth/login', json={'username': 'teacher', 'password': 'old-password'}).status_code == 403
        r = c.post('/api/auth/login', headers=ORIGIN, json={'username': 'teacher', 'password': 'secret', 'extra': 1})
        assert r.status_code == 401
        r = c.post('/api/auth/login', headers=ORIGIN, json={'username': ''})
        assert r.status_code == 422
        assert set(r.json()) == {'detail', 'code', 'errors', 'request_id'}
        assert 'input' not in str(r.json())
        assert c.get('/missing').json()['code'] == 'HTTP_404'


def test_expiry_inactive_and_course_policy(app):
    with TestClient(app) as c:
        login(c)
        assert c.get('/course/1').status_code == 503
        app.state.course_access = lambda user, course_id: user.role == 'teacher' and course_id == 1
        assert c.get('/course/1').status_code == 200
        assert c.get('/course/2').status_code == 403
        with app.state.sessions() as db:
            db.scalar(select(AuthSession)).expires_at = time.time() - 1
            db.commit()
        assert c.get('/api/auth/me').status_code == 401
        login(c)
        with app.state.sessions() as db:
            db.scalar(select(User).where(User.username == 'teacher')).active = False
            db.commit()
        assert c.get('/api/auth/me').status_code == 401


def test_rate_limit_persisted(app):
    with TestClient(app) as c:
        for _ in range(10):
            assert c.post('/api/auth/login', headers=ORIGIN, json={'username': 'absent', 'password': 'bad'}).status_code == 401
        assert login(c).status_code == 429


def test_websocket_heartbeat_delivery_and_revocation(app):
    with TestClient(app) as c:
        login(c)
        with c.websocket_connect('/ws', headers=ORIGIN) as ws:
            heartbeat = ws.receive_json()
            assert heartbeat['type'] == 'heartbeat'
            ws.send_json({'type': 'heartbeat.ack', 'id': heartbeat['id']})
            c.portal.call(app.state.hub.publish, 'submission.updated', {'submission_id': 1, 'version': 1}, {1})
            assert ws.receive_json()['type'] == 'submission.updated'
            c.post('/api/auth/logout', headers=csrf(c))
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
        assert not app.state.hub.connections


def test_websocket_rejects_and_times_out(app):
    with TestClient(app) as c:
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect('/ws', headers=ORIGIN):
                pass
        login(c, 'student')
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect('/ws', headers=ORIGIN):
                pass
        login(c)
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect('/ws', headers={'origin': 'https://evil.invalid'}):
                pass
        with c.websocket_connect('/ws', headers=ORIGIN) as ws:
            ws.receive_json()
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()


def test_migration_upgrade_downgrade(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    url = f'sqlite:///{tmp_path / "migration.db"}'
    monkeypatch.setattr(Settings, '__init__', lambda self: setattr(self, 'database_url', url))
    config = Config('server/alembic.ini')
    command.upgrade(config, 'head')
    engine = create_engine(url)
    assert {'users', 'auth_sessions', 'login_attempts'} <= set(inspect(engine).get_table_names())
    command.downgrade(config, 'base')
    assert 'users' not in inspect(engine).get_table_names()
    command.upgrade(config, 'head')
    engine.dispose()


def test_websocket_recipient_isolation(app):
    with TestClient(app) as c:
        login(c)
        with c.websocket_connect('/ws', headers=ORIGIN) as ws:
            c.portal.call(app.state.hub.publish, 'submission.updated', {'submission_id': 99}, {999})
            assert ws.receive_json()['type'] == 'heartbeat'
            # Let the endpoint close cleanly before TestClient tears down its task.
            ws.send_json({'type': 'heartbeat.ack', 'id': 'invalid'})
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()


def test_secure_cookie(app):
    app.state.settings.secure_cookie = True
    with TestClient(app, base_url='https://testserver') as c:
        r = login(c)
        assert 'Secure' in r.headers['set-cookie']
        assert c.get('/api/auth/me').status_code == 200


def test_live_http_server():
    import socket
    import subprocess
    import sys
    import httpx
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server.app.main:app',
        '--host', '127.0.0.1', '--port', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}') as c:
            for _ in range(50):
                try:
                    response = c.get('/openapi.json')
                    break
                except httpx.ConnectError:
                    time.sleep(0.1)
            else:
                pytest.fail('Uvicorn did not start')
            assert response.status_code == 200
            assert '/api/auth/login' in response.json()['paths']
            assert c.get('/api/auth/me').status_code == 401
    finally:
        process.terminate()
        process.wait(timeout=10)
