"""Versioned, course-scoped ZIP transfer; no SQL, session tokens or filesystem extraction."""
import hashlib
import io
import json
import math
import secrets
import time
import zipfile
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile
from fastapi.responses import Response
from ... import models as m
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...services import access, files, idempotency
from ...services.activity import audit

router = APIRouter(prefix="/api", tags=["course-transfer"])
LIMIT = 200 * 1024 * 1024
UNPACKED_LIMIT = 500 * 1024 * 1024
# Parents precede children. Teachers are deliberately mapped to the importing owner.
MODELS = [m.Classes, m.User, m.Students, m.Courses, m.CourseClasses,
          m.CourseEnrollments, m.CourseMaterials, m.CalendarEvents, m.AttendanceSessions,
          m.AttendanceRecords, m.Assignments, m.AssignmentSubmissions, m.AssignmentGrades, m.CodingExams,
          m.Problems, m.TestCases, m.ExamRegistrations, m.ExamSessions,
          m.CodeSubmissions, m.JudgeJobs, m.JudgeResults, m.GradeComponents, m.Grades,
          m.ExamSessionEvents]
PATHS = {"storage_path", "source_path", "input_path", "expected_output_path", "attachment_path"}


def export_package(db, user, cid, root):
    course = access.course(db, user, cid, True)
    tables = {}
    selected = {"courses": {cid}}
    # Resolve the scope downwards, then collect profiles belonging to this course.
    scope = [m.CourseClasses, m.CourseEnrollments, m.CourseMaterials, m.CalendarEvents,
             m.AttendanceSessions, m.AttendanceRecords, m.Assignments,
             m.AssignmentSubmissions, m.AssignmentGrades, m.CodingExams, m.Problems, m.TestCases,
             m.ExamRegistrations, m.ExamSessions, m.CodeSubmissions, m.JudgeJobs,
             m.JudgeResults, m.GradeComponents, m.Grades, m.ExamSessionEvents]
    for model in scope:
        table = model.__table__
        parent = next((column for column in table.columns if column.foreign_keys
                       and next(iter(column.foreign_keys)).column.table.name in selected), None)
        if parent is None:
            raise RuntimeError("Missing course scope")
        parent_table = next(iter(parent.foreign_keys)).column.table.name
        rows = list(db.scalars(select(model).where(parent.in_(selected[parent_table]))))
        tables[table.name] = [{c.name: getattr(row, c.name) for c in table.columns} for row in rows]
        selected[table.name] = {row.id for row in rows}
    student_ids = {r["student_id"] for r in tables["course_enrollments"]}
    # Historical records can reference students whose enrollment was later removed.
    for rows in tables.values():
        student_ids.update(r["student_id"] for r in rows if "student_id" in r)
    students = list(db.scalars(select(m.Students).where(m.Students.id.in_(student_ids))))
    class_ids = {s.class_id for s in students if s.class_id is not None}
    class_ids.update(r["class_id"] for r in tables["course_classes"])
    for model, values in [(m.Classes, class_ids), (m.User, {s.user_id for s in students}),
                          (m.Students, student_ids)]:
        tables[model.__tablename__] = [{c.name: getattr(row, c.name) for c in model.__table__.columns}
                                      for row in db.scalars(select(model).where(model.id.in_(values)))]
    tables["courses"] = [{c.name: getattr(course, c.name) for c in m.Courses.__table__.columns}]
    # No teacher account credentials or unrelated users are exported.
    blobs = {}
    total_bytes = 0
    for rows in tables.values():
        for row in rows:
            for column in PATHS & row.keys():
                if row[column] is None: continue
                content = files.resolve(root, row[column]).read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                if digest not in blobs:
                    total_bytes += len(content)
                if total_bytes > UNPACKED_LIMIT:
                    fail(413, "COURSE_TOO_LARGE", "Khóa học vượt 500 MiB; dùng backup toàn hệ thống")
                blobs[digest] = content
                row[column] = digest
    if sum(map(len, blobs.values())) > UNPACKED_LIMIT:
        fail(413, "COURSE_TOO_LARGE", "Khóa học vượt giới hạn gói 500 MiB; dùng backup toàn hệ thống")
    package = {"format": "lan-lms-course", "version": 1, "created_at": time.time(), "tables": tables}
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(package, ensure_ascii=False, allow_nan=False))
        for digest, content in blobs.items():
            archive.writestr("blobs/" + digest, content)
    if output.tell() > LIMIT:
        fail(413, "COURSE_TOO_LARGE", "Gói nén vượt 200 MiB; dùng backup toàn hệ thống")
    return output.getvalue()


