"""Own one lab attempt: its backend, its fresh sessions and the host-calibrated stop loop.

Every time rule comes from ``hermes_cli.local_runtime.throughput`` and the host's calibration
record. The only fixed periods are observation cadences (telemetry, supervisor loop, slot poll)
and INT-0004's OS-level kill safety (grace and cleanup), none of which is token work.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time

import psutil

from hermes_cli.local_runtime.processes import spawn_server
from hermes_cli.local_runtime.throughput import (
    Calibration,
    RateTracker,
    StallClock,
    TimeParams,
    gap_window,
    load_backstop,
    predict_seconds,
    request_backstop,
    sprint_budget,
    stall_window,
    step_stop,
    uncalibrated_stall_window,
)
from policy import (
    ac1_request_coverage,
    PagingGuard,
    admission_requirements,
    admitted,
    budget_exceeded,
    identity_mismatch,
    launch_allowed,
    load_progressed,
    request_allowed,
    reserve_breached,
    server_identity_mismatch,
    supervisor_lagged,
    telemetry_stale,
)
import verify_long
from wire import Wire

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TASKS = HERE / "tasks"
TELEMETRY_PERIOD = 1.0  # telemetry.py cadence (retained: observation, not token work)
LOOP_PERIOD = 0.25  # supervisor loop (retained)
OBSERVATION_PERIOD = 0.5  # /slots poll (retained)
BASELINE_SAMPLES = 10  # telemetry samples before admission (retained)
GRACE_S, CLEANUP_S = 2, 5  # INT-0004 AC2 OS-level kill safety (retained)
MAX_CHECKPOINTS = 32
VERIFY_S = 120  # hidden-verifier process bound (retained: OS safety, not token work)
ARMS = json.loads((HERE / "arms.json").read_text(encoding="utf-8"))
ENV_ALLOWED = {
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATH",
    "TEMP",
    "TMP",
    "SYSTEMDRIVE",
    "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMDATA",
}
CHECKPOINT_LINE = re.compile(r"created context checkpoint .*?size = ([0-9.]+) MiB")


def write_json(path, value):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(pending, path)


def inside_repo(path: Path) -> bool:
    resolved = path.resolve()
    return resolved == REPO or REPO in resolved.parents


def session_env(home: Path, venv: Path) -> dict:
    """No repository path reaches the CLI or its tools; the task venv comes first."""
    env = {k: v for k, v in os.environ.items() if k.upper() in ENV_ALLOWED}
    scripts = venv / ("Scripts" if os.name == "nt" else "bin")
    outside = [
        entry
        for entry in env.get("PATH", "").split(os.pathsep)
        if entry and not inside_repo(Path(entry))
    ]
    env["PATH"] = os.pathsep.join([str(scripts), *outside])
    # A private TEMP: Git Bash mounts /tmp on it, and the owner's TEMP would carry files
    # from one session into the next.
    temp = home / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    env.update(
        TEMP=str(temp),
        TMP=str(temp),
        HERMES_HOME=str(home),
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        USERPROFILE=str(home),
        APPDATA=str(home / "appdata"),
        LOCALAPPDATA=str(home / "local"),
    )
    return env


def session_config(url, context, echo, timer, fixture) -> dict:
    return {
        "model": {
            "default": "amalgam-pilot",
            "provider": "custom",
            "base_url": url,
            "context_length": context,
            "reasoning_echo": echo,
        },
        "providers": {
            "custom": {"request_timeout_seconds": timer, "stale_timeout_seconds": timer}
        },
        "agent": {
            "environment_probe": False,
            "local_stream_stale_timeout": timer,
            "turn_liveness": {"timeout_s": timer},
        },
        "local_runtime": {"enabled": False},
        "compression": {"enabled": False},
        "fallback_models": [],
        "display": {"streaming": True},
        "terminal": {"backend": "local", "cwd": str(fixture)},
        "tools": {"tool_search": {"enabled": "off"}},
        "auxiliary": {
            "title_generation": {"enabled": False},
            "compression": {
                "provider": "custom",
                "model": "amalgam-pilot",
                "base_url": url,
                "api_key": "local-pilot",
            },
        },
    }


def fresh_session(attempt: Path, workload: str) -> tuple[Path, Path, Path]:
    """Fresh state at the same paths every session: Hermes renders its home and working
    directory into the system prompt, so per-session paths would make two identical
    sessions' prefixes differ (C3). Each session is archived when it ends."""
    root = attempt / "live"
    home, fixture = root / "home", root / "fixture"
    home.mkdir(parents=True)
    task = workload.partition(":")[0]
    template = TASKS / task / "fixture"
    if workload.startswith("long") and template.is_dir():
        shutil.copytree(template, fixture)
    else:
        fixture.mkdir()
    return root, home, fixture


