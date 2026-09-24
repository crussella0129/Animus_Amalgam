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
from policy import (
    PagingGuard,
    admission_requirements,
    admitted,
    identity_mismatch,
    reserve_breached,
    server_identity_mismatch,
)
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
        else {
            "started": None,
            "launches": 0,
            "requests": 0,
            "attempts": 0,
            "charged_seconds": 0,
        }
    )
    attempt_start = time.monotonic()
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
        if ledger["requests"] >= manifest["limits"]["max_requests"]:
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
    paging = PagingGuard(manifest["limits"])
    loaded = threading.Event()
    load_start = None
    previous_tick = time.monotonic()
    reason = "unfinished"
    server = None
    driver = None
    port = None
    interrupt_file = attempt / "INTERRUPT"
    try:
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5, cwd=HERE.parents[1]
        ).strip()
        artifact_sha256 = {}
        for artifact, key in (("model", "model"), ("backend", "server")):
            with Path(paths[key]).open("rb") as stream:
                artifact_sha256[artifact] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
        mismatch = identity_mismatch(manifest, source_commit, artifact_sha256)
        if mismatch:
            raise RuntimeError(mismatch)
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
            nonlocal previous_tick, last_sample
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
            if reserve_breached(available, sample["vram_free"], manifest["limits"]):
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
                stop = paging.observe(sample, available, load_allowance)
                last_sample = sample["at"]
                record(
                    "sample",
                    load_page_in_allowance=load_allowance,
                    ram_pressure=available < paging.pressure_below,
                    **sample,
                )
                if stop:
                    raise RuntimeError(stop)
            if (
                ledger["charged_seconds"] + now - attempt_start
                > manifest["limits"]["total_seconds"]
            ):
                raise RuntimeError("aggregate live time budget exhausted")
            return sample

        sample = None
        while time.monotonic() - collector_start < 10:
            sample = observe()
            time.sleep(0.25)
        placement = manifest["placement"]
        cpu_needed, gpu_needed = admission_requirements(placement, manifest["limits"])
        record("admission", cpu_needed=cpu_needed, gpu_needed=gpu_needed, sample=sample)
        if not admitted(sample, placement, manifest["limits"]):
            reason = "not-run: resource gate"
            return
        if ledger["launches"] >= manifest["limits"]["max_launches"]:
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
        wire = Wire(
            f"http://127.0.0.1:{port}",
            token,
            record,
            consume_request,
            manifest["limits"]["input_tokens"],
        )
        load_error = []

        def readiness():
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                try:
                    props = wire.backend("/props")
                    mismatch = server_identity_mismatch(
                        props,
                        paths["model"],
                        manifest["limits"]["context"],
                        lambda a, b: Path(a).resolve() == Path(b).resolve(),
                    )
                    if mismatch:
                        load_error.append(mismatch)
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
        ledger["charged_seconds"] += time.monotonic() - attempt_start
        write_json(ledger_path, ledger)
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
