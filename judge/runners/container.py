"""Docker CLI runner: compile once, run each test in a fresh isolated container."""

import base64, json, os, subprocess, tempfile, time, uuid
from dataclasses import dataclass
from pathlib import Path
from ..languages.config import LANGUAGES
from ..limits import Limits
from ..comparators.output import compare


@dataclass(frozen=True)
class TestCase:
    __test__ = False
    input: bytes
    expected: bytes
    points: float = 1


@dataclass
class Result:
    verdict: str
    score: float | None
    max_score: float
    compile_message: str = ""


class InfrastructureError(RuntimeError):
    pass


class DockerJudge:
    def __init__(self, image="lan-lms-judge:day25"):
        self.image = image

    def _run(
        self,
        command,
        mounts,
        seconds,
        memory=256,
        env=None,
        input_file=None,
        cap=2 * 1024 * 1024,
    ):
        name = "lan-lms-" + uuid.uuid4().hex
        args = [
            "docker",
            "run",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--user",
            "65534:65534",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--cpus",
            "1",
            "--pids-limit",
            "64",
            "--ulimit",
            "fsize=67108864:67108864",
            "--memory",
            f"{memory}m",
            "--memory-swap",
            f"{memory}m",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=32m,mode=1777",
            "--tmpfs",
            "/work:rw,nosuid,size=64m,mode=1777",
        ]
        for source, target, writable in mounts:
            args += [
                "--mount",
                f"type=bind,source={source},target={target}"
                + ("" if writable else ",readonly"),
            ]
        for key, value in (env or {}).items():
            args += ["--env", f"{key}={value}"]
        args += [self.image] + command
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            process = subprocess.Popen(args, stdout=out, stderr=err)
            started = time.monotonic()
            reason = None
            try:
                while process.poll() is None:
                    if time.monotonic() - started > seconds:
                        reason = "timeout"
                        break
                    if (
                        os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size
                        > cap
                    ):
                        reason = "output"
                        break
                    time.sleep(0.02)
                if reason:
                    subprocess.run(
                        ["docker", "rm", "-f", name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=10,
                    )
                    process.kill()
                process.wait(timeout=10)
                out.seek(0)
                err.seek(0)
                stdout = out.read(cap)
                stderr = err.read(cap)
                state = subprocess.run(
                    ["docker", "inspect", "--format", "{{json .State}}", name],
                    capture_output=True,
                    timeout=10,
                )
                if state.returncode:
                    raise InfrastructureError(
                        "Docker did not create the execution container"
                    )
                meta = json.loads(state.stdout)
                if meta.get("OOMKilled"):
                    return 137, stdout, stderr, "oom"
                return process.returncode, stdout, stderr, reason
            except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
                raise InfrastructureError("Docker execution unavailable") from exc
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                subprocess.run(
                    ["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )

    def grade(
        self,
        source,
        language,
        cases,
        limits=None,
        io_mode="stdio",
        input_filename="input.txt",
        output_filename="output.txt",
        comparator="exact",
    ):
        limits = limits or Limits()
        limits.validate()
        if language not in LANGUAGES:
            raise ValueError("Unsupported language")
        if len(source.encode()) > 256 * 1024 or not cases or len(cases) > 100:
            raise ValueError("Invalid source or cases")
        if io_mode not in ("stdio", "file") or comparator not in (
            "exact",
            "normalized",
        ):
            raise ValueError("Invalid problem config")
        for name in (input_filename, output_filename):
            if (
                not name
                or "/" in name
                or "\\" in name
                or ":" in name
                or name in (".", "..", "stdout", "stderr")
            ):
                raise ValueError("File I/O requires simple basenames")
        if input_filename == output_filename:
            raise ValueError("Input and output file must differ")
        if any(
            c.points < 0 or len(c.input) > 1024 * 1024 or len(c.expected) > 1024 * 1024
            for c in cases
        ):
            raise ValueError("Invalid test data")
        maximum = sum(c.points for c in cases)
        with tempfile.TemporaryDirectory(prefix="lan-lms-judge-") as directory:
            root = Path(directory)
            src = root / "source"
            artifacts = root / "artifacts"
            case = root / "case"
            for p in (src, artifacts, case):
                p.mkdir()
                p.chmod(0o777)
            filename, compiler, program = LANGUAGES[language]
            (src / filename).write_text(source, encoding="utf-8")
            (src / filename).chmod(0o644)
            code, out, err, reason = self._run(
                compiler,
                [(src, "/source", False), (artifacts, "/artifacts", True)],
                30,
                memory=768,
                cap=65536,
            )
            if code or reason:
                message = (
                    (err or out)
                    .decode("utf-8", errors="replace")[:16384]
                    .replace(str(root), "[work]")
                    .replace("/source/", "")
                )
                return Result("Compile Error", 0, maximum, message)
            score = 0
            first = None
            for test in cases:
                (case / "input").write_bytes(test.input)
                (case / "input").chmod(0o644)
                code, out, err, reason = self._run(
                    [
                        "python3",
                        "/opt/sandbox_entry.py",
                        io_mode,
                        input_filename,
                        output_filename,
                        str(limits.time_ms),
                        str(limits.output_bytes),
                    ],
                    [(artifacts, "/artifacts", False), (case, "/case", False)],
                    limits.time_ms / 1000 + 10,
                    memory=limits.memory_mib,
                    env={"PROGRAM_COMMAND": json.dumps(program)},
                )
                if reason == "oom":
                    status = "Memory Limit Exceeded"
                elif reason == "timeout":
                    status = "Time Limit Exceeded"
                elif reason == "output":
                    status = "Runtime Error"
                elif code:
                    raise InfrastructureError("Execution supervisor failed")
                else:
                    try:
                        payload = json.loads(out)
                        status = payload["status"]
                        if status == "Accepted" and not compare(
                            base64.b64decode(payload["output"], validate=True),
                            test.expected,
                            comparator,
                        ):
                            status = "Wrong Answer"
                    except (ValueError, KeyError) as exc:
                        raise InfrastructureError("Invalid supervisor result") from exc
                if status == "Accepted":
                    score += test.points
                elif first is None:
                    first = status
            return Result(first or "Accepted", score, maximum)