class KernelCache:
    """The backend's CUDA JIT cache, kept per lab rather than per attempt.

    On a cold cache the driver compiles kernels on first use: one CPU core busy, the GPU
    idle and no progress event for tens of seconds at load and again in the first request
    (measured 2026-10-03: load 48.6 s vs 18.2 s warm, prefill 15.6 vs 115 tok/s). The cache
    growing is the only visible sign of that work, and a request that grew it is not a rate
    sample. Driver state, not agent state, so a fresh attempt does not reset it.
    """

    def __init__(self, path: Path):
        self.path = path
        path.mkdir(exist_ok=True)
        self.last = self.bytes()

    def bytes(self) -> int:
        total = 0
        for item in self.path.rglob("*"):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except OSError:
                pass  # the driver renames entries while writing them
        return total

    def grew(self) -> bool:
        now = self.bytes()
        grew, self.last = now > self.last, now
        return grew

    def env(self, base: dict) -> dict:
        # 4 GiB is the driver's maximum: never evict compiled kernels mid-sprint.
        return {
            **base,
            "CUDA_CACHE_PATH": str(self.path),
            "CUDA_CACHE_MAXSIZE": "4294967296",
        }


def read_sample(path: Path, last: dict | None) -> dict | None:
    """The latest telemetry sample, or ``last`` while Windows refuses the open.

    Windows refuses to open a file mid-``os.replace``; the staleness rule bounds how long
    a kept sample may last (attempt 05 stopped on this race).
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except PermissionError:
        return last


def tree_cpu(proc) -> float:
    try:
        procs = [psutil.Process(proc.pid)]
        procs += procs[0].children(recursive=True)
    except psutil.Error:
        return 0.0
    total = 0.0
    for p in procs:
        try:
            times = p.cpu_times()
            total += times.user + times.system
        except psutil.Error:
            pass
    return total


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    lab = args.lab.resolve()
    if inside_repo(lab):
        raise SystemExit("the lab root must be outside the repository")
    manifest = json.loads(args.manifest.read_text())
    paths = json.loads((lab / "paths.json").read_text())
    params = TimeParams(**manifest["time_params"])
    record = manifest["calibration_record"]
    cal = Calibration(**record["rates"]) if record else None
    limits = manifest["limits"]
    ledger_path = lab / "budget.json"
    ledger = (
        json.loads(ledger_path.read_text())
        if ledger_path.exists()
        else {"launches": 0, "requests": 0, "attempts": 0, "charged_seconds": 0.0}
    )
    attempt_start = time.monotonic()
    ledger["attempts"] += 1
    attempt = lab / "attempts" / f"attempt-{ledger['attempts']:02d}-{manifest['plan']}"
    attempt.mkdir(parents=True)
    write_json(attempt / "manifest.json", manifest)
    write_json(ledger_path, ledger)
    events = (attempt / "events.jsonl").open("w", encoding="utf-8")
    event_lock = threading.Lock()

    def record_event(kind, **data):
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
        if not request_allowed(ledger["requests"], limits):
            raise RuntimeError("aggregate request budget exhausted")
        ledger["requests"] += 1
        write_json(ledger_path, ledger)
        return ledger["requests"]

    owned, streams = [], []

    def spawn(command, name, env, cwd):
        output = (attempt / f"{name}.log").open("w", encoding="utf-8")
        streams.append(output)
        proc, job = spawn_server(
            command,
            cwd=cwd,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if job is None:
            raise RuntimeError("This lab requires native Windows job ownership")
        owned.append((proc, job, name))
        record_event("owned_process", role=name, pid=proc.pid)
        return proc

    base_env = session_env(attempt / "owner-home", Path(paths["task_venv"]))
    kernel = KernelCache(lab / "kernel-cache")
    sample_path = attempt / "sample.json"
    state = {"last_sample": None, "previous_tick": time.monotonic(), "max_lag": 0.0}
    paging = PagingGuard(limits)
    wire = server = driver = port = None
    reason = "unfinished"
    session_outcomes = []
    t_load = None
    interrupt_file = None
    try:
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10, cwd=REPO
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, timeout=10, cwd=REPO
            ).strip()
        )
        hash_start = time.monotonic()
        artifact_sha256 = {}
        for artifact, key in (("model", "model"), ("backend", "server")):
            with Path(paths[key]).open("rb") as stream:
                artifact_sha256[artifact] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
        hash_s = time.monotonic() - hash_start
        mismatch = identity_mismatch(manifest, source_commit, artifact_sha256, dirty)
        if mismatch:
            raise RuntimeError(mismatch)
        record_event("identity_verified", hash_seconds=hash_s)
        collector = spawn(
            [sys.executable, "-B", str(HERE / "telemetry.py"), str(sample_path)],
            "telemetry",
            base_env,
            attempt,
        )
        collector_start = time.monotonic()
        state["previous_tick"] = time.monotonic()

        def observe(loading=False):
            """Check every guard; returns (latest sample, previous distinct sample)."""
            now = time.monotonic()
            if (lab / "STOP").exists():
                raise RuntimeError("operator STOP requested")
            lag = now - state["previous_tick"]
            state["max_lag"] = max(state["max_lag"], lag)
            if supervisor_lagged(state["previous_tick"], now, TELEMETRY_PERIOD):
                raise RuntimeError(
                    "supervisor scheduler lag exceeded two telemetry periods"
                )
            state["previous_tick"] = now
            if collector.poll() is not None:
                raise RuntimeError("critical telemetry process exited")
            if not sample_path.exists():
                if telemetry_stale(collector_start, now, TELEMETRY_PERIOD):
                    raise RuntimeError("critical telemetry did not start")
                return None, None
            sample = read_sample(sample_path, state["last_sample"])
            if sample is None:
                return None, None
            if telemetry_stale(sample["at"], now, TELEMETRY_PERIOD):
                raise RuntimeError("critical telemetry stale")
            available = psutil.virtual_memory().available
            if reserve_breached(available, sample["vram_free"], limits):
                record_event(
                    "reserve_breach",
                    current_ram_available=available,
                    latest_sample=sample,
                )
                raise RuntimeError("RAM or VRAM reserve breached")
            if sample["at"] != (state["last_sample"] or {}).get("at"):
                # During load, page-in is the model being read; page-out still counts.
                stop = paging.observe(sample, available, loading)
                record_event(
                    "sample", ram_pressure=available < paging.pressure_below, **sample
                )
                if stop:
                    raise RuntimeError(stop)
                state["previous_sample"], state["last_sample"] = (
                    state["last_sample"],
                    sample,
                )
                state["samples"] = state.get("samples", 0) + 1
            charged = ledger["charged_seconds"] + now - attempt_start
            if budget_exceeded(charged, (record or {}).get("sprint_budget_s")):
                raise RuntimeError(
                    "host-derived sprint budget exceeded: stop and report"
                )
            return sample, state.get("previous_sample")

        sample = None
        while state.get("samples", 0) < BASELINE_SAMPLES:
            sample, _ = observe()
            time.sleep(LOOP_PERIOD)
        placement = manifest["placement"]
        cpu_needed, gpu_needed = admission_requirements(placement, limits)
        record_event(
            "admission", cpu_needed=cpu_needed, gpu_needed=gpu_needed, sample=sample
        )
        if not admitted(sample, placement, limits):
            reason = "not-run: resource gate"
            return
        if not launch_allowed(ledger["launches"], limits):
            raise RuntimeError("aggregate launch budget exhausted")
        ledger["launches"] += 1
        write_json(ledger_path, ledger)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        token = secrets.token_hex(24)
        token_file = attempt / "backend.key"
        token_file.write_text(token)
        slot_dir = attempt / "slots"
        slot_dir.mkdir()
        command = [
            paths["server"],
            "-m",
            paths["model"],
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--api-key-file",
            str(token_file),
            "--slot-save-path",
            str(slot_dir),
            *manifest["launch"]["flags"],
        ]
        record_event(
            "launch",
            command=command,
            python=sys.version,
            kernel_cache_bytes=kernel.last,
        )
        load_start = time.monotonic()
        server = spawn(command, "backend", kernel.env(base_env), attempt)
        backend_log = attempt / "backend.log"
        ready = threading.Event()
        load_error = []

        def readiness():
            while not ready.is_set():
                try:
                    props = Wire.probe(
                        f"http://127.0.0.1:{port}",
                        token,
                        "/props",
                        probe_window(cal, params, None, OBSERVATION_PERIOD),
                    )
                    mismatch = server_identity_mismatch(
                        props,
                        paths["model"],
                        manifest["launch"]["context"],
                        lambda a, b: Path(a).resolve() == Path(b).resolve(),
                    )
                    if mismatch:
                        load_error.append(mismatch)
                    record_event("server_props", props=props)
                    ready.set()
                except (OSError, KeyError, ValueError):
                    time.sleep(OBSERVATION_PERIOD)

        threading.Thread(target=readiness, daemon=True).start()
        load_clock = StallClock(load_start, params.stall_multiple * TELEMETRY_PERIOD)
        log_size, seen_at = 0, None
        while not ready.is_set():
            sample, previous = observe(loading=True)
            now = time.monotonic()
            size = backend_log.stat().st_size if backend_log.exists() else 0
            if sample is not None and sample["at"] != seen_at:
                seen_at = sample["at"]
                if load_progressed(previous, sample, size > log_size or kernel.grew()):
                    load_clock.progress(now)
            log_size = size
            verdict = step_stop(
                load_start,
                load_clock.last_progress,
                now,
                load_clock.window,
                load_backstop(cal, params) if cal else None,
            )
            if verdict == "stall":
                raise RuntimeError("load stalled: no memory growth or log output")
            if verdict == "backstop":
                raise RuntimeError("host-derived load backstop exceeded")
            if server.poll() is not None:
                raise RuntimeError(f"backend exited during load: {server.returncode}")
            time.sleep(LOOP_PERIOD)
        if load_error:
            raise RuntimeError(load_error[0])
        t_load = time.monotonic() - load_start
        record_event("loaded", load_seconds=t_load, kernel_cache_bytes=kernel.bytes())
        rates = RateTracker(params, cal)
        predictor = (
            (
                lambda uncached, cap: predict_seconds(
                    uncached, cap, rates.prefill_tps, rates.decode_tps, cal.overhead_s
                )
            )
            if cal
            else None
        )
        wire = Wire(
            f"http://127.0.0.1:{port}",
            token,
            record_event,
            consume_request,
            probe_window(cal, params, t_load, OBSERVATION_PERIOD),
            OBSERVATION_PERIOD,
            predictor,
            kernel.bytes,
        )
        task_state = {"prechecked": False}
        queue, index = list(manifest["sessions"]), 0
        while queue:
            spec, index = queue.pop(0), index + 1
            outcome = run_session(index, spec, locals())
            session_outcomes.append(outcome)
            if outcome.get("attempt_stop"):
                raise RuntimeError(outcome["attempt_stop"])
            if (outcome.get("verification") or {}).get("contamination"):
                if spec.get("rerun_of") is None:
                    queue.insert(0, {**spec, "rerun_of": index})
                else:
                    outcome["contaminated_twice"] = True
                    record_event("contaminated_twice", session=index)
        reason = "sessions complete"
        if manifest["plan"] == "calibration":
            write_calibration(
                lab, attempt, hash_s, t_load, session_outcomes, params, record_event
            )
    except (Exception, KeyboardInterrupt) as exc:
        reason = f"stopped: {type(exc).__name__}: {exc}"
    finally:
        stop_start = time.monotonic()
        active = wire.active if wire is not None else None
        if active is not None:
            record_event(
                "request_stopped", **stopped_request(active, reason, stop_start)
            )
        live_driver = next(
            (p for p, _j, n in owned if n.startswith("cli") and p.poll() is None), None
        )
        if live_driver is not None and interrupt_file_holder.get("path"):
            interrupt_file_holder["path"].touch()
            record_event("graceful_interrupt", grace_seconds=GRACE_S)
            while (
                live_driver.poll() is None and time.monotonic() - stop_start < GRACE_S
            ):
                if psutil.virtual_memory().available < limits["ram_reserve_bytes"]:
                    break
                time.sleep(0.1)
        for _proc, job, _name in reversed(owned):
            job.close()
        for proc, _job, _name in reversed(owned):
            try:
                proc.wait(timeout=max(0.1, CLEANUP_S - (time.monotonic() - stop_start)))
            except subprocess.TimeoutExpired:
                record_event(
                    "cleanup_failure",
                    pid=proc.pid,
                    error="process wait deadline exceeded",
                )
        cleanup_seconds = time.monotonic() - stop_start
        # The tree is gone, so the cut-short session's fixture is final (L2).
        current = interrupt_file_holder.get("session")
        stopped = bounded(
            lambda: stopped_session(
                current, wire, Path(paths["task_venv"]), manifest["allowlist"]
            ),
            VERIFY_S,
        )
        if stopped:
            record_event("session_stopped", **stopped)
        elif current is not None:
            record_event(
                "session_stopped",
                session=current["index"],
                workload=current["workload"],
                verification={"error": "verifier did not finish"},
            )
        record_event(
            "cleanup",
            seconds=cleanup_seconds,
            processes=[
                {"pid": p.pid, "role": n, "exit": p.returncode} for p, _j, n in owned
            ],
        )
        if wire is not None:
            try:
                wire.close()
            except RuntimeError as exc:
                record_event("cleanup_failure", error=str(exc))
        listener_closed = True
        if port is not None:
            with socket.socket() as probe:
                probe.settimeout(0.2)
                listener_closed = probe.connect_ex(("127.0.0.1", port)) != 0
        record_event("listener_cleanup", backend_listener_closed=listener_closed)
        ledger["charged_seconds"] += time.monotonic() - attempt_start
        write_json(ledger_path, ledger)
        write_json(
            attempt / "outcome.json",
            {
                "reason": reason,
                "manifest_id": manifest["id"],
                "plan": manifest["plan"],
                "budget": ledger,
                "cleanup_seconds": cleanup_seconds,
                "backend_listener_closed": listener_closed,
                "load_seconds": t_load,
                "max_supervisor_lag_seconds": state["max_lag"],
                "sessions": session_outcomes,
            },
        )
        events.close()
        for stream in streams:
            stream.close()
        print(
            json.dumps({
                "attempt": attempt.name,
                "reason": reason,
                "launches": ledger["launches"],
                "requests": ledger["requests"],
                "charged_seconds": round(ledger["charged_seconds"], 1),
            }),
            flush=True,
        )


interrupt_file_holder: dict = {}


def probe_window(cal, params, t_load, period) -> float:
    """Timeout for a backend metadata probe (template, tokenize, slots, props).

    Calibrated: the pre-first-event stall window. Before calibration it is the attempt's
    own load time × k, and during the load itself the observation floor; like every
    other window, never under that floor.
    """
    if cal:
        return stall_window("pre_first_event", cal, params, period)
    return uncalibrated_stall_window(
        params.stall_multiple * (t_load or 0.0), params, period
    )


def stopped_request(active: dict, reason: str, now: float) -> dict:
    """The receipt for a request an attempt stop cut short: cause, elapsed time and the
    predictions it was sent with (INT-0007 AC7)."""
    return {
        "request_id": active["request_id"],
        "reason": reason,
        "seconds": now - active["started"],
        "meaningful_first_token_seconds": active["first_token"],
        "predicted_initial_seconds": active["predicted_initial"],
        "predicted_rearmed_seconds": active["predicted_rearmed"],
    }


def stop_active_request(wire, record_event, cause: str) -> None:
    """Stop the in-flight request: its receipt names the cause first, so the cancel
    record that follows is never read as a deliberate cancel (AC7, H2)."""
    active = wire.active
    if active is not None:
        record_event(
            "request_stopped", **stopped_request(active, cause, time.monotonic())
        )
    wire.cancel_active()


def stopped_session(current, wire, venv: Path, allowlist) -> dict | None:
    """L2's "being stopped" branch: score a session an attempt stop cut short, from
    its fixture state alone, once its process tree is gone.

    L4 screens the conversation the wire last forwarded, the session's history up to
    the stop. A scoring failure is recorded, never raised: the stop path must still
    charge the ledger and write the outcome.
    """
    if current is None:
        return None
    # The session may have ended at the wire already, if the stop came while it was
    # being verified; a session's own id tells it from the previous one.
    candidates = (wire.session, wire.ended) if wire is not None else ()
    session = next((s for s in candidates if s and s["id"] == current["index"]), None)
    conversation = (session or {}).get("last_messages") or []
    try:
        verification = verify_session(
            current["workload"],
            current["fixture"],
            {"conversation": conversation},
            venv,
            allowlist,
        )
    except Exception as exc:
        verification = {"error": f"{type(exc).__name__}: {exc}"}
    stopped = {
        "session": current["index"],
        "workload": current["workload"],
        "requests": session["requests"] if session else None,
        "tool_calls": None if session is None else session["tool_call_validity"],
        "verification": verification,
    }
    if session is not None and current["workload"] == "long:all":
        stopped["ac1_request_coverage"] = ac1_request_coverage(session["requests"])
    return stopped


def bounded(fn, seconds):
    """``fn()``'s result, or None if it is still running after ``seconds``."""
    box = {}
    worker = threading.Thread(target=lambda: box.update(value=fn()), daemon=True)
    worker.start()
    worker.join(seconds)
    return box.get("value")


