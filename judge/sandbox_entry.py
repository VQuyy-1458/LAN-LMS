"""Trusted container supervisor. Expected outputs never enter this container."""

import base64, json, math, os, resource, signal, subprocess, sys, time
from pathlib import Path

mode, input_name, output_name, limit_ms, cap = sys.argv[1:]
limit = int(limit_ms) / 1000
cap = int(cap)
if mode == "file":
    Path(input_name).write_bytes(Path("/case/input").read_bytes())


def limits():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_FSIZE, (cap, cap))
    resource.setrlimit(
        resource.RLIMIT_CPU, (math.ceil(limit) + 1, math.ceil(limit) + 1)
    )
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


command = json.loads(os.environ["PROGRAM_COMMAND"])
with (
    open("/case/input", "rb") as source,
    open("stdout", "wb") as out,
    open("stderr", "wb") as err,
):
    child = subprocess.Popen(
        command, stdin=source, stdout=out, stderr=err, preexec_fn=limits
    )
    started = time.monotonic()
    status = None
    while child.poll() is None:
        if time.monotonic() - started > limit:
            status = "Time Limit Exceeded"
            break
        if Path("stdout").stat().st_size >= cap or Path("stderr").stat().st_size >= cap:
            status = "Runtime Error"
            break
        time.sleep(0.01)
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()
output = Path(output_name) if mode == "file" else Path("stdout")
if status is None:
    status = "Accepted" if child.returncode == 0 else "Runtime Error"
    if not output.is_file() or output.is_symlink():
        status = "Runtime Error"
    elif output.stat().st_size >= cap:
        status = "Runtime Error"
data = output.read_bytes()[:cap] if status == "Accepted" else b""
print(
    json.dumps(
        {
            "status": status,
            "output": base64.b64encode(data).decode(),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }
    )
)
