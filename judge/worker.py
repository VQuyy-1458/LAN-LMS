"""Run an independent judge worker; no student program runs in the API process."""

import argparse
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from sqlalchemy import select
from server.app.core.config import Settings, PROJECT_ROOT
from server.app.core.database import database
from server.app.models import CodeSubmissions, Problems, TestCases
from server.app.services.files import resolve
from . import job_queue as queue
from .runners.container import DockerJudge, TestCase, InfrastructureError
from .limits import Limits

logger = logging.getLogger("lan_lms.worker")


def execute(sessions, root, claim, judge=None):
    judge = judge or DockerJudge(os.getenv("JUDGE_IMAGE", "lan-lms-judge:day25"))
    with sessions() as db:
        sub = db.get(CodeSubmissions, claim.submission_id)
        p = db.get(Problems, sub.problem_id)
        source = resolve(root, sub.source_path).read_text(encoding="utf-8")
        cases = [
            TestCase(
                resolve(root, t.input_path).read_bytes(),
                resolve(root, t.expected_output_path).read_bytes(),
                t.weight,
            )
            for t in db.scalars(
                select(TestCases)
                .where(TestCases.problem_id == p.id)
                .order_by(TestCases.sort_order, TestCases.id)
            )
        ]
        config = dict(
            language=sub.language,
            cases=cases,
            limits=Limits(p.time_limit_ms, p.memory_limit_mib),
            io_mode=p.io_mode,
            input_filename=p.input_filename or "input.txt",
            output_filename=p.output_filename or "output.txt",
            comparator=p.comparator,
        )
    stopped = threading.Event()
    lost = threading.Event()
    start = time.perf_counter()
    compiled = None

    def heartbeat():
        while not stopped.wait(10):
            try:
                queue.renew(sessions, claim)
            except Exception:
                lost.set()
                return

    def progress(stage):
        nonlocal compiled
        if lost.is_set():
            raise queue.LostLease()
        if stage == "Running":
            compiled = time.perf_counter()
            queue.running(sessions, claim, (compiled - start) * 1000)

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        result = judge.grade(source=source, progress=progress, **config)
        elapsed = (time.perf_counter() - start) * 1000
        compile_ms = ((compiled - start) * 1000) if compiled else elapsed
        if lost.is_set():
            raise queue.LostLease()
        queue.complete(
            sessions, claim, result, compile_ms, max(0, elapsed - compile_ms)
        )
    finally:
        stopped.set()
        thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--worker-id", default=uuid.uuid4().hex[:12])
    parser.add_argument(
        "--storage-root",
        type=Path,
        default=Path(os.getenv("STORAGE_ROOT", PROJECT_ROOT / "storage")),
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    engine, sessions = database(Settings().database_url)
    try:
        while True:
            c = queue.claim(sessions, args.worker_id)
            if not c:
                if args.once:
                    return
                time.sleep(1)
                continue
            try:
                execute(sessions, args.storage_root, c)
            except queue.LostLease:
                logger.warning("Lease lost for job %s", c.job_id)
            except Exception:
                logger.error(
                    "Judge attempt failed for job %s; retrying without exposing payload",
                    c.job_id,
                )
                try:
                    queue.retry(sessions, c)
                except queue.LostLease:
                    pass
                if not args.once:
                    time.sleep(2)
            if args.once:
                return
    except KeyboardInterrupt:
        pass
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
