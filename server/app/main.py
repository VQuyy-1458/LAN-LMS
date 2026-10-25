import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import Settings
from .core.database import database
from .core.realtime import EventHub, websocket_endpoint
from .modules.auth import router
from .schemas.common import ErrorResponse
from .core.config import PROJECT_ROOT
from .modules.courses.router import router as courses_router
from .modules.students.router import router as students_router
from .modules.materials.router import router as materials_router
from .modules.assignments.router import router as assignments_router
from .modules.courses.calendar import router as calendar_router
from .modules.attendance.router import router as attendance_router
from .modules.coding_exams.router import router as exams_router
from .modules.submissions.router import router as submissions_router
from .services.notifications import dispatch
from .modules.gradebook.router import router as gradebook_router
from .modules.courses.dashboard import router as dashboard_router
from .services import access

logger = logging.getLogger("lan_lms")


def create_app(settings=None):
    settings = settings or Settings()
    engine, sessions = database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        bridge = asyncio.create_task(dispatch(app))
        try:
            yield
        finally:
            bridge.cancel()
            await asyncio.gather(bridge, return_exceptions=True)
        for ws in list(app.state.hub.connections):
            await ws.close(1001)
        engine.dispose()

    app = FastAPI(
        title="LAN-LMS",
        version="1.1",
        lifespan=lifespan,
        responses={
            code: {"model": ErrorResponse}
            for code in (400, 401, 403, 404, 409, 413, 422, 429, 500, 503)
        },
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = sessions
    app.state.hub = EventHub()
    app.state.storage_root = __import__("pathlib").Path(
        __import__("os").getenv("STORAGE_ROOT", str(PROJECT_ROOT / "storage"))
    )

    def course_policy(user, course_id):
        with sessions() as db:
            try:
                access.course(db, user, course_id)
                return True
            except StarletteHTTPException:
                return False

    app.state.course_access = course_policy

    def error(request, status, code, detail, errors=None):
        return JSONResponse(
            status_code=status,
            content={
                "detail": detail,
                "code": code,
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "errors": errors or [],
            },
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        try:
            response = await call_next(request)
        except Exception:
            # Do not log request bodies/passwords or SQL bound parameters.
            logger.error("Unhandled request error id=%s", request.state.request_id)
            response = error(request, 500, "INTERNAL_ERROR", "Lá»—i há»‡ thá»‘ng")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        payload = (
            exc.detail
            if isinstance(exc.detail, dict)
            else {"detail": str(exc.detail), "code": f"HTTP_{exc.status_code}"}
        )
        response = error(
            request,
            exc.status_code,
            payload.get("code", f"HTTP_{exc.status_code}"),
            payload.get("detail", "YÃªu cáº§u khÃ´ng há»£p lá»‡"),
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [
            {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
            for e in exc.errors()
        ]
        return error(
            request, 422, "VALIDATION_ERROR", "Dá»¯ liá»‡u khÃ´ng há»£p lá»‡", errors
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error(request, 409, "DATA_CONFLICT", "Dá»¯ liá»‡u xung Ä‘á»™t")

    @app.exception_handler(OperationalError)
    async def database_error(request, exc):
        return error(
            request, 503, "DATABASE_UNAVAILABLE", "Database táº¡m khÃ´ng sáºµn sÃ ng"
        )

    @app.get("/api/health", tags=["system"])
    def health():
        with sessions() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}

    @app.get("/api/ready", tags=["system"])
    def ready():
        # SELECT 1 alone cannot detect an unmigrated database.
        with sessions() as db:
            db.execute(
                text(
                    "SELECT id, username, password_hash, role, active, must_change_password FROM users LIMIT 0"
                )
            )
            db.execute(
                text(
                    "SELECT token_hash, user_id, csrf_hash, expires_at FROM auth_sessions LIMIT 0"
                )
            )
            db.execute(text("SELECT id, ip, created_at FROM login_attempts LIMIT 0"))
            db.execute(text("SELECT id, score_ladder_json FROM coding_exams LIMIT 0"))
            db.execute(text("SELECT id, event_type, data_json FROM realtime_events LIMIT 0"))
            db.execute(text("SELECT id, title FROM attendance_sessions LIMIT 0"))
        return {"status": "ready"}

    app.include_router(router)
    for module_router in (
        courses_router,
        students_router,
        materials_router,
        assignments_router,
        calendar_router,
        attendance_router,
        exams_router,
        submissions_router,
        gradebook_router,
        dashboard_router,
    ):
        app.include_router(module_router)
    app.websocket("/ws")(websocket_endpoint)
    return app


app = create_app()
