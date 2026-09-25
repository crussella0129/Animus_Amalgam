"""Freeze one lab attempt plan into a manifest; loads no model and runs no tests.

The lab root must sit outside the repository so the model's terminal cannot reach the task
sources, the verifier or earlier attempts. Time limits are derived later from the host's
calibration record; this manifest freezes only dimensionless parameters and the record itself.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from hermes_cli.local_runtime.estimator import ctx_bytes, profile_from_gguf
from hermes_cli.local_runtime.gguf import read_gguf_header
from hermes_cli.local_runtime.throughput import (
    Calibration,
    TimeParams,
    request_backstop,
)
from policy import manifest_digest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CPU_PATTERN = r"blk\.\d+\.ffn_.*\.weight"
SEED = 42
TERMINAL_TIMEOUT_DEFAULT = (
    180  # Hermes terminal.timeout default; recorded, moves with T-219
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def inside_repo(path: Path) -> bool:
    resolved = path.resolve()
    return resolved == REPO or REPO in resolved.parents


def task_corpus_digest() -> str:
    files = [
        HERE / "driver.py",
        HERE / "arms.json",
        HERE / "verify_long.py",
        *sorted((HERE / "tasks").rglob("*")),
    ]
    return json_digest({
        str(p.relative_to(HERE)).replace("\\", "/"): digest(p)
        for p in files
        if p.is_file()
    })


def resolve_sessions(arms: dict, plan: dict) -> list[dict]:
    sessions = []
    multiple = arms["session_request_limit_multiple"]
    for spec in plan["sessions"]:
        name = spec["arm"]
        if name.startswith("winner:"):
            mode = name.split(":", 1)[1]
            name = arms["screen_winners"].get(mode)
            if not name:
                raise SystemExit(
                    f"no screen winner recorded for thinking mode {mode!r}"
                )
        arm = arms["session_arms"][name]
        planned = arms["planned_requests"][spec["workload"]]
        sessions.append({
            "arm_name": name,
            "arm": arm,
            "sampling": arms["sampling"][arm["sampling"]],
            "workload": spec["workload"],
            "reasoning_echo": spec["echo"],
            "planned_requests": planned,
            "request_limit": planned * multiple,
        })
    return sessions


def task_venv(lab: Path) -> Path:
    """Disposable stdlib venv from the managed runtime's base interpreter; no download."""
    venv = lab / "task-venv"
    if (
        not (venv / "Scripts" / "python.exe").exists()
        and not (venv / "bin" / "python").exists()
    ):
        subprocess.run(
            [sys._base_executable, "-m", "venv", "--without-pip", str(venv)],
            check=True,
            timeout=600,
        )
    return venv


