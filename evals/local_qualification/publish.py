"""Publish one attempt's receipts into the Book: correlated per-request fields, no private text.

Prompts, replies and tool output never leave the lab (the task's defects stay private, and
conversations may echo local paths); only their hashes and token counts are published. Every
known local root is replaced by a placeholder, and a privacy screen fails closed on anything
that still looks like a user path, credential or the backend's key.

    python publish.py --lab <lab> --attempt <attempt dir name> --out <book receipts dir>
"""

import argparse
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# L1: the request fields every long-task receipt carries; a missing one is named, never dropped.
REQUEST_FIELDS = (
    "id_slot",
    "finish_reason",
    "input_tokens",
    "cached_tokens",
    "uncached_prompt_tokens",
    "reasoning_tokens",
    "visible_tokens",
    "prompt_ms",
    "decode_ms",
    "decode_tps",
    "seconds",
    "predicted_initial_seconds",
    "predicted_rearmed_seconds",
    "resources",
)


def _events(attempt: Path):
    with (attempt / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def receipts(attempt: Path) -> dict:
    requests, sessions, other = {}, [], []
    for event in _events(attempt):
        kind = event["kind"]
        if kind == "sample":
            continue
        rid = event.get("request_id")
        if kind == "request":
            requests[rid] = {
                "request_id": rid,
                "session": event["session"],
                "input_tokens": event["input_tokens"],
                "prompt_sha256": event["prompt_sha256"],
                "system_sha256": event["system_sha256"],
                "tools_sha256": event["tools_sha256"],
                "continuation_of_length_finish": event["continuation_of_length_finish"],
            }
        elif kind in ("response_end", "response_cancelled") and rid in requests:
            r = requests[rid]
            t = event.get("timings") or {}
            r.update(
                outcome=kind,
                seconds=event.get("seconds"),
                meaningful_first_token_seconds=event.get(
                    "meaningful_first_token_seconds"
                ),
                first_event_seconds=event.get("first_event_seconds"),
                predicted_initial_seconds=event.get("predicted_initial_seconds"),
                predicted_rearmed_seconds=event.get("predicted_rearmed_seconds"),
                id_slot=event.get("id_slot"),
                finish_reason=event.get("finish_reason"),
                tool_calls=event.get("tool_calls"),
                reasoning_tokens=event.get("reasoning_tokens"),
                visible_tokens=event.get("visible_tokens"),
                kernel_compiled=event.get("kernel_compiled"),
                cached_tokens=t.get("cache_n"),
                uncached_prompt_tokens=t.get("prompt_n"),
                decoded_tokens=t.get("predicted_n"),
                prompt_ms=t.get("prompt_ms"),
                decode_ms=t.get("predicted_ms"),
                decode_tps=t.get("predicted_per_second"),
            )
        elif kind == "request_resources" and rid in requests:
            requests[rid]["resources"] = {
                k: v
                for k, v in event.items()
                if k not in ("at", "kind", "manifest_id", "request_id")
            }
        elif kind == "session_end":
            sessions.append({
                k: v for k, v in event.items() if k not in ("at", "manifest_id")
            })
        elif kind not in ("progress", "owned_process"):
            other.append({k: v for k, v in event.items() if k != "manifest_id"})
    for r in requests.values():
        r["missing"] = [f for f in REQUEST_FIELDS if r.get(f) is None]
    outcome = json.loads((attempt / "outcome.json").read_text(encoding="utf-8"))
    outcome.pop("sessions", None)
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    return {
        "attempt": attempt.name,
        "manifest_id": manifest["id"],
        "plan": manifest["plan"],
        "source_commit": manifest.get("source_commit"),
        "outcome": outcome,
        "sessions": sessions,
        "requests": list(requests.values()),
        "events": other,
    }


def placeholders(lab: Path, attempt: Path) -> list[tuple[str, str]]:
    roots = {
        str(attempt): "<attempt>",
        str(lab): "<lab>",
        str(REPO): "<repo>",
        os.environ.get("LOCALAPPDATA", ""): "<localappdata>",
        os.environ.get("APPDATA", ""): "<appdata>",
        str(Path.home()): "<home>",
    }
    pairs = []
    for root, name in roots.items():
        if root:
            for form in {root, root.replace("\\", "/"), root.replace("\\", "\\\\")}:
                pairs.append((form, name))
    # Longest first, so a nested root wins over its parent.
    return sorted(pairs, key=lambda p: -len(p[0]))


def sanitize(text: str, pairs) -> str:
    for root, name in pairs:
        text = re.sub(re.escape(root), name, text, flags=re.IGNORECASE)
    return text


def privacy_screen(text: str, attempt: Path) -> list[str]:
    """Anything left that names this machine's user, its key or a credential."""
    findings = []
    user = Path.home().name
    if re.search(rf"users[\\/]+{re.escape(user)}\b", text, re.IGNORECASE):
        findings.append("user profile path")
    key = attempt / "backend.key"
    if key.exists() and key.read_text().strip() in text:
        findings.append("backend api key")
    if re.search(r"bearer\s+\S+|api[_-]?key\"?\s*[:=]\s*\"[^\"<]", text, re.IGNORECASE):
        findings.append("credential-shaped value")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
        findings.append("email address")
    return findings


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lab = args.lab.resolve()
    attempt = lab / "attempts" / args.attempt
    text = sanitize(json.dumps(receipts(attempt), indent=1), placeholders(lab, attempt))
    findings = privacy_screen(text, attempt)
    if findings:
        raise SystemExit(f"privacy screen refused {args.attempt}: {findings}")
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{args.attempt}.json"
    target.write_text(text + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
