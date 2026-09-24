"""Prepare an isolated operational lab; does not load a model or run tests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path

from hermes_cli.local_runtime.estimator import ctx_bytes, profile_from_gguf
from hermes_cli.local_runtime.gguf import read_gguf_header


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--lab", type=Path, required=True)
    args = parser.parse_args()
    lab = args.lab.resolve()
    lab.mkdir(parents=True, exist_ok=True)
    header = read_gguf_header(args.model)
    # Use the installed runtime's existing hybrid FFN-on-CPU placement, fixed
    # before launch. Price its exact tensor names rather than average layers.
    cpu_pattern = r"blk\.\d+\.ffn_.*\.weight"
    cpu_weights = sum(
        size
        for name, size in header.tensor_sizes.items()
        if re.fullmatch(cpu_pattern, name) or name == "token_embd.weight"
    )
    manifest = {
        "schema": 1,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, timeout=10
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
            "cpu_pattern": cpu_pattern,
            "cpu_weight_bytes": cpu_weights,
            "gpu_weight_bytes": header.tensor_bytes - cpu_weights,
            "context_bytes_upper": ctx_bytes(profile_from_gguf(header), 8192),
            "cpu_overhead_bytes": 2 << 30,
            "gpu_overhead_bytes": 1 << 30,
        },
        "limits": {
            "context": 8192,
            "input_tokens": 4096,
            "output_tokens": 128,
            "request_seconds": 300,
            "load_seconds": 300,
            "load_page_in_allowance_seconds": 60,
            "max_requests": 18,
            "max_launches": 6,
            "total_seconds": 3600,
            "ram_reserve_bytes": 4 << 30,
            "vram_reserve_bytes": 1 << 30,
        },
        "owner_choice": {"model": "existing 27B first", "pilot_seconds": 300},
        "interpreter": sys.version,
        "task_corpus_sha256": digest(Path(__file__).with_name("driver.py")),
        "sampling": {"temperature": 0, "top_p": 1, "seed": 42},
        "dependencies": sorted(
            f"{d.metadata['Name']}=={d.version}"
            for d in importlib.metadata.distributions()
        ),
        "rendered_prefix": {
            "status": "not-measured",
            "reason": "server not yet admitted",
        },
        "tools": {"smoke": [], "operation": ["terminal", "file"]},
    }
    manifest["id"] = json_digest(manifest)
    (lab / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Paths are local-only; no secrets from the live profile are copied.
    (lab / "paths.json").write_text(
        json.dumps({
            "model": str(args.model.resolve()),
            "server": str(args.server.resolve()),
        }),
        encoding="utf-8",
    )
    for name in ("home", "fixture", "receipts"):
        (lab / name).mkdir(exist_ok=True)
    config = {
        "model": {
            "default": "amalgam-pilot",
            "provider": "custom",
            "base_url": "http://127.0.0.1:18082/v1",
        },
        "local_runtime": {"enabled": False},
        "compression": {"enabled": False},
        "fallback_models": [],
        "display": {"streaming": True},
        "terminal": {"backend": "local", "cwd": str(lab / "fixture")},
        "auxiliary": {
            "compression": {
                "provider": "custom",
                "model": "amalgam-pilot",
                "base_url": "http://127.0.0.1:18082/v1",
            }
        },
    }
    (lab / "home" / "config.yaml").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )
    fixtures = {
        "settings.json": '{"retry_limit": 2}\n',
        "check.py": "import json\nfrom pathlib import Path\n"
        'assert json.loads(Path("settings.json").read_text())["retry_limit"] == 3\n'
        'print("CHECK_OK")\n',
    }
    for name, content in fixtures.items():
        path = lab / "fixture" / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print(
        json.dumps({"manifest_id": manifest["id"], "placement": manifest["placement"]})
    )


if __name__ == "__main__":
    main()
