"""Pre-live stop-control check (T-221 T5): no model is loaded.

Two synthetic children run under owned Job Objects, and the host-calibrated stall rule
watches each one's output, driven by explicit synthetic rates. A chatty child keeps
progressing and must survive three stall windows. A silent child (with a grandchild) must
be stopped by the stall rule, and its owned tree must be gone within INT-0004 AC2's cleanup
bound. An unrelated sentinel must survive.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import psutil

from hermes_cli.local_runtime.processes import spawn_server
from hermes_cli.local_runtime.throughput import (
    Calibration,
    StallClock,
    TimeParams,
    stall_window,
)

CLEANUP_S = 5
OBSERVATION_PERIOD = 0.5
SILENT_TREE = (
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3600)'])\n"
    "time.sleep(3600)\n"
)
CHATTY = (
    "import sys, time\n"
    "while True:\n"
    "    print('progress', flush=True)\n"
    "    time.sleep(float(sys.argv[1]))\n"
)


def watch(output: Path, window: float, horizon: float) -> float | None:
    """Seconds until the stall rule fires on ``output``'s growth, or None within horizon."""
    started = time.monotonic()
    clock, size = StallClock(started, window), 0
    while time.monotonic() - started < horizon:
        now = time.monotonic()
        grown = output.stat().st_size
        if grown > size:
            clock.progress(now)
            size = grown
        if clock.stalled(now):
            return now - started
        time.sleep(OBSERVATION_PERIOD / 5)
    return None


def owned(code, output, *args):
    with output.open("w") as stream:
        proc, job = spawn_server(
            [sys.executable, "-u", "-c", code, *args],
            cwd=Path.cwd(),
            stdout=stream,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    if job is None:
        raise SystemExit("native Windows job ownership is required")
    return proc, job


def stop(proc, job) -> tuple[bool, float]:
    tree = [proc.pid] + [
        c.pid for c in psutil.Process(proc.pid).children(recursive=True)
    ]
    stop_start = time.monotonic()
    job.close()
    while any(psutil.pid_exists(p) and psutil.Process(p).is_running() for p in tree):
        if time.monotonic() - stop_start > CLEANUP_S:
            break
        time.sleep(0.05)
    return not any(psutil.pid_exists(p) for p in tree), time.monotonic() - stop_start


def main():
    # Synthetic, deliberately fast rates keep the check short; the rule under test is the same.
    cal = Calibration(
        prefill_tps=512.0, decode_tps=64.0, overhead_s=0.05, load_s=1.0, cli_start_s=0.5
    )
    params = TimeParams(stall_multiple=4.0)
    window = stall_window("decode", cal, params, OBSERVATION_PERIOD)
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(3600)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    with tempfile.TemporaryDirectory() as tmp:
        chatty_out, silent_out = Path(tmp) / "chatty.log", Path(tmp) / "silent.log"
        chatty = owned(CHATTY, chatty_out, str(window / 4))
        chatty_stalled = watch(chatty_out, window, 3 * window)
        stop(*chatty)
        silent = owned(SILENT_TREE, silent_out)
        time.sleep(1)
        tree = 1 + len(psutil.Process(silent[0].pid).children(recursive=True))
        silent_stalled = watch(silent_out, window, 3 * window)
        tree_gone, cleanup = stop(*silent)
    sentinel_alive = sentinel.poll() is None
    sentinel.kill()
    result = {
        "stall_window_s": window,
        "chatty_survived_s": None if chatty_stalled else round(3 * window, 3),
        "silent_stalled_after_s": None
        if silent_stalled is None
        else round(silent_stalled, 3),
        "owned_tree": tree,
        "tree_gone": tree_gone,
        "cleanup_s": round(cleanup, 3),
        "sentinel_alive": sentinel_alive,
        "passed": chatty_stalled is None
        and silent_stalled is not None
        and silent_stalled >= window
        and tree_gone
        and cleanup <= CLEANUP_S
        and sentinel_alive,
    }
    print(json.dumps(result))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
