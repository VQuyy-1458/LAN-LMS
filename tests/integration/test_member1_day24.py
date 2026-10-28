"""Acceptance checks for TV1 A01-A05; A08/Q01 external dependencies are reported separately."""
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from server.app.core.config import PROJECT_ROOT, Settings
from server.app.core.database import Base, User, AuthSession, get_db
from server.app.core.security import hasher, digest, learning_user
from server.app.main import create_app
from server.app.schemas.common import Page, Pagination, utc_iso

ORIGIN = {'Origin': 'http://localhost:3000'}


@pytest.fixture
def app(tmp_path):
    app = create_app(Settings(database_url=f'sqlite:///{tmp_path / "acceptance.db"}'))
    Base.metadata.create_all(app.state.engine)
    with app.state.sessions() as db:
        db.add(User(username='newstudent', password_hash=hasher.hash('15032005'), role='student', must_change_password=True))
        db.add(User(username='teacher', password_hash=hasher.hash('teacher-pass'), role='teacher'))
        db.commit()

    @app.post('/test/learning')
    def learning(user=Depends(learning_user)):
        return {'id': user.user_id}

    @app.get('/test/page', response_model=Page[int])
    def page(pagination=Depends(Pagination)):
        return pagination.response(list(range(50))[pagination.offset:pagination.offset+pagination.page_size], 50)

    @app.post('/test/write')
    def write(db=Depends(get_db)):
        db.execute(text('PRAGMA busy_timeout=1'))
        db.add(User(username='pending', password_hash='unused', role='student'))
        db.commit()
        return {'ok': True}

    @app.post('/test/uncommitted')
    def uncommitted(db=Depends(get_db)):
        db.add(User(username='rollback', password_hash='unused', role='student'))
        db.flush()
        raise RuntimeError('private/internal/path secret-value')

    yield app
    app.state.engine.dispose()


def login(client, username='teacher', password='teacher-pass'):
    return client.post('/api/auth/login', headers=ORIGIN, json={'username':username, 'password':password})


def headers(client):
    return {**ORIGIN, 'X-CSRF-Token':client.get('/api/auth/csrf').json()['csrf_token']}


def test_settings_read_environment_per_instance(monkeypatch):
    monkeypatch.setenv('ALLOWED_ORIGINS',' http://192.168.1.10:8080, https://lms.example ')
    monkeypatch.setenv('SECURE_COOKIE','true')
    s=Settings()
    assert s.allowed_origins == ('http://192.168.1.10:8080','https://lms.example')
    assert s.secure_cookie is True
    monkeypatch.setenv('SECURE_COOKIE','sometimes')
    with pytest.raises(ValueError, match='SECURE_COOKIE'):
        Settings()


@pytest.mark.parametrize('origin', ['*', 'file:///tmp/app', 'http://example.com/path', 'http://name:password@example.com', 'http://example.com:bad'])
def test_invalid_origin_configuration_is_rejected(origin):
    with pytest.raises(ValueError, match='ALLOWED_ORIGINS'):
        Settings(allowed_origins=(origin,))


def test_config_path_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings=Settings(database_url='sqlite:///database/day24.db')
    from sqlalchemy.engine import make_url
    assert Path(make_url(settings.database_url).database) == PROJECT_ROOT / 'database' / 'day24.db'
    with pytest.raises(ValueError, match='DATABASE_URL'):
        Settings(database_url='this is not a URL')


def test_ready_requires_migrated_tables(tmp_path):
    app=create_app(Settings(database_url=f'sqlite:///{tmp_path / "empty.db"}'))
    with TestClient(app) as c:
        assert c.get('/api/health').status_code == 200
        assert c.get('/api/ready').status_code == 503
        Base.metadata.create_all(app.state.engine)
        assert c.get('/api/ready').json() == {'status':'ready'}


def test_db_pragmas_and_rollback(app):
    with app.state.sessions() as db:
        assert db.scalar(text('PRAGMA foreign_keys')) == 1
        assert db.scalar(text('PRAGMA journal_mode')) == 'wal'
        assert db.scalar(text('PRAGMA busy_timeout')) == 5000
    with TestClient(app, raise_server_exceptions=False) as c:
        r=c.post('/test/uncommitted')
        assert r.status_code == 500
        assert 'secret-value' not in r.text
        assert r.headers['X-Request-ID'] == r.json()['request_id']
    with app.state.sessions() as db:
        assert db.scalar(select(User).where(User.username=='rollback')) is None


