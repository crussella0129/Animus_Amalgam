"""Own one real Hermes operation, its backend and the independent stop loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import threading
import time

import psutil

from hermes_cli.local_runtime.processes import spawn_server
from wire import Wire

HERE = Path(__file__).resolve().parent


def write_json(path, value):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(pending, path)


def child_environment(lab):
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATH",
        "TEMP",
        "TMP",
        "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS",
        "PROGRAMFILES",
    }
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(
        HERMES_HOME=str(lab / "home"),
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(HERE.parents[1]),
        USERPROFILE=str(lab / "home"),
        APPDATA=str(lab / "home" / "appdata"),
        LOCALAPPDATA=str(lab / "home" / "local"),
    )
    return env


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=[
            "smoke",
            "operate",
            "workflow",
            "exercise",
            "main-cancel",
            "aux-cancel",
        ],
        required=True,
    )
    args = parser.parse_args()
    lab = args.lab.resolve()
    manifest = json.loads((lab / "manifest.json").read_text())
    paths = json.loads((lab / "paths.json").read_text())
    ledger_path = lab / "budget.json"
    ledger = (
        json.loads(ledger_path.read_text())
        if ledger_path.exists()
        else {"started": None, "launches": 0, "requests": 0, "attempts": 0}
    )
    ledger["attempts"] += 1
    attempt = lab / "receipts" / f"attempt-{ledger['attempts']:02d}-{args.mode}"
    attempt.mkdir()
    write_json(attempt / "manifest.json", manifest)
    write_json(ledger_path, ledger)
    events = (attempt / "events.jsonl").open("w", encoding="utf-8")
    event_lock = threading.Lock()

    def record(kind, **data):
        with event_lock:
            events.write(
                json.dumps({
                    "at": time.monotonic(),
                    "kind": kind,
                    "manifest_id": manifest["id"],
                    **data,
                })
                + "\n"
            )
            events.flush()

    def consume_request():
        if ledger["requests"] >= 18:
            raise RuntimeError("aggregate request budget exhausted")
        ledger["requests"] += 1
        write_json(ledger_path, ledger)
        return ledger["requests"]

    env = child_environment(lab)
    owned, streams = [], []

    def spawn(command, name):
        output = (attempt / f"{name}.log").open("w", encoding="utf-8")
        streams.append(output)
        proc, job = spawn_server(
            command,
            cwd=lab / "fixture",
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if job is None:
            raise RuntimeError(
                "This operational pilot requires native Windows job ownership"
            )
        owned.append((proc, job))
        record("owned_process", role=name, pid=proc.pid)
        return proc

    sample_path = attempt / "sample.json"
    wire = None
    last_sample = None
    paging_streak = 0
    page_out_streak = 0
    loaded = threading.Event()
    load_start = None
    previous_tick = time.monotonic()
    reason = "unfinished"
    server = None
    driver = None
    port = None
    interrupt_file = attempt / "INTERRUPT"
    try:
        identity = {k: v for k, v in manifest.items() if k != "id"}
        actual_digest = hashlib.sha256(
            json.dumps(
                identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()
        if actual_digest != manifest["id"]:
            raise RuntimeError("candidate manifest digest mismatch")
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5, cwd=HERE.parents[1]
        ).strip()
        if manifest["source_dirty"] or source_commit != manifest["source_commit"]:
            raise RuntimeError("source revision differs from frozen candidate")
        for artifact in ("model", "backend"):
            artifact_path = Path(paths["model" if artifact == "model" else "server"])
            with artifact_path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != manifest[artifact]["sha256"]:
                raise RuntimeError(f"{artifact} artifact differs from frozen candidate")
        record(
            "identity_verified",
            file_cache_state="uncontrolled; artifact verification reads model bytes",
        )
        previous_tick = time.monotonic()
        collector = spawn(
            [sys.executable, "-B", str(HERE / "telemetry.py"), str(sample_path)],
            "telemetry",
        )
        collector_start = time.monotonic()

        def observe():
            nonlocal previous_tick, last_sample, paging_streak, page_out_streak
            now = time.monotonic()
            if (lab / "STOP").exists():
                raise RuntimeError("operator STOP requested")
            if now - previous_tick > 2:
                raise RuntimeError("supervisor scheduler lag exceeded two seconds")
            previous_tick = now
            if collector.poll() is not None:
                raise RuntimeError("critical telemetry process exited")
            if not sample_path.exists():
                if now - collector_start > 3:
                    raise RuntimeError(
                        "critical telemetry startup exceeded three seconds"
                    )
                return None
            sample = json.loads(sample_path.read_text())
            if now - sample["at"] > 3:
                raise RuntimeError("critical telemetry stale")
            available = psutil.virtual_memory().available
            if available < 4 << 30 or sample["vram_free"] < 1 << 30:
                record(
                    "reserve_breach",
                    current_ram_available=available,
                    latest_sample=sample,
                )
                raise RuntimeError("RAM or VRAM reserve breached")
            if sample["at"] != last_sample:
                load_allowance = (
                    load_start is not None
                    and not loaded.is_set()
                    and now - load_start
                    < manifest["limits"]["load_page_in_allowance_seconds"]
                )
                paging_streak = (
                    paging_streak + 1
                    if not load_allowance
                    and sample["hard_page_in_bytes_per_second"] > 64 << 20
                    else 0
                )
                page_out_streak = (
                    page_out_streak + 1
                    if sample["page_out_bytes_per_second"] > 64 << 20
                    else 0
                )
                last_sample = sample["at"]
                record("sample", load_page_in_allowance=load_allowance, **sample)
                if paging_streak >= 3:
                    raise RuntimeError("hard page-in rate breached")
                if page_out_streak >= 3:
                    raise RuntimeError("page-out rate breached")
            if (
                ledger["started"] is not None
                and now - ledger["started"] - ledger.get("idle_approval_seconds", 0)
                > 3600
            ):
                raise RuntimeError("aggregate live time budget exhausted")
            return sample

        sample = None
        while time.monotonic() - collector_start < 10:
            sample = observe()
            time.sleep(0.25)
        placement = manifest["placement"]
        cpu_needed = (
            placement["cpu_weight_bytes"] + placement["cpu_overhead_bytes"] + (4 << 30)
        )
        gpu_needed = (
            placement["gpu_weight_bytes"]
            + placement["context_bytes_upper"]
            + placement["gpu_overhead_bytes"]
            + (1 << 30)
        )
        record("admission", cpu_needed=cpu_needed, gpu_needed=gpu_needed, sample=sample)
        if (
            sample is None
            or sample["ram_available"] < cpu_needed
            or sample["vram_free"] < gpu_needed
        ):
            reason = "not-run: resource gate"
            return
        if ledger["launches"] >= 6:
            raise RuntimeError("aggregate launch budget exhausted")
        ledger["launches"] += 1
        if ledger["started"] is None:
            ledger["started"] = time.monotonic()
        write_json(ledger_path, ledger)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        token = secrets.token_hex(24)
        token_file = attempt / "backend.key"
        token_file.write_text(token)
        command = [
            paths["server"],
            "-m",
            paths["model"],
            "--alias",
            "amalgam-pilot",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--api-key-file",
            str(token_file),
            "--offline",
            "--ctx-size",
            "8192",
            "--parallel",
            "1",
            "--fit",
            "off",
            "--load-mode",
            "none",
            "--no-context-shift",
            "--no-warmup",
            "--spec-type",
            "none",
            "-ngl",
            "all",
            "-ot",
            placement["cpu_pattern"] + "=CPU",
            "-ctk",
            "q8_0",
            "-ctv",
            "q8_0",
            "-fa",
            "on",
            "-b",
            "256",
            "-ub",
            "128",
            "-t",
            "6",
            "--cache-ram",
            "0",
            "--ctx-checkpoints",
            "0",
            "--predict",
            "128",
            "--temp",
            "0",
            "--top-p",
            "1",
            "--seed",
            "42",
            "--chat-template-kwargs",
            '{"enable_thinking":false}',
            "--metrics",
        ]
        record("launch", command=command, python=sys.version)
        load_start = time.monotonic()
        server = spawn(command, "backend")
        wire = Wire(f"http://127.0.0.1:{port}", token, record, consume_request)
        load_error = []

        def readiness():
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                try:
                    props = wire.backend("/props")
                    if (
                        props["total_slots"] != 1
                        or props["default_generation_settings"]["n_ctx"] != 8192
                    ):
                        load_error.append("server context/slot identity mismatch")
                    if (
                        Path(props["model_path"]).resolve()
                        != Path(paths["model"]).resolve()
                    ):
                        load_error.append("server model path mismatch")
                    record("server_props", props=props)
                    loaded.set()
                    return
                except (OSError, KeyError, ValueError):
                    time.sleep(0.5)

        threading.Thread(target=readiness, daemon=True).start()
        while not loaded.is_set():
            observe()
            if server.poll() is not None:
                raise RuntimeError(f"backend exited during load: {server.returncode}")
            if time.monotonic() - load_start > 300:
                raise RuntimeError("load deadline exceeded")
            time.sleep(0.25)
        if load_error:
            raise RuntimeError(load_error[0])
        print("Backend ready; starting actual Hermes CLI", flush=True)
        config_path = lab / "home" / "config.yaml"
        config = json.loads(config_path.read_text())
        config["model"]["base_url"] = wire.url
        config["auxiliary"]["compression"]["base_url"] = wire.url
        config["auxiliary"]["compression"]["api_key"] = "local-pilot"
        write_json(config_path, config)
        driver = spawn(
            [
                sys.executable,
                "-B",
                str(HERE / "driver.py"),
                "--lab",
                str(lab),
                "--url",
                wire.url,
                "--mode",
                args.mode,
                "--result",
                str(attempt / "result.json"),
                "--interrupt-file",
                str(interrupt_file),
            ],
            "cli",
        )
        driver_start = time.monotonic()
        while driver.poll() is None:
            observe()
            if wire.failure:
                raise RuntimeError(wire.failure)
            if server.poll() is not None:
                raise RuntimeError("backend exited during CLI operation")
            if wire.active is not None:
                elapsed = time.monotonic() - wire.active["started"]
                if elapsed > 300:
                    raise RuntimeError("request deadline exceeded")
                stage_path = attempt / "stage.json"
                active_mode = (
                    json.loads(stage_path.read_text())["mode"]
                    if args.mode == "exercise" and stage_path.exists()
                    else args.mode
                )
                if active_mode.endswith("cancel") and elapsed > 5:
                    slots = wire.backend("/slots")
                    record("cancel_trigger", slots=slots, request=wire.active)
                    if not any(slot.get("is_processing") for slot in slots):
                        raise RuntimeError(
                            "cancellation inconclusive: no active backend slot"
                        )
                    reason = "deliberate cancellation"
                    break
            elif time.monotonic() - driver_start > 300:
                raise RuntimeError("CLI operation stalled outside an inference request")
            time.sleep(0.25)
        if reason == "unfinished":
            reason = f"CLI exited: {driver.returncode}"
            if args.mode.endswith("cancel") or args.mode == "exercise":
                reason = "cancellation inconclusive: CLI ended before active trigger"
    except (Exception, KeyboardInterrupt) as exc:
        reason = f"stopped: {type(exc).__name__}: {exc}"
    finally:
        stop_start = time.monotonic()
        if driver is not None and driver.poll() is None:
            interrupt_file.touch()
            record("graceful_interrupt", grace_seconds=2)
            while driver.poll() is None and time.monotonic() - stop_start < 2:
                # A resource emergency can shorten grace, never delay the hard stop.
                if psutil.virtual_memory().available < 4 << 30:
                    break
                time.sleep(0.1)
        # The owned job is the external hard stop; no provider callback is needed.
        for proc, job in reversed(owned):
            job.close()
        for proc, _job in reversed(owned):
            try:
                proc.wait(timeout=max(0.1, 5 - (time.monotonic() - stop_start)))
            except subprocess.TimeoutExpired:
                record(
                    "cleanup_failure",
                    pid=proc.pid,
                    error="process wait deadline exceeded",
                )
        record(
            "cleanup",
            seconds=time.monotonic() - stop_start,
            processes=[{"pid": p.pid, "exit": p.returncode} for p, _j in owned],
        )
        if wire is not None:
            try:
                wire.close()
            except RuntimeError as exc:
                record("cleanup_failure", error=str(exc))
        listener_closed = True
        if port is not None:
            with socket.socket() as probe:
                probe.settimeout(0.2)
                listener_closed = probe.connect_ex(("127.0.0.1", port)) != 0
        record("listener_cleanup", backend_listener_closed=listener_closed)
        write_json(
            attempt / "outcome.json",
            {
                "reason": reason,
                "manifest_id": manifest["id"],
                "budget": ledger,
                "cleanup_seconds": time.monotonic() - stop_start,
                "backend_listener_closed": listener_closed,
            },
        )
        events.close()
        for stream in streams:
            stream.close()
        print(
            json.dumps({"attempt": attempt.name, "reason": reason, "budget": ledger}),
            flush=True,
        )


if __name__ == "__main__":
    main()