def erases_slot(index: int, spec: dict) -> bool:
    """Every session after the first starts on an erased slot unless its plan keeps the
    slot to measure cross-session prefix reuse (C3; attempt 04 erased them all)."""
    return index > 1 and spec.get("erase_slot", True)


class RequestExtrema:
    """Resource extrema of the request in flight (L1).

    Recorded when the request changes and whenever the session loop exits, by any
    path: a guard stop raised inside ``observe()`` used to drop them.
    """

    FIELDS = (
        ("ram_available_min", "ram_available", min),
        ("vram_free_min", "vram_free", min),
        ("page_in_max", "hard_page_in_bytes_per_second", max),
        ("page_out_max", "page_out_bytes_per_second", max),
        ("gpu_temperature_max", "gpu_temperature", max),
    )

    def __init__(self, record_event):
        self.record_event = record_event
        self.request_id, self.values = None, {}

    def observe(self, request_id, sample) -> None:
        if request_id != self.request_id:
            self.close()
            self.request_id = request_id
        if request_id is not None and sample is not None:
            for key, field, pick in self.FIELDS:
                self.values[key] = pick(
                    self.values.get(key, sample[field]), sample[field]
                )

    def close(self) -> None:
        if self.request_id is not None:
            self.record_event(
                "request_resources", request_id=self.request_id, **self.values
            )
        self.request_id, self.values = None, {}