def terminal_allowlist(venv: Path) -> list[str]:
    """The task venv, OS system directories and the bash the terminal tool resolves."""
    from tools.environments import local as terminal_local

    saved = os.environ.get("LOCALAPPDATA")
    # Sessions get a private LOCALAPPDATA, so resolve bash exactly as a session would.
    os.environ["LOCALAPPDATA"] = str(venv / "no-local-appdata")
    try:
        bash = terminal_local._find_bash()
        bins = terminal_local._git_bash_bin_dirs()
    finally:
        if saved is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = saved
    system_root = os.environ.get("SYSTEMROOT", "")
    return sorted({str(venv), system_root, str(Path(bash).parent), *bins} - {""})


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    lab = args.lab.resolve()
    if inside_repo(lab):
        raise SystemExit("the lab root must be outside the repository")
    lab.mkdir(parents=True, exist_ok=True)
    arms = json.loads((HERE / "arms.json").read_text(encoding="utf-8"))
    plan = arms["attempt_plans"][args.plan]
    profile = arms["launch_profiles"][plan["launch"]]
    params = TimeParams(**arms["time_params"])
    calibration_path = lab / "calibration.json"
    record = (
        json.loads(calibration_path.read_text()) if calibration_path.exists() else None
    )
    if args.plan != "calibration" and record is None:
        raise SystemExit("run the calibration plan first; later plans need its record")
    header = read_gguf_header(args.model)
    cpu_weights = sum(
        size
        for name, size in header.tensor_sizes.items()
        if re.fullmatch(CPU_PATTERN, name) or name == "token_embd.weight"
    )
    context = profile["context"]
    checkpoints = profile["ctx_checkpoints"]
    if checkpoints == "calibrated":
        checkpoints = record["frozen_checkpoints"]
    checkpoint_ram = checkpoints * record["checkpoint_bytes"] if record else 0
    flags = [
        "--alias",
        "amalgam-pilot",
        "--offline",
        "--ctx-size",
        str(context),
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
        CPU_PATTERN + "=CPU",
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
        str(checkpoints),
        "--metrics",
    ]
    if profile["checkpoint_min_step"] is not None:
        flags += ["--checkpoint-min-step", str(profile["checkpoint_min_step"])]
    if profile["trace"]:
        flags += ["-lv", "4"]
    sessions = resolve_sessions(arms, plan)
    venv = task_venv(lab)
    cal = Calibration(**record["rates"]) if record else None
    hermes_timer = (
        request_backstop(
            cal, params, context, max(s["arm"]["output_cap"] for s in sessions)
        )
        if cal
        else None
    )
    manifest = {
        "schema": 2,
        "plan": args.plan,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10, cwd=REPO
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, timeout=10, cwd=REPO
            ).strip()
        ),
        "model": {
            "name": args.model.name,
            "sha256": digest(args.model),
            "bytes": args.model.stat().st_size,
            "tensor_bytes": header.tensor_bytes,
            "architecture": header.architecture,
            "tokenizer_sha256": json_digest({
                k: v
                for k, v in header.metadata.items()
                if k.startswith("tokenizer.") and "chat_template" not in k
            }),
            "template_sha256": json_digest({
                k: v for k, v in header.metadata.items() if "chat_template" in k
            }),
        },
        "backend": {
            "name": args.server.name,
            "sha256": digest(args.server),
            "libraries": {
                p.name: digest(p) for p in sorted(args.server.parent.glob("*.dll"))
            },
        },
        "placement": {
            "load_mode": "none",
            "cpu_pattern": CPU_PATTERN,
            "cpu_weight_bytes": cpu_weights,
            "gpu_weight_bytes": header.tensor_bytes - cpu_weights,
            "context_bytes_upper": ctx_bytes(profile_from_gguf(header), context),
            "cpu_overhead_bytes": 2 << 30,
            "gpu_overhead_bytes": 1 << 30,
            "checkpoint_ram_bytes": checkpoint_ram,
        },
        "launch": {
            "profile": plan["launch"],
            "context": context,
            "flags": flags,
            "server_output_limit": "request cap only (server reports n_predict=-1)",
        },
        "sessions": sessions,
        "seed": SEED,
        "limits": {
            "context": context,
            "input_margin_tokens": 512,
            "page_in_stop_below_ram_bytes": 8 << 30,
            "max_requests": 400,
            "max_launches": 12,
            "ram_reserve_bytes": 4 << 30,
            "vram_reserve_bytes": 1 << 30,
            "max_turns_per_user_turn": arms["max_turns_per_user_turn"],
        },
        "time_params": arms["time_params"],
        "owner_choice": {
            "model": "existing 27B first",
            "time_model": arms["owner_time_model_decision"],
        },
        "calibration_record": record,
        "hermes_timeouts": {
            "request_timeout_seconds": hermes_timer,
            "stale_timeout_seconds": hermes_timer,
            "local_stream_stale_timeout": hermes_timer,
            "turn_liveness_timeout_s": hermes_timer,
            "terminal_timeout": TERMINAL_TIMEOUT_DEFAULT,
            "note": "null during calibration: the lab sets them per session from that "
            "attempt's measured load time",
        },
        "allowlist": terminal_allowlist(venv),
        "interpreter": sys.version,
        "task_corpus_sha256": task_corpus_digest(),
        "dependencies": sorted(
            f"{d.metadata['Name']}=={d.version}"
            for d in importlib.metadata.distributions()
        ),
        "rendered_prefix": {
            "status": "not-measured",
            "reason": "measured per session by the wire after admission",
        },
        "tools": {"fixed_workloads": [], "long": ["terminal"], "tool_search": "off"},
    }
    manifest["id"] = manifest_digest(manifest)
    manifests = lab / "manifests"
    manifests.mkdir(exist_ok=True)
    path = manifests / f"{args.plan}-{manifest['id'][:12]}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Paths are local-only; no secrets from the live profile are copied.
    (lab / "paths.json").write_text(
        json.dumps({
            "model": str(args.model.resolve()),
            "server": str(args.server.resolve()),
            "task_venv": str(venv),
        }),
        encoding="utf-8",
    )
    print(
        json.dumps({
            "manifest": str(path),
            "id": manifest["id"],
            "sessions": [s["arm_name"] + ":" + s["workload"] for s in sessions],
        })
    )


if __name__ == "__main__":
    main()
