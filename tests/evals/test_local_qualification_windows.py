"""Native-Windows file behaviour the lab depends on (Sprint 3 T-214 regressions).

Windows refuses to open a file that is being replaced, and to replace a file another
process holds open. The supervisor reads the telemetry sample four times a second while
telemetry.py replaces it once a second: attempt 05 died on the read side and attempt 07 on
the write side. Text-mode writes on Windows also turn LF into CRLF, which changed the
task-corpus digest and published receipts.
"""

import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import threading
import time

import pytest

LAB_DIR = Path(__file__).resolve().parents[2] / "evals" / "local_qualification"
sys.path.insert(0, str(LAB_DIR))


def _exclusive_handle(path: Path):
    """A handle that shares nothing, as a file mid-replace behaves to a reader."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    handle = kernel32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value, ctypes.get_last_error()
    return kernel32, handle


@pytest.mark.windows_only
def test_refused_telemetry_read_keeps_the_last_sample(tmp_path):
    import run

    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({"at": 2.0}), encoding="utf-8")
    assert run.read_sample(sample, None) == {"at": 2.0}
    kernel32, handle = _exclusive_handle(sample)
    try:
        assert run.read_sample(sample, {"at": 1.0}) == {"at": 1.0}
    finally:
        kernel32.CloseHandle(handle)


@pytest.mark.windows_only
def test_telemetry_publish_survives_a_held_destination(tmp_path):
    import telemetry

    destination = tmp_path / "sample.json"
    destination.write_text("{}", encoding="utf-8")
    pending = tmp_path / "sample.tmp"
    pending.write_text(json.dumps({"at": 1.0}), encoding="utf-8")
    held = destination.open(encoding="utf-8")  # the supervisor mid-read
    threading.Timer(0.2, held.close).start()
    # A generous injected bound: the reader lets go after 0.2 s.
    assert telemetry.publish(pending, destination, retry_s=5.0)
    assert json.loads(destination.read_text(encoding="utf-8")) == {"at": 1.0}

    pending.write_text(json.dumps({"at": 2.0}), encoding="utf-8")
    with destination.open(encoding="utf-8"):
        started = time.monotonic()
        assert not telemetry.publish(pending, destination, retry_s=0.3)  # skipped
        assert time.monotonic() - started < 2.0


@pytest.mark.windows_only
def test_lab_writers_emit_lf(tmp_path, monkeypatch):
    import publish

    lab = tmp_path / "lab"
    attempt = lab / "attempts" / "attempt-01-x"
    attempt.mkdir(parents=True)
    (attempt / "events.jsonl").write_text("", encoding="utf-8")
    (attempt / "outcome.json").write_text(
        json.dumps({"reason": "ok"}), encoding="utf-8"
    )
    (attempt / "manifest.json").write_text(
        json.dumps({"id": "abc", "plan": "x"}), encoding="utf-8"
    )
    (lab / "paths.json").write_text(
        json.dumps({"task_venv": str(tmp_path / "venv")}), encoding="utf-8"
    )
    out = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["publish.py", "--lab", str(lab), "--attempt", attempt.name, "--out", str(out)],
    )
    publish.main()
    for written in out.rglob("*.json"):
        assert b"\r\n" not in written.read_bytes(), written.name