def session_windows(cal, params, t_load, context, output_cap, period) -> dict:
    """Every time window a session uses, from the throughput model alone (T1, T3).

    Calibrated: the host's floor rates set the stall windows and the request backstop,
    and its measured CLI start-up sets the gap window. During calibration itself, the
    attempt's own load time stands in for the unknown rates.
    """
    phases = ("pre_first_event", "prefill", "decode")
    if cal:
        backstop = request_backstop(cal, params, context, output_cap)
        stall = {phase: stall_window(phase, cal, params, period) for phase in phases}
        return {
            "stall": stall,
            "request_backstop": backstop,
            "gap": gap_window(cal, params, period),
            "settle": stall["prefill"],
            "hermes_timer": backstop,
            "probe": probe_window(cal, params, t_load, period),
        }
    window = uncalibrated_stall_window(t_load, params, period)
    return {
        "stall": dict.fromkeys(phases, window),
        "request_backstop": None,
        "gap": uncalibrated_stall_window(
            params.stall_multiple * t_load, params, period
        ),
        "settle": window,
        "hermes_timer": params.stall_multiple * t_load,
        "probe": probe_window(cal, params, t_load, period),
    }


def wait_while(busy, seconds, observe, period) -> bool:
    """Every supervisor wait keeps the guards running; True if busy() cleared in time.

    A wait that skipped ``observe()`` froze the guards and tripped the lag stop
    (attempt 02).
    """
    deadline = time.monotonic() + seconds
    while busy():
        if time.monotonic() > deadline:
            return False
        observe()
        time.sleep(period)
    return True