def read_package(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)) or len(names) > 50000 or sum(x.file_size for x in infos) > UNPACKED_LIMIT:
                raise ValueError("Archive limits")
            if "manifest.json" not in names or archive.getinfo("manifest.json").file_size > 32 * 1024 * 1024:
                raise ValueError("Manifest limits")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest["format"] != "lan-lms-course" or manifest["version"] != 1:
                raise ValueError("Unsupported format")
            tables = manifest["tables"]
            tables.setdefault("assignment_grades", [])
            if set(tables) != {model.__tablename__ for model in MODELS}:
                raise ValueError("Unknown/missing tables")
            if len(tables["courses"]) != 1 or sum(map(len, tables.values())) > 50000:
                raise ValueError("Row limits")
            for model in MODELS:
                rows = tables[model.__tablename__]
                ids = set()
                for row in rows:
                    if model == m.AttendanceSessions:
                        row.setdefault("event_id", None)
                    if model == m.Assignments:
                        row.setdefault("attachment_path", None)
                        row.setdefault("attachment_filename", None)
                    if set(row) != set(model.__table__.columns.keys()) or type(row["id"]) is not int or row["id"] <= 0 or row["id"] in ids:
                        raise ValueError("Invalid columns/ids")
                    ids.add(row["id"])
                    for column in model.__table__.columns:
                        value = row[column.name]
                        if value is None:
                            if not column.nullable: raise ValueError("Missing required value")
                        elif column.type.python_type is bool:
                            if type(value) is not bool: raise ValueError("Invalid boolean")
                        elif column.type.python_type in (float, int):
                            if type(value) not in (float, int) or not math.isfinite(value): raise ValueError("Invalid number")
                            if column.type.python_type is int and type(value) is not int: raise ValueError("Invalid integer")
                        elif not isinstance(value, str) or len(value) > 1000000:
                            raise ValueError("Invalid string")
            if any(row["role"] != "student" or not row["password_hash"].startswith("$argon2id$") for row in tables["users"]):
                raise ValueError("Invalid student accounts")
            blobs = {}
            for rows in tables.values():
                for row in rows:
                    for column in PATHS & row.keys():
                        if row[column] is None: continue
                        digest = row[column]
                        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest): raise ValueError("Invalid blob name")
                        if digest not in blobs:
                            content = archive.read("blobs/" + digest)
                            if hashlib.sha256(content).hexdigest() != digest: raise ValueError("Blob checksum")
                            blobs[digest] = content
            if set(names) != {"manifest.json", *("blobs/" + digest for digest in blobs)}:
                raise ValueError("Unexpected ZIP entries")
            return tables, blobs
    except (ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, RuntimeError, NotImplementedError, OverflowError):
        fail(422, "INVALID_COURSE_PACKAGE", "Gói khóa học không hợp lệ, thiếu file hoặc sai checksum")


