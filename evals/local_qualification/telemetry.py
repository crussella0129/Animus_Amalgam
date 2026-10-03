"""Out-of-process probes so a stalled GPU query cannot block the owner."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil
import win32pdh


def publish(pending: Path, destination: Path) -> bool:
    """Replace the sample; False when the supervisor held it open for the whole try.

    Windows refuses to replace a file another process has open, and the supervisor opens
    this one four times a second. A skipped sample is bounded by the supervisor's
    staleness rule; dying here would stop the attempt (attempt 07).
    """
    deadline = time.monotonic() + 0.5
    while True:
        try:
            os.replace(pending, destination)
            return True
        except PermissionError:
            if time.monotonic() > deadline:
                return False
            time.sleep(0.01)


def main():
    destination = Path(sys.argv[1])
    query = win32pdh.OpenQuery()
    counter = win32pdh.AddEnglishCounter(query, r"\Memory\Pages Input/sec")
    output_counter = win32pdh.AddEnglishCounter(query, r"\Memory\Pages Output/sec")
    win32pdh.CollectQueryData(query)
    try:
        while True:
            time.sleep(1)
            win32pdh.CollectQueryData(query)
            _, pages = win32pdh.GetFormattedCounterValue(
                counter, win32pdh.PDH_FMT_DOUBLE
            )
            _, pages_out = win32pdh.GetFormattedCounterValue(
                output_counter, win32pdh.PDH_FMT_DOUBLE
            )
            gpu = (
                subprocess
                .check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.free,memory.used,utilization.gpu,temperature.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    text=True,
                    timeout=2,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                .strip()
                .splitlines()
            )
            if len(gpu) != 1:
                raise RuntimeError("This pilot requires one explicitly identified GPU")
            free, used, utilization, temperature = map(int, gpu[0].split(","))
            sample = {
                "at": time.monotonic(),
                "ram_available": psutil.virtual_memory().available,
                "vram_free": free << 20,
                "vram_used": used << 20,
                "gpu_utilization": utilization,
                "gpu_temperature": temperature,
                "hard_page_in_bytes_per_second": pages * 4096,
                "page_out_bytes_per_second": pages_out * 4096,
            }
            pending = destination.with_suffix(".tmp")
            pending.write_text(json.dumps(sample), encoding="utf-8")
            publish(pending, destination)
    finally:
        win32pdh.CloseQuery(query)


if __name__ == "__main__":
    main()
