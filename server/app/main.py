import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import Settings
from .core.database import database
from .core.realtime import EventHub, websocket_endpoint
from .modules.auth import router

logger = logging.getLogger('lan_lms')


def create_app(settings=None):
    settings = settings or Settings()
    engine, sessions = database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        yield
        for ws in list(app.state.hub.connections):
            await ws.close(1001)
        engine.dispose()

    app = FastAPI(title='LAN-LMS', version='1.1', lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = sessions
    app.state.hub = EventHub()
    app.state.course_access = None

    def error(request, status, code, detail, errors=None):
        return JSONResponse(status_code=status, content={'detail': detail, 'code': code,
            'request_id': getattr(request.state, 'request_id', str(uuid.uuid4())), 'errors': errors or []})

    @app.middleware('http')
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        try:
            response = await call_next(request)
        except Exception:
            # Do not log request bodies/passwords or SQL bound parameters.
            logger.error('Unhandled request error id=%s', request.state.request_id)
            response = error(request, 500, 'INTERNAL_ERROR', 'Lỗi hệ thống')
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if request.url.path.startswith('/api/auth'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        payload = exc.detail if isinstance(exc.detail, dict) else {'detail': str(exc.detail), 'code': f'HTTP_{exc.status_code}'}
        return error(request, exc.status_code, payload['code'], payload['detail'])

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in exc.errors()]
        return error(request, 422, 'VALIDATION_ERROR', 'Dữ liệu không hợp lệ', errors)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error(request, 409, 'DATA_CONFLICT', 'Dữ liệu xung đột')

    @app.exception_handler(OperationalError)
    async def database_error(request, exc):
        return error(request, 503, 'DATABASE_UNAVAILABLE', 'Database tạm không sẵn sàng')

    @app.get('/api/health', tags=['system'])
    def health():
        with sessions() as db:
            db.execute(text('SELECT 1'))
        return {'status': 'ok'}

    app.include_router(router)
    app.websocket('/ws')(websocket_endpoint)
    return app


app = create_app()