def import_package(db, user, tables, blobs, course_code, root, created_paths):
    teacher = access.teacher(db, user)
    maps = {}
    for model in MODELS:
        name = model.__tablename__
        maps[name] = {}
        for original in tables[name]:
            values = dict(original)
            source_id = values.pop("id")
            for column in model.__table__.columns:
                if not column.foreign_keys or values.get(column.name) is None: continue
                parent = next(iter(column.foreign_keys)).column.table.name
                if parent == "teachers": values[column.name] = teacher.id
                elif parent == "users" and model not in (m.Students,): values[column.name] = user.user_id
                else:
                    try: values[column.name] = maps[parent][values[column.name]]
                    except KeyError: fail(422, "INVALID_COURSE_PACKAGE", "Tham chiếu dữ liệu nằm ngoài khóa học")
            existing = None
            if model == m.Classes:
                existing = db.scalar(select(model).where(model.class_code == values["class_code"]))
                if existing and any(getattr(existing, k) != v for k, v in values.items()):
                    fail(409, "CLASS_CONFLICT", "Mã lớp đã tồn tại với thông tin khác")
            if model == m.User:
                existing = db.scalar(select(model).where(model.username == values["username"]))
                if existing and existing.role != "student": fail(409, "ACCOUNT_CONFLICT", "Tên đăng nhập trùng tài khoản giảng viên")
                # Existing local account password/status is never overwritten.
            if model == m.Students:
                existing = db.scalar(select(model).where(model.student_code == values["student_code"]))
                if existing and any(getattr(existing, k) != v for k, v in values.items()):
                    fail(409, "STUDENT_CONFLICT", "Mã sinh viên đã tồn tại với hồ sơ khác; chưa nhập dữ liệu")
                if not existing and db.scalar(select(model.id).where(model.user_id == values["user_id"])):
                    fail(409, "ACCOUNT_CONFLICT", "Tài khoản đã gắn với mã sinh viên khác")
            if existing:
                maps[name][source_id] = existing.id
                continue
            if model == m.Courses:
                values["course_code"] = course_code
                if db.scalar(select(model.id).where(model.course_code == course_code, model.semester == values["semester"], model.academic_year == values["academic_year"])):
                    fail(409, "COURSE_EXISTS", "Khóa học đã tồn tại; chọn mã mới. Không ghi đè khóa cũ")
            if model == m.AttendanceSessions: values["token_hash"] = secrets.token_hex(32)
            if model == m.JudgeJobs and values["status"] in ("running", "pending"):
                values.update(status="pending", attempt_id=None, lease_until=None, worker_id=None, attempt_count=0, started_at=None, finished_at=None)
            if model == m.CodeSubmissions and values["status"] in ("Compiling", "Running"): values["status"] = "Pending"
            for column in PATHS & values.keys():
                if values[column] is None: continue
                path = files.save(root, "course_imports", blobs[values[column]])
                created_paths.append(path)
                values[column] = path
            row = model(**values)
            db.add(row)
            db.flush()
            maps[name][source_id] = row.id
    cid = next(iter(maps["courses"].values()))
    db.add(m.CourseTeachers(course_id=cid, teacher_id=teacher.id, role="owner"))
    audit(db, user.user_id, "import", "course", cid, {"format": 1, "source_course": tables["courses"][0]["course_code"]})
    return {"id": cid, "course_code": course_code}


@router.get("/courses/{cid}/export-package")
def export(cid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    idempotency.write_lock(db)
    data = export_package(db, user, cid, request.app.state.storage_root)
    db.rollback()
    return Response(data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="course-{cid}.zip"'})


@router.post("/courses/import-package/preview")
async def preview(file: UploadFile = File(...), db=Depends(get_db), user=Depends(learning_user)):
    access.teacher(db, user)
    _, data = await files.read_upload(file, LIMIT, {".zip"})
    tables, _ = read_package(data)
    course = tables["courses"][0]
    return {"name": course["course_name"], "course_code": course["course_code"],
            "counts": {name: len(rows) for name, rows in tables.items()}}


@router.post("/courses/import-package", status_code=201)
async def import_course(request: Request, file: UploadFile = File(...), course_code: str = Form(..., min_length=1, max_length=128),
                        key: str = Header(..., alias="Idempotency-Key"), db=Depends(get_db), user=Depends(learning_user)):
    _, data = await files.read_upload(file, LIMIT, {".zip"})
    tables, blobs = read_package(data)
    created = []
    try:
        result, status = idempotency.run(db, user, "POST", "/api/courses/import-package", key,
            idempotency.request_hash({"course_code": course_code}, data),
            lambda: import_package(db, user, tables, blobs, course_code, request.app.state.storage_root, created),
            status=201, authorize=lambda: access.teacher(db, user))
        return Response(json.dumps(result), status_code=status, media_type="application/json")
    except BaseException as error:
        db.rollback()
        for path in created: (Path(request.app.state.storage_root) / path).unlink(missing_ok=True)
        if isinstance(error, IntegrityError): fail(409, "IMPORT_CONFLICT", "Dữ liệu bị trùng hoặc mâu thuẫn; chưa nhập khóa học")
        raise
