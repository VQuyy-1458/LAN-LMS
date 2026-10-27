"""Atomic SQLite unit of work. Call before other DB reads; mutation and replay commit together."""

import hashlib
import json
import time
from sqlalchemy import select, text
from ..models import IdempotencyKeys
from ..core.security import fail


def write_lock(db):
    if db.in_transaction() and db.info.get("mutation_lock"):
        return
    if db.in_transaction():
        raise RuntimeError("Start atomic mutation before any DB reads")
    if db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    db.info["mutation_lock"] = True


def request_hash(metadata, content=b""):
    value = json.dumps(
        metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(value + b"\0" + content).hexdigest()


def run(
    db, user, method, path, key, fingerprint, operation, status=200, authorize=None
):
    if not key or not 1 <= len(key) <= 128:
        fail(400, "IDEMPOTENCY_KEY_REQUIRED", "Cần Idempotency-Key dài 1–128 ký tự")
    write_lock(db)
    if authorize:
        authorize()
    now = time.time()
    record = db.scalar(
        select(IdempotencyKeys).where(
            IdempotencyKeys.user_id == user.user_id,
            IdempotencyKeys.method == method,
            IdempotencyKeys.path == path,
            IdempotencyKeys.key == key,
        )
    )
    if record and record.expires_at <= now:
        db.delete(record)
        db.flush()
        record = None
    if record:
        if record.request_hash != fingerprint:
            fail(409, "IDEMPOTENCY_CONFLICT", "Key đã dùng cho dữ liệu khác")
        if record.status != "completed" or record.response_json is None:
            fail(409, "REQUEST_IN_PROGRESS", "Yêu cầu đang xử lý")
        # Callers must check current access inside operation before replay via authorize callback.
        return json.loads(record.response_json), record.response_status
    result = operation()
    db.add(
        IdempotencyKeys(
            user_id=user.user_id,
            method=method,
            path=path,
            key=key,
            request_hash=fingerprint,
            status="completed",
            response_status=status,
            response_json=json.dumps(result, ensure_ascii=False),
            expires_at=now + 86400,
        )
    )
    db.commit()
    return result, status
