"""Reproducible real-loopback HTTP benchmark using isolated synthetic accounts and storage."""

import argparse
import asyncio
import csv
import json
import os
import platform
import socket
import tempfile
import threading
import time
from pathlib import Path
from statistics import median
import httpx
import uvicorn
from server.app.main import create_app
from server.app.core.config import Settings
from server.app.core.database import Base, User
from server.app.core.security import hasher
from server.app.models import (
    Teachers,
    Students,
    Courses,
    CourseTeachers,
    CourseEnrollments,
    CodingExams,
    Problems,
    TestCases,
)


def percentile(values, p):
    ordered = sorted(values)
    return ordered[
        min(len(ordered) - 1, max(0, __import__("math").ceil(p * len(ordered)) - 1))
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.trials <= 10:
        parser.error("trials must be 1..10")
    args.output.mkdir(parents=True, exist_ok=True)
    raw = []
    summaries = []
    with tempfile.TemporaryDirectory(prefix="lan-lms-network-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        origin = f"http://127.0.0.1:{port}"
        app = create_app(
            Settings(
                database_url=f'sqlite:///{root/"test.db"}', allowed_origins=(origin,)
            )
        )
        app.state.storage_root = root / "storage"
        app.state.storage_root.mkdir()
        Base.metadata.create_all(app.state.engine)
        password = "Synthetic-benchmark-only"
        encoded = hasher.hash(password)
        with app.state.sessions.begin() as db:
            teacher = User(
                username="bench-teacher", password_hash=encoded, role="teacher"
            )
            db.add(teacher)
            db.flush()
            t = Teachers(
                user_id=teacher.id, teacher_code="B", full_name="Synthetic teacher"
            )
            db.add(t)
            db.flush()
            course = Courses(
                course_code="BENCH",
                course_name="Synthetic benchmark",
                semester="1",
                academic_year="2026-2027",
                status="active",
                grades_published=False,
                final_grade_policy="single_final_exam",
            )
            db.add(course)
            db.flush()
            cid = course.id
            db.add(CourseTeachers(course_id=cid, teacher_id=t.id, role="primary"))
            exam = CodingExams(
                course_id=cid,
                created_by=t.id,
                title="Benchmark",
                grade_component="final",
                starts_at=time.time() - 60,
                ends_at=time.time() + 3600,
                status="scheduled",
                results_published=False,
                score_ladder_json="[0,10]",
            )
            db.add(exam)
            db.flush()
            eid = exam.id
            p = Problems(
                exam_id=eid,
                title="Sum",
                statement="Add two numbers",
                languages_json='["cpp"]',
                io_mode="stdio",
                max_score=100,
                time_limit_ms=2000,
                memory_limit_mib=256,
                comparator="normalized",
            )
            db.add(p)
            db.flush()
            pid = p.id
            (root / "storage/01.in").write_bytes(b"1 2\n")
            (root / "storage/01.out").write_bytes(b"3\n")
            db.add(
                TestCases(
                    problem_id=pid,
                    input_path="01.in",
                    expected_output_path="01.out",
                    weight=100,
                    sort_order=1,
                    is_sample=False,
                )
            )
            for n in range(36 * args.trials):
                u = User(username=f"bench-{n}", password_hash=encoded, role="student")
                db.add(u)
                db.flush()
                s = Students(
                    user_id=u.id, student_code=u.username, full_name=f"Synthetic {n}"
                )
                db.add(s)
                db.flush()
                db.add(
                    CourseEnrollments(course_id=cid, student_id=s.id, status="active")
                )
        server = uvicorn.Server(
            uvicorn.Config(
                app, host="127.0.0.1", port=port, log_level="error", access_log=False
            )
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 15
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("Benchmark server failed to start")
            time.sleep(0.05)

        async def scenario(concurrency, trial, start_index):
            clients = []
            session_ids = []
            try:
                for i in range(concurrency):
                    client = httpx.AsyncClient(
                        base_url=origin, timeout=30, headers={"Origin": origin}
                    )
                    clients.append(client)
                    r = await client.post(
                        "/api/auth/login",
                        json={
                            "username": f"bench-{start_index+i}",
                            "password": password,
                        },
                    )
                    r.raise_for_status()
                    token = (await client.get("/api/auth/csrf")).json()["csrf_token"]
                    client.headers["X-CSRF-Token"] = token
                    r = await client.post(f"/api/coding-exams/{eid}/sessions/start")
                    r.raise_for_status()
                    session_ids.append(r.json()["id"])
                    (await client.get("/api/health")).raise_for_status()

                async def flow(index, client):
                    actions = [
                        ("GET", "/api/courses", None),
                        ("GET", f"/api/coding-exams/{eid}/problems", None),
                        (
                            "POST",
                            f"/api/problems/{pid}/submissions",
                            {
                                "exam_session_id": session_ids[index],
                                "language": "cpp",
                                "source_code": "int main(){return 0;}",
                            },
                        ),
                    ]
                    for method, path, body in actions:
                        started = time.perf_counter()
                        status = 0
                        try:
                            r = await client.request(
                                method,
                                path,
                                json=body,
                                headers={
                                    "Idempotency-Key": f"bench-{trial}-{concurrency}-{index}"
                                },
                            )
                            status = r.status_code
                        except httpx.HTTPError:
                            pass
                        raw.append(
                            dict(
                                concurrency=concurrency,
                                trial=trial,
                                client=index,
                                method=method,
                                path=path,
                                status=status,
                                latency_ms=round(
                                    (time.perf_counter() - started) * 1000, 4
                                ),
                            )
                        )

                begin = time.perf_counter()
                await asyncio.gather(*(flow(i, c) for i, c in enumerate(clients)))
                elapsed = time.perf_counter() - begin
                records = [
                    r
                    for r in raw
                    if r["concurrency"] == concurrency and r["trial"] == trial
                ]
                latencies = [r["latency_ms"] for r in records]
                errors = sum(r["status"] not in (200, 202) for r in records)
                summaries.append(
                    dict(
                        concurrency=concurrency,
                        trial=trial,
                        requests=len(records),
                        elapsed_seconds=elapsed,
                        p50_ms=median(latencies),
                        p95_ms=percentile(latencies, 0.95),
                        throughput_requests_per_second=len(records) / elapsed,
                        error_rate=errors / len(records),
                    )
                )
            finally:
                await asyncio.gather(*(c.aclose() for c in clients))

        async def run():
            index = 0
            for trial in range(1, args.trials + 1):
                for count in (1, 5, 10, 20):
                    await scenario(count, trial, index)
                    index += count

        try:
            asyncio.run(run())
        finally:
            server.should_exit = True
            thread.join(timeout=15)
            app.state.engine.dispose()
    with (args.output / "network-raw.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)
    result = {
        "measured_at": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "cpu": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "transport": "HTTP TCP loopback, direct Uvicorn; synthetic clients on one physical machine",
            "judge_workers": 0,
            "warmup": "login, CSRF, session start and health excluded from measured requests",
        },
        "runs": summaries,
    }
    (args.output / "network-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summaries, indent=2))
    if any(r["error_rate"] for r in summaries):
        raise SystemExit("Benchmark recorded HTTP errors; inspect raw data")


if __name__ == "__main__":
    main()
