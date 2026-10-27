"""Bounded testcase ZIP ingestion and permission-scoped example/download views."""
import io
import re
import zipfile
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, File, Header, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func
from ...core.database import get_db
from ...core.security import learning_user, fail
from ...models import TestCases
from ...services import files, idempotency
from ...services.activity import audit
from . import service as svc

router = APIRouter()


def unpack_cases(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 200 or len({x.filename for x in entries}) != len(entries): raise ValueError()
            if sum(x.file_size for x in entries) > 50 * 1024 * 1024: raise ValueError()
            pairs = {}
            for entry in entries:
                if entry.file_size > 1024 * 1024 or not re.fullmatch(r"[A-Za-z0-9_-]+\.(in|out)", entry.filename): raise ValueError()
                stem, extension = entry.filename.rsplit(".", 1)
                pairs.setdefault(stem, {})[extension] = archive.read(entry)
            if any(set(pair) != {"in", "out"} for pair in pairs.values()): raise ValueError()
            return [(stem, pairs[stem]["in"], pairs[stem]["out"]) for stem in sorted(pairs)]
    except (ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError):
        fail(422, "INVALID_TEST_ZIP", "ZIP cần 1-100 cặp tên.in/tên.out ở thư mục gốc; mỗi file tối đa 1 MiB, giải nén tối đa 50 MiB")


@router.post("/problems/{pid}/test-cases/import-zip", status_code=201)
async def import_zip(pid: int, request: Request, file: UploadFile = File(...),
                     key: str = Header(..., alias="Idempotency-Key"), db=Depends(get_db), user=Depends(learning_user)):
    _, data = await files.read_upload(file, 20 * 1024 * 1024, {".zip"})
    pairs = unpack_cases(data)
    saved = []
    def authorize():
        problem, exam = svc.problem(db, user, pid, True)
    def operation():
        problem, exam = svc.problem(db, user, pid, True)
        svc.editable(db, exam)
        if db.scalar(select(func.count(TestCases.id)).where(TestCases.problem_id == pid)):
            fail(409, "TESTS_ALREADY_EXIST", "Nhập ZIP dành cho bài chưa có testcase; các test hiện có được giữ nguyên")
        for ordinal, (stem, inp, out) in enumerate(pairs, 1):
            paths = []
            for content in (inp, out):
                path = files.save(request.app.state.storage_root, "test_cases", content)
                saved.append(path)
                paths.append(path)
            db.add(TestCases(problem_id=pid, input_path=paths[0], expected_output_path=paths[1],
                             weight=problem.max_score / len(pairs), sort_order=ordinal,
                             is_sample=stem.lower().startswith(("sample_", "sample-"))))
        audit(db, user.user_id, "import-tests", "problem", pid, {"count": len(pairs)})
        return {"count": len(pairs), "total_weight": problem.max_score}
    try:
        result, status = idempotency.run(db, user, "POST", f"/api/problems/{pid}/test-cases/import-zip", key,
            idempotency.request_hash({"problem_id": pid}, data), operation, status=201, authorize=authorize)
        return JSONResponse(result, status_code=status)
    except BaseException:
        db.rollback()
        for path in saved: (Path(request.app.state.storage_root) / path).unlink(missing_ok=True)
        raise


@router.get("/problems/{pid}/examples")
def examples(pid: int, request: Request, db=Depends(get_db), user=Depends(learning_user)):
    svc.problem(db, user, pid)
    rows = list(db.scalars(select(TestCases).where(TestCases.problem_id == pid, TestCases.is_sample == True).order_by(TestCases.sort_order).limit(20)))
    result = []
    for row in rows:
        def read(path):
            with files.resolve(request.app.state.storage_root, path).open("rb") as source:
                content = source.read(65537)
            return content[:65536].decode("utf-8", errors="replace"), len(content) > 65536
        inp, cut_input = read(row.input_path)
        out, cut_output = read(row.expected_output_path)
        result.append({"input": inp, "output": out, "truncated": cut_input or cut_output})
    return {"items": result}


@router.get("/test-cases/{tid}/file")
def download(tid: int, kind: Literal["input", "output"], request: Request, db=Depends(get_db), user=Depends(learning_user)):
    row = db.get(TestCases, tid)
    if not row: fail(404, "NOT_FOUND", "Không tìm thấy testcase")
    svc.problem(db, user, row.problem_id, True)
    path = row.input_path if kind == "input" else row.expected_output_path
    return FileResponse(files.resolve(request.app.state.storage_root, path), filename=f"{tid}.{'in' if kind == 'input' else 'out'}", media_type="application/octet-stream")
