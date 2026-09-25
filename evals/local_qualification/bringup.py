"""Pre-live stop-control check (T-221 T5): no model is loaded.

A synthetic child (with a grandchild) emits no progress under the owned Job Object. The
host-calibrated stall rule, driven by explicit synthetic rates, must fire; the owned tree must be
gone within INT-0004 AC2's cleanup bound; an unrelated sentinel must survive.
"""

import json
from pathlib import Path
import subprocess
import sys
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
    proc, job = spawn_server(
        [sys.executable, "-c", SILENT_TREE],
        cwd=Path.cwd(),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if job is None:
        raise SystemExit("native Windows job ownership is required")
    time.sleep(1)
    tree = [proc.pid] + [
        c.pid for c in psutil.Process(proc.pid).children(recursive=True)
    ]
    started = time.monotonic()
    clock = StallClock(started, window)
    while not clock.stalled(time.monotonic()):
        time.sleep(OBSERVATION_PERIOD / 5)
    stalled_after = time.monotonic() - started
    stop_start = time.monotonic()
    job.close()
    while any(psutil.pid_exists(p) and psutil.Process(p).is_running() for p in tree):
        if time.monotonic() - stop_start > CLEANUP_S:
            break
        time.sleep(0.05)
    cleanup = time.monotonic() - stop_start
    tree_gone = not any(psutil.pid_exists(p) for p in tree)
    sentinel_alive = sentinel.poll() is None
    sentinel.kill()
    result = {
        "stall_window_s": window,
        "stalled_after_s": round(stalled_after, 3),
        "owned_tree": len(tree),
        "tree_gone": tree_gone,
        "cleanup_s": round(cleanup, 3),
        "sentinel_alive": sentinel_alive,
        "passed": tree_gone
        and cleanup <= CLEANUP_S
        and sentinel_alive
        and stalled_after >= window,
    }
    print(json.dumps(result))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
