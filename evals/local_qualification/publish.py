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

from policy import ac1_request_coverage, manifest_digest
import verify_long
from wire import tool_call_validity

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# L1: the request fields every long-task receipt carries; a missing one is named, never dropped.
REQUEST_FIELDS = (
    "meaningful_first_token_seconds",
    "id_slot",
    "finish_reason",
    "tool_calls",
    "input_tokens",
    "cached_tokens",
    "uncached_prompt_tokens",
    "reasoning_tokens",
    "visible_tokens",
    "tool_call_tokens",
    "prompt_ms",
    "decode_ms",
    "decode_tps",
    "seconds",
    "predicted_initial_seconds",
    "predicted_rearmed_seconds",
    "resources",
)


TIMING_FIELDS = (
    "seconds",
    "meaningful_first_token_seconds",
    "predicted_initial_seconds",
    "predicted_rearmed_seconds",
)


def _events(attempt: Path):
    with (attempt / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def receipts(attempt: Path, task_python: Path | None = None) -> dict:
    """Correlated receipts for one attempt.

    ``task_python`` scores a long session an attempt stop cut short before the lab
    recorded ``session_stopped`` itself, from its preserved fixture (L2).
    """
    requests, sessions, started, other, last_body = {}, [], {}, [], {}
    t0 = None
    for event in _events(attempt):
        kind = event["kind"]
        t0 = event["at"] if t0 is None else t0
        if kind == "sample":
            continue
        rid = event.get("request_id")
        if kind == "request":
            last_body[event["session"]] = event.get("original_body") or {}
            requests[rid] = {
                "request_id": rid,
                "session": event["session"],
                "input_tokens": event["input_tokens"],
                "prompt_sha256": event["prompt_sha256"],
                "system_sha256": event["system_sha256"],
                "tools_sha256": event["tools_sha256"],
                "continuation_of_length_finish": event["continuation_of_length_finish"],
                "predicted_initial_seconds": event.get("predicted_initial_seconds"),
                "_at": event["at"],
            }
        elif kind in ("response_end", "response_cancelled") and rid in requests:
            r = requests[rid]
            t = event.get("timings") or {}
            fields = {
                "seconds": event.get("seconds"),
                "meaningful_first_token_seconds": event.get(
                    "meaningful_first_token_seconds"
                ),
                "first_event_seconds": event.get("first_event_seconds"),
                "predicted_initial_seconds": event.get("predicted_initial_seconds"),
                "predicted_rearmed_seconds": event.get("predicted_rearmed_seconds"),
                "id_slot": event.get("id_slot"),
                "id_slot_source": event.get("id_slot_source"),
                "finish_reason": event.get("finish_reason"),
                "tool_calls": event.get("tool_calls"),
                "reasoning_tokens": event.get("reasoning_tokens"),
                "visible_tokens": event.get("visible_tokens"),
                "tool_call_tokens": event.get("tool_call_tokens"),
                "tool_call_validity": event.get("tool_call_validity"),
                "kernel_compiled": event.get("kernel_compiled"),
                "cached_tokens": t.get("cache_n"),
                "uncached_prompt_tokens": t.get("prompt_n"),
                "decoded_tokens": t.get("predicted_n"),
                "prompt_ms": t.get("prompt_ms"),
                "decode_ms": t.get("predicted_ms"),
                "decode_tps": t.get("predicted_per_second"),
            }
            if r.get("outcome") == "stopped":
                # The attempt stop is the cause; a later record only fills gaps.
                _fill(r, fields)
            else:
                r.update(outcome=kind, **fields)
            r.setdefault("_ended_at", event["at"])
        elif kind == "request_stopped" and rid in requests:
            r = requests[rid]
            r.update(outcome="stopped", stop_reason=event.get("reason"))
            r.update({k: event[k] for k in TIMING_FIELDS if event.get(k) is not None})
            r.setdefault("_ended_at", event["at"])
        elif kind == "wire_failure" and rid in requests:
            r = requests[rid]
            r.setdefault("outcome", "wire_failure")
            r["error"] = event.get("error")
            r["_failed_at"] = event["at"]
            _fill(r, {k: event.get(k) for k in TIMING_FIELDS})
            r.setdefault("_ended_at", event["at"])
            other.append({k: v for k, v in event.items() if k != "manifest_id"})
        elif kind == "request_resources" and rid in requests:
            requests[rid]["resources"] = {
                k: v
                for k, v in event.items()
                if k not in ("at", "kind", "manifest_id", "request_id")
            }
        elif kind in ("session_end", "session_stopped"):
            sessions.append({
                **{k: v for k, v in event.items() if k not in ("at", "manifest_id")},
                "stopped": kind == "session_stopped",
            })
        elif kind not in ("progress", "owned_process"):
            if kind == "session_start":
                started[event["session"]] = event["workload"]
            other.append({k: v for k, v in event.items() if k != "manifest_id"})
    outcome = json.loads((attempt / "outcome.json").read_text(encoding="utf-8"))
    session_stop = {s["session"]: s.get("stop") for s in sessions if not s["stopped"]}
    for r in requests.values():
        if r.get("outcome") == "wire_failure" and "stop_reason" not in r:
            # Before the request_stopped receipt existed, a stop surfaced only as the
            # aborted request's wire failure. Its cause is its own session's recorded
            # stop; only a request still in flight at the attempt stop takes the
            # attempt's reason.
            cause = session_stop.get(r["session"])
            if cause is None and r["session"] not in session_stop:
                if outcome["reason"].startswith("stopped:"):
                    cause = outcome["reason"]
            if cause:
                r["outcome"], r["stop_reason"] = "stopped", cause
                if r.get("seconds") is None:
                    r["seconds"] = round(r["_failed_at"] - r["_at"], 3)
                    r["seconds_source"] = "receipt timestamps"
        # Times relative to the attempt's first receipt: machine time is recomputable.
        r["started_s"] = round(r.pop("_at") - t0, 3)
        ended = r.pop("_ended_at", None)
        r["ended_s"] = None if ended is None else round(ended - t0, 3)
        r.pop("_failed_at", None)
        split = [
            r.get(k) for k in ("decoded_tokens", "reasoning_tokens", "visible_tokens")
        ]
        if None not in split:
            # Decoded output that is neither reasoning, visible content nor counted
            # tool-call output: template markup, plus tool-call output in receipts
            # whose wire did not count it (before round 5).
            r["unsplit_decoded_tokens"] = (
                split[0] - split[1] - split[2] - (r.get("tool_call_tokens") or 0)
            )
        r["missing"] = [f for f in REQUEST_FIELDS if r.get(f) is None]
    machine_time = _machine_time(requests.values())
    recorded = {s["session"] for s in sessions}
    for index, workload in started.items():
        fixture = attempt / "live" / "fixture"
        if (
            index not in recorded
            and workload.startswith("long")
            and task_python is not None
            and fixture.is_dir()
        ):
            body = last_body.get(index) or {}
            own_requests = [r for r in requests.values() if r["session"] == index]
            conversation = body.get("messages") or []
            known = {
                (t.get("function") or {}).get("name") for t in body.get("tools") or []
            }
            sessions.append({
                "session": index,
                "workload": workload,
                "stopped": True,
                "requests": len(own_requests),
                "tool_calls": tool_call_validity(conversation, known),
                **(
                    {"ac1_request_coverage": ac1_request_coverage(len(own_requests))}
                    if workload == "long:all"
                    else {}
                ),
                "verification": {
                    "score": verify_long.score(fixture, task_python),
                    "contamination": _screen(attempt, fixture, conversation),
                    "screened": verify_long.screened(conversation),
                },
                "scored": "at publish, from the session's preserved fixture and the "
                "conversation the wire last forwarded",
            })
    for s in sessions:
        if str(s.get("workload", "")).startswith("long") and isinstance(
            s.get("tool_calls"), list
        ):
            # Validity covers every delivered call, or names the shortfall: Hermes's
            # history, the source before round 5, drops a call it rejected.
            own = [r for r in requests.values() if r["session"] == s["session"]]
            s["delivered_tool_calls"] = sum(r.get("tool_calls") or 0 for r in own)
            s["unvalidated_tool_calls"] = s["delivered_tool_calls"] - len(
                s["tool_calls"]
            )
            s["length_finished_tool_call_requests"] = [
                r["request_id"]
                for r in own
                if r.get("finish_reason") == "length" and r.get("tool_calls")
            ]
    outcome.pop("sessions", None)
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    return {
        "attempt": attempt.name,
        "manifest_id": manifest["id"],
        "plan": manifest["plan"],
        "source_commit": manifest.get("source_commit"),
        "outcome": outcome,
        "sessions": sessions,
        "machine_time": machine_time,
        "requests": list(requests.values()),
        "events": other,
    }


def _screen(attempt: Path, fixture: Path, conversation: list) -> list:
    """L4 on a cut-short session's last forwarded conversation, as the lab screens a
    finished one: the session's own home is in scope, and /tmp is the TEMP it had.

    Each attempt scored here was stopped with a request in flight, so the conversation
    that request forwarded holds every tool call Hermes ran (a receipt test checks it).
    """
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    home = attempt / "live" / "home"
    private = home / "tmp"
    temp = private if private.is_dir() else Path(os.environ["TEMP"])
    return verify_long.contamination(
        conversation, fixture, [*manifest["allowlist"], str(home)], temp
    )


def _fill(record: dict, fields: dict) -> None:
    for key, value in fields.items():
        if record.get(key) is None and value is not None:
            record[key] = value


def _machine_time(requests) -> list[dict]:
    """Per session: first request start to last response end, excluding load (S2's
    definition), from the published relative times."""
    spans = {}
    for r in requests:
        if r["ended_s"] is None:
            continue
        first, last = spans.get(r["session"], (r["started_s"], r["ended_s"]))
        spans[r["session"]] = (min(first, r["started_s"]), max(last, r["ended_s"]))
    return [
        {
            "session": session,
            "first_request_s": first,
            "last_response_s": last,
            "machine_time_s": round(last - first, 3),
        }
        for session, (first, last) in sorted(spans.items())
    ]


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
    # Any remaining spelling of the profile, e.g. a repr nested in JSON doubles every
    # backslash again (attempt 05's PermissionError reason).
    user = re.escape(Path.home().name)
    return re.sub(
        rf"[A-Za-z]:[\\/]+users[\\/]+{user}\b", "<home>", text, flags=re.IGNORECASE
    )


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


def published_manifest(attempt: Path, pairs) -> dict:
    """The frozen manifest with local roots replaced.

    It keeps ``id``, the digest the lab verified at launch over the private manifest.
    Sanitizing changes the bytes, so ``published_digest`` covers this public copy instead.
    """
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    public = json.loads(sanitize(json.dumps(manifest), pairs))
    public["published_digest"] = manifest_digest({
        k: v for k, v in public.items() if k != "published_digest"
    })
    return public


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lab = args.lab.resolve()
    attempt = lab / "attempts" / args.attempt
    paths = json.loads((lab / "paths.json").read_text(encoding="utf-8"))
    venv = Path(paths["task_venv"])
    task_python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    text = sanitize(
        json.dumps(receipts(attempt, task_python), indent=1), placeholders(lab, attempt)
    )
    findings = privacy_screen(text, attempt)
    manifest = published_manifest(attempt, placeholders(lab, attempt))
    manifest_text = json.dumps(manifest, indent=1, sort_keys=True)
    findings += privacy_screen(manifest_text, attempt)
    if findings:
        raise SystemExit(f"privacy screen refused {args.attempt}: {findings}")
    (args.out / "manifests").mkdir(parents=True, exist_ok=True)
    target = args.out / f"{args.attempt}.json"
    target.write_bytes((text + "\n").encode("utf-8"))  # LF on every host
    (args.out / "manifests" / f"{manifest['id']}.json").write_bytes(
        (manifest_text + "\n").encode("utf-8")
    )
    print(target)


if __name__ == "__main__":
    main()