def test_db_busy_returns_controlled_error(app):
    with app.state.engine.connect() as blocker, TestClient(app) as c:
        blocker.execute(text('BEGIN IMMEDIATE'))
        try:
            r=c.post('/test/write')
            assert r.status_code == 503
            assert r.json()['code'] == 'DATABASE_UNAVAILABLE'
            assert 'INSERT INTO' not in r.text
        finally:
            blocker.rollback()
        assert c.post('/test/write').status_code == 200


def test_page_bounds_and_utc(app):
    with TestClient(app) as c:
        assert c.get('/test/page?page=2&page_size=3').json() == {'items':[3,4,5],'page':2,'page_size':3,'total':50}
        for query in ('page=0', 'page_size=101', 'page_size=-1'):
            assert c.get('/test/page?'+query).json()['code'] == 'VALIDATION_ERROR'
    assert utc_iso(datetime(2026,10,24,7,tzinfo=timezone(timedelta(hours=7)))) == '2026-10-24T00:00:00Z'
    with pytest.raises(ValueError):
        utc_iso(datetime(2026,10,24))


def test_session_survives_app_restart_and_is_hashed(app):
    with TestClient(app) as c:
        assert login(c).status_code == 200
        token=c.cookies.get('lan_lms_session')
        with app.state.sessions() as db:
            session=db.scalar(select(AuthSession))
            assert session.token_hash == digest(token) and session.token_hash != token
            assert db.scalar(select(User).where(User.username=='teacher')).password_hash.startswith('$argon2id$')
        restarted=create_app(app.state.settings)
        with TestClient(restarted) as other:
            other.cookies.set('lan_lms_session',token)
            assert other.get('/api/auth/me').status_code == 200
            assert other.post('/api/auth/logout',headers=headers(other)).status_code == 204
        assert c.get('/api/auth/me').status_code == 401


def test_relogin_rotates_and_revokes_replaced_cookie(app):
    with TestClient(app) as c:
        login(c)
        original=c.cookies.get('lan_lms_session')
        login(c)
        assert c.cookies.get('lan_lms_session') != original
        with app.state.sessions() as db:
            assert db.get(AuthSession,digest(original)) is None


def test_new_student_password_gate_and_validation(app):
    with TestClient(app) as c:
        assert login(c,'newstudent','15032005').status_code == 200
        h=headers(c)
        assert c.post('/test/learning',headers=h).json()['code'] == 'PASSWORD_CHANGE_REQUIRED'
        for password in ('short','x'*129):
            r=c.post('/api/auth/change-password',headers=h,json={'current_password':'15032005','new_password':password})
            assert r.status_code == 422
            assert '15032005' not in r.text
        r=c.post('/api/auth/change-password',headers=h,json={'current_password':'15032005','new_password':'15032005'})
        assert r.json()['code'] == 'PASSWORD_UNCHANGED'
        assert c.post('/api/auth/change-password',headers=h,json={'current_password':'15032005','new_password':'new-password'}).status_code == 204
        assert c.get('/api/auth/me').status_code == 401
        login(c,'newstudent','new-password')
        assert c.post('/test/learning',headers=headers(c)).status_code == 200


def test_csrf_is_stable_for_tabs_and_openapi_documents_errors(app):
    with TestClient(app) as c:
        login(c)
        first=headers(c)
        assert headers(c) == first
        assert c.post('/api/auth/logout',headers=first).status_code == 204
        schema=c.get('/openapi.json').json()
        responses=schema['paths']['/api/auth/login']['post']['responses']
        assert responses['422']['content']['application/json']['schema']['$ref'].endswith('/ErrorResponse')
        assert responses['200']['content']['application/json']['schema']['$ref'].endswith('/LoginResponse')


def test_lan_probe_against_live_backend(tmp_path):
    import os
    import socket
    import subprocess
    import sys
    import time
    import httpx
    import json
    url=f'sqlite:///{tmp_path / "smoke.db"}'
    environment=dict(os.environ, DATABASE_URL=url)
    migration=subprocess.run([sys.executable,'-m','alembic','-c','server/alembic.ini','upgrade','head'],
                             env=environment,capture_output=True,text=True)
    assert migration.returncode == 0, migration.stderr
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server.app.main:app','--host','127.0.0.1','--port',str(port)],
                             env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if httpx.get(f'http://127.0.0.1:{port}/api/ready').status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            time.sleep(0.1)
        else:
            pytest.fail('Backend did not become ready')
        probe=subprocess.run([sys.executable,'scripts/check_lan.py','--base-url',f'http://127.0.0.1:{port}'],
                             capture_output=True,text=True,timeout=20)
        assert probe.returncode == 0, probe.stdout
        assert all(item['passed'] for item in json.loads(probe.stdout)['checks'])
    finally:
        process.terminate()
        process.wait(timeout=10)
