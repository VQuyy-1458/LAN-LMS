"""Real Docker judge throughput experiment: 20 submissions, 1/2 workers, repeated trials."""

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from statistics import median
from sqlalchemy import select
from server.app.core.database import Base, User, database
from server.app.models import (
    Teachers,
    Students,
    Courses,
    CourseEnrollments,
    CodingExams,
    Problems,
    TestCases,
    ExamRegistrations,
    ExamSessions,
    CodeSubmissions,
    JudgeJobs,
)

SOURCES = {
    "c": '#include <stdio.h>\n#include <unistd.h>\nint main(){int a,b;scanf("%d%d",&a,&b);SLOW;printf("%d\\n",a+b);return 0;}',
    "cpp": '#include <iostream>\n#include <unistd.h>\nint main(){int a,b;std::cin>>a>>b;SLOW;std::cout<<a+b<<"\\n";}',
    "java": "import java.util.*; public class Main{public static void main(String[] args)throws Exception{Scanner s=new Scanner(System.in);int a=s.nextInt(),b=s.nextInt();SLOW;System.out.println(a+b);}}",
}


def run(workers, trial, count):
    with tempfile.TemporaryDirectory(prefix="lan-lms-worker-bench-") as directory:
        root = Path(directory)
        storage = root / "storage"
        storage.mkdir()
        url = f'sqlite:///{root/"bench.db"}'
        engine, sessions = database(url)
        Base.metadata.create_all(engine)
        (storage / "01.in").write_bytes(b"1 2\n")
        (storage / "01.out").write_bytes(b"3\n")
        with sessions.begin() as db:
            u = User(
                username="teacher",
                password_hash="not-login-enabled",
                role="teacher",
                active=False,
            )
            db.add(u)
            db.flush()
            t = Teachers(user_id=u.id, teacher_code="T", full_name="Synthetic teacher")
            db.add(t)
            db.flush()
            c = Courses(
                course_code="BENCH",
                course_name="Synthetic benchmark",
                semester="1",
                academic_year="2026",
                status="active",
                grades_published=False,
                final_grade_policy="single_final_exam",
            )
            db.add(c)
            db.flush()
            e = CodingExams(
                course_id=c.id,
                created_by=t.id,
                title="Benchmark",
                grade_component="final",
                starts_at=time.time() - 60,
                ends_at=time.time() + 3600,
                status="scheduled",
                results_published=False,
                score_ladder_json="[0,10]",
            )
            db.add(e)
            db.flush()
            p = Problems(
                exam_id=e.id,
                title="Sum",
                statement="Sum",
                languages_json='["c","cpp","java"]',
                io_mode="stdio",
                max_score=100,
                time_limit_ms=3000,
                memory_limit_mib=256,
                comparator="normalized",
            )
            db.add(p)
            db.flush()
            db.add(
                TestCases(
                    problem_id=p.id,
                    input_path="01.in",
                    expected_output_path="01.out",
                    weight=100,
                    sort_order=1,
                    is_sample=False,
                )
            )
            for n in range(count):
                u = User(
                    username=f"s{n}",
                    password_hash="not-login-enabled",
                    role="student",
                    active=False,
                )
                db.add(u)
                db.flush()
                s = Students(
                    user_id=u.id, student_code=u.username, full_name="Synthetic student"
                )
                db.add(s)
                db.flush()
                db.add(
                    CourseEnrollments(course_id=c.id, student_id=s.id, status="active")
                )
                reg = ExamRegistrations(
                    exam_id=e.id,
                    student_id=s.id,
                    registered_at=time.time(),
                    status="active",
                )
                db.add(reg)
                db.flush()
                exam_session = ExamSessions(
                    registration_id=reg.id,
                    started_at=time.time(),
                    ends_at=e.ends_at,
                    status="active",
                )
                db.add(exam_session)
                db.flush()
                language = ("c", "cpp", "java")[n % 3]
                slow = n % 4 == 0
                source = SOURCES[language].replace(
                    "SLOW",
                    (
                        ("Thread.sleep(1000)" if language == "java" else "sleep(1)")
                        if slow
                        else ""
                    ),
                )
                path = f"source-{n}"
                (storage / path).write_text(source, encoding="utf-8")
                sub = CodeSubmissions(
                    exam_session_id=exam_session.id,
                    problem_id=p.id,
                    student_id=s.id,
                    attempt_no=1,
                    language=language,
                    source_path=path,
                    received_at=time.time(),
                    status="Pending",
                    version=1,
                )
                db.add(sub)
                db.flush()
                db.add(
                    JudgeJobs(
                        submission_id=sub.id,
                        status="pending",
                        attempt_count=0,
                        created_at=sub.received_at,
                    )
                )
        env = {
            **os.environ,
            "DATABASE_URL": url,
            "STORAGE_ROOT": str(storage),
            "PYTHONUTF8": "1",
        }
        processes = []
        begin = time.perf_counter()
        with (root / "worker.log").open("w", encoding="utf-8") as log:
            try:
                for n in range(workers):
                    processes.append(
                        subprocess.Popen(
                            [
                                sys.executable,
                                "-m",
                                "judge.worker",
                                "--worker-id",
                                f"bench-{n}",
                            ],
                            env=env,
                            stdout=log,
                            stderr=log,
                        )
                    )
                deadline = time.monotonic() + 1200
                while True:
                    with sessions() as db:
                        jobs = list(db.scalars(select(JudgeJobs)))
                        if all(j.status == "done" for j in jobs):
                            break
                    if any(p.poll() is not None for p in processes):
                        raise RuntimeError("Worker exited during benchmark")
                    if time.monotonic() > deadline:
                        raise TimeoutError("Judge benchmark timed out")
                    time.sleep(0.2)
                elapsed = time.perf_counter() - begin
                with sessions() as db:
                    raw = [
                        {
                            "submission_id": s.id,
                            "language": s.language,
                            "verdict": s.status,
                            "queue_wait_ms": (j.started_at - j.created_at) * 1000,
                            "compile_ms": j.compile_ms,
                            "run_ms": j.run_ms,
                            "end_to_end_ms": (j.finished_at - s.received_at) * 1000,
                            "attempts": j.attempt_count,
                        }
                        for j, s in db.execute(
                            select(JudgeJobs, CodeSubmissions).join(CodeSubmissions)
                        )
                    ]
                if any(r["verdict"] != "Accepted" for r in raw):
                    raise RuntimeError(
                        "Unexpected verdict in benchmark: " + json.dumps(raw)
                    )
                return dict(
                    workers=workers,
                    trial=trial,
                    jobs=count,
                    elapsed_seconds=elapsed,
                    throughput_jobs_per_second=count / elapsed,
                    p50_queue_wait_ms=median(r["queue_wait_ms"] for r in raw),
                    p50_end_to_end_ms=median(r["end_to_end_ms"] for r in raw),
                    busy_time_ratio=sum(r["compile_ms"] + r["run_ms"] for r in raw)
                    / 1000
                    / (workers * elapsed),
                    raw=raw,
                )
            finally:
                for p in processes:
                    if p.poll() is None:
                        p.terminate()
                for p in processes:
                    try:
                        p.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=5)
                engine.dispose()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--jobs", type=int, default=20)
    args = p.parse_args()
    if not 1 <= args.trials <= 10 or not 1 <= args.jobs <= 100:
        p.error("trials 1..10, jobs 1..100")
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for trial in range(1, args.trials + 1):
        for workers in (1, 2):
            result = run(workers, trial, args.jobs)
            results.append(result)
            print(
                json.dumps({k: v for k, v in result.items() if k != "raw"}), flush=True
            )
    (args.output / "judge-summary.json").write_text(
        json.dumps(
            {
                "measured_at": __import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
                "environment": {
                    "os": platform.platform(),
                    "python": platform.python_version(),
                    "cpu": platform.processor(),
                    "logical_cpus": os.cpu_count(),
                    "image": os.getenv("JUDGE_IMAGE", "lan-lms-judge:day25"),
                    "dataset": "20 isolated C/C++/Java sum programs, one test, every fourth program sleeps 1s, 3000ms/256MiB, fresh database per trial",
                    "utilization_note": "busy_time_ratio is wall-clock worker occupancy, not CPU utilization",
                },
                "runs": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