def run_session(index, spec, ctx):
    """One fresh session on the attempt's backend; returns its outcome record."""
    attempt, manifest, params, cal = (
        ctx["attempt"],
        ctx["manifest"],
        ctx["params"],
        ctx["cal"],
    )
    wire, record_event, observe = ctx["wire"], ctx["record_event"], ctx["observe"]
    spawn, paths, t_load, rates = (
        ctx["spawn"],
        ctx["paths"],
        ctx["t_load"],
        ctx["rates"],
    )
    limits, context = manifest["limits"], manifest["launch"]["context"]
    arm, workload = spec["arm"], spec["workload"]
    kernel, task_state = ctx["kernel"], ctx["task_state"]

    def waiting(busy, seconds):
        return wait_while(busy, seconds, observe, LOOP_PERIOD)

    windows = session_windows(
        cal, params, t_load, context, arm["output_cap"], OBSERVATION_PERIOD
    )
    root, home, fixture = fresh_session(attempt, workload)
    interrupt_file_holder["session"] = {
        "index": index,
        "workload": workload,
        "fixture": fixture,
    }
    if erases_slot(index, spec):
        # A slot is busy until its current batch ends, even after its client has left.
        if not waiting(lambda: wire.slot_busy(OBSERVATION_PERIOD), windows["settle"]):
            return {"session": index, "attempt_stop": "backend slot did not settle"}
        record_event("slot_erase", session=index, result=wire.erase_slot())
    timer = windows["hermes_timer"]
    write_json(
        home / "config.yaml",
        session_config(wire.url, context, spec["reasoning_echo"], timer, fixture),
    )
    env = session_env(home, Path(paths["task_venv"]))
    interrupt_file = root / "INTERRUPT"
    interrupt_file_holder["path"] = interrupt_file
    result_path = root / "result.json"
    precheck = None
    if workload.startswith("long") and not task_state["prechecked"]:
        task_state["prechecked"] = True
        caps = [a["output_cap"] for a in ARMS["session_arms"].values()]
        precheck = functools.partial(
            verify_long.precheck,
            wire.backend,
            smallest_cap=min(caps),
            input_ceiling=context - max(caps) - limits["input_margin_tokens"],
        )
    wire.begin_session(
        index,
        arm,
        spec["sampling"],
        manifest["seed"],
        context - arm["output_cap"] - limits["input_margin_tokens"],
        spec["request_limit"],
        precheck,
    )
    record_event(
        "session_start",
        session=index,
        arm=spec["arm_name"],
        workload=workload,
        reasoning_echo=spec["reasoning_echo"],
        hermes_timer_seconds=timer,
        rerun_of=spec.get("rerun_of"),
    )
    driver = spawn(
        [
            sys.executable,
            "-B",
            str(HERE / "driver.py"),
            "--fixture",
            str(fixture),
            "--url",
            wire.url,
            "--arm",
            json.dumps(arm),
            "--workload",
            workload,
            "--max-turns",
            str(limits["max_turns_per_user_turn"]),
            "--result",
            str(result_path),
            "--interrupt-file",
            str(interrupt_file),
        ],
        f"cli-{index:02d}",
        env,
        fixture,
    )
    session_start = time.monotonic()
    gap_clock = StallClock(session_start, windows["gap"])
    cli_log = attempt / f"cli-{index:02d}.log"
    kernel_session_start = kernel.bytes()
    cpu = log_size = 0.0
    stop = None
    cancelled = False
    extrema = RequestExtrema(record_event)
    try:
        while driver.poll() is None:
            sample, _ = observe()
            now = time.monotonic()
            active = wire.active
            extrema.observe(
                active["request_id"] if active is not None else None, sample
            )
            if wire.failure:
                stop = f"wire: {wire.failure}"
                break
            if ctx["server"].poll() is not None:
                return {
                    "session": index,
                    "attempt_stop": "backend exited during a session",
                }
            if kernel.grew():
                # Kernel compilation is the backend working with no stream or slot signal.
                gap_clock.progress(now)
                if active is not None:
                    active["last_progress"] = now
            if active is not None:
                gap_clock.progress(now)
                window = windows["stall"][active["phase"]]
                verdict = step_stop(
                    active["started"],
                    active["last_progress"],
                    now,
                    window,
                    windows["request_backstop"],
                )
                if verdict == "stall":
                    stop = f"stall in {active['phase']} (window {window:.1f}s)"
                    break
                if verdict == "backstop":
                    stop = "host-derived request backstop reached"
                    break
                if (
                    workload == "main-cancel"
                    and active["first_token"] is not None
                    and not cancelled
                ):
                    record_event(
                        "cancel_trigger",
                        session=index,
                        slots=wire.last_slots,
                        request_id=active["request_id"],
                    )
                    interrupt_file.touch()
                    wire.cancel_active()
                    cancelled = True
                    cancel_at = now
            else:
                new_cpu = tree_cpu(driver)
                size = cli_log.stat().st_size if cli_log.exists() else 0
                if new_cpu > cpu or size > log_size:
                    gap_clock.progress(now)
                cpu, log_size = new_cpu, size
                if gap_clock.stalled(now):
                    stop = "idle between requests beyond the host-derived gap window"
                    break
            if cancelled and now - cancel_at > CLEANUP_S:
                stop = "cancelled request did not settle within the cleanup bound"
                break
            time.sleep(LOOP_PERIOD)
    finally:
        extrema.close()
    if stop and driver.poll() is None:
        interrupt_file.touch()
        stop_active_request(wire, record_event, stop)
        waiting(lambda: driver.poll() is None, GRACE_S)
    slot_idle = None
    if cancelled:
        slot_idle = waiting(
            lambda: wire.slot_busy(OBSERVATION_PERIOD),
            max(0.0, CLEANUP_S - (time.monotonic() - cancel_at)),
        )
        record_event(
            "cancel_settled",
            session=index,
            slot_idle=slot_idle,
            seconds=time.monotonic() - cancel_at,
        )
    session = wire.end_session()
    result = json.loads(result_path.read_text()) if result_path.exists() else None
    verified = {}
    verifier = threading.Thread(
        target=lambda: verified.update(
            value=verify_session(
                workload,
                fixture,
                result,
                Path(paths["task_venv"]),
                manifest["allowlist"],
            )
        ),
        daemon=True,
    )
    verifier.start()
    waiting(verifier.is_alive, VERIFY_S)
    verification = verified.get("value", {"error": "verifier did not finish"})
    for event in (
        json.loads(line) for line in (attempt / "events.jsonl").open(encoding="utf-8")
    ):
        if (
            event["kind"] == "response_end"
            and event.get("session") == index
            and event.get("timings")
            and not event.get("kernel_compiled")
        ):
            t = event["timings"]
            rates.observe_prefill(t.get("prompt_n", 0), t.get("prompt_ms", 0) / 1000)
            rates.observe_decode(
                t.get("predicted_n", 0), t.get("predicted_ms", 0) / 1000
            )
    outcome = {
        "session": index,
        "arm": spec["arm_name"],
        "workload": workload,
        "reasoning_echo": spec["reasoning_echo"],
        "stop": stop,
        "driver_exit": driver.returncode,
        "requests": session["requests"],
        "first_request": session["first_request"],
        "machine_seconds": time.monotonic() - session_start,
        "cli_start_seconds": (result or {}).get("cli_start_seconds"),
        "tool_calls": session["tool_call_validity"],
        "verification": verification,
        "cancelled": cancelled,
        "slot_idle_after_cancel": slot_idle,
        "kernel_cache_growth_bytes": kernel.bytes() - kernel_session_start,
        "rerun_of": spec.get("rerun_of"),
    }
    if workload == "long:all":
        # AC1 coverage is recorded apart from completion: fewer requests is a finding.
        outcome["ac1_request_coverage"] = ac1_request_coverage(session["requests"])
    record_event("session_end", **outcome)
    interrupt_file_holder.pop("session", None)  # scored above; not cut short
    # The session's whole tree goes before its state is archived, so nothing it started
    # (a background shell, say) outlives it into the next session at the same paths.
    for proc, job, _name in ctx["owned"]:
        if proc is driver:
            job.close()
    archive = attempt / f"session-{index:02d}"
    if not waiting(lambda: not renamed(root, archive), CLEANUP_S):
        return {**outcome, "attempt_stop": "session state could not be archived"}
    return outcome


def renamed(source: Path, target: Path) -> bool:
    try:
        source.rename(target)
    except OSError:
        return False  # a scanner may briefly hold a handle
    return True


def verify_session(workload, fixture, result, venv, allowlist):
    """Independent checks from fixture state or exact expected answers, never model claims."""
    if workload in ("smoke", "decode-sample"):
        return {"expected_answer": bool(result and result.get("expected_answer"))}
    if workload.startswith("long"):
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        conversation = (result or {}).get("conversation") or []
        return {
            "score": verify_long.score(fixture, python),
            # Hermes points TMPDIR and its scratch directory into the session's own home.
            "contamination": verify_long.contamination(
                conversation,
                fixture,
                [*allowlist, str(fixture.parent / "home")],
                fixture.parent / "home" / "tmp",
            ),
            "screened": verify_long.screened(conversation),
        }
    return None


def write_calibration(lab, attempt, hash_s, t_load, outcomes, params, record_event):
    """Fail closed: every field must come from this host's measurements.

    Checkpoint headroom comes from the attempt's own admission receipt (attempt 04 was
    handed a post-load sample instead, and froze 0 checkpoints).
    """
    prefill, decode, first_events = [], [], []
    admission = None
    for event in (
        json.loads(line) for line in (attempt / "events.jsonl").open(encoding="utf-8")
    ):
        if event["kind"] == "admission":
            admission = event
        if event["kind"] != "response_end" or not event.get("timings"):
            continue
        if event.get("kernel_compiled"):
            continue  # compile time is not throughput
        t = event["timings"]
        if t.get("prompt_n", 0) >= params.min_prefill_sample_tokens and t.get(
            "prompt_ms"
        ):
            prefill.append(t["prompt_n"] / (t["prompt_ms"] / 1000))
        if t.get("predicted_n", 0) >= params.min_decode_sample_tokens and t.get(
            "predicted_ms"
        ):
            decode.append(t["predicted_n"] / (t["predicted_ms"] / 1000))
        if event.get("first_event_seconds") is not None:
            first_events.append(event["first_event_seconds"])
    cli_starts = [
        o["cli_start_seconds"] for o in outcomes if o.get("cli_start_seconds")
    ]
    sizes = [
        float(m.group(1))
        for m in CHECKPOINT_LINE.finditer(
            (attempt / "backend.log").read_text(encoding="utf-8", errors="replace")
        )
    ]
    missing = [
        name
        for name, values in (
            ("prefill", prefill),
            ("decode", decode),
            ("overhead", first_events),
            ("cli_start", cli_starts),
            ("checkpoint_size", sizes),
            ("admission", [admission] if admission else []),
        )
        if not values
    ]
    if missing:
        record_event("calibration_failed", missing=missing)
        raise RuntimeError(f"calibration incomplete (fail closed): missing {missing}")
    rates = {
        "prefill_tps": statistics.median(prefill),
        "decode_tps": statistics.median(decode),
        "overhead_s": statistics.median(first_events),
        "load_s": t_load,
        "cli_start_s": statistics.median(cli_starts),
        "hash_s": hash_s,
    }
    checkpoint_bytes = int(max(sizes) * (1 << 20))
    headroom = admission["sample"]["ram_available"] - admission["cpu_needed"]
    frozen = max(0, min(MAX_CHECKPOINTS, headroom // checkpoint_bytes))
    arms = json.loads((HERE / "arms.json").read_text(encoding="utf-8"))
    planned = []
    for plan_name in ("screen", "R0", "R1", "R2", "R3"):
        plan = arms["attempt_plans"][plan_name]
        requests = sum(
            arms["planned_requests"][s["workload"]] for s in plan["sessions"]
        )
        cap = max(
            arms["session_arms"].get(s["arm"], {"output_cap": 768})["output_cap"]
            for s in plan["sessions"]
        )
        planned.append((len(plan["sessions"]), requests, cap))
    budget = sprint_budget(Calibration(**rates), params, planned)
    calibration = {
        "rates": rates,
        "checkpoint_bytes": checkpoint_bytes,
        "frozen_checkpoints": int(frozen),
        "sprint_budget_s": budget,
        "planned_attempts": planned,
        "calibrated_at_attempt": attempt.name,
    }
    write_json(lab / "calibration.json", calibration)
    record_event("calibration_written", **calibration)


if __name__ == "__main__":
    main()
