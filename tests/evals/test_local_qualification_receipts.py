"""Published Sprint 3 receipts are correlated, complete and private (T-214 V3, M3, M4, L1).

Every attempt receipt resolves to its published manifest. A manifest keeps the ``id`` the
lab verified over the private original at launch; sanitizing local paths changes the
bytes, so ``published_digest`` covers the public copy instead.
"""

import json
from pathlib import Path
import re

import pytest

from evals.local_qualification.policy import manifest_digest

QUALIFICATION = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "sprints"
    / "s3"
    / "sprint-tests"
    / "qualification"
)
RECEIPTS = sorted(QUALIFICATION.glob("attempt-*.json"))
PRIVATE = re.compile(r"[A-Za-z]:[\\/]+Users|/Users/|/home/|Bearer\s|\b[0-9a-f]{48}\b")
# L1/M3: every request carries these, or names them missing; never silently absent.
# Tool-call validity is per session (M3), checked on the sessions.
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
    "prompt_ms",
    "decode_ms",
    "decode_tps",
    "seconds",
    "predicted_initial_seconds",
    "predicted_rearmed_seconds",
    "resources",
)
RATES = {"prefill_tps", "decode_tps", "overhead_s", "load_s", "cli_start_s"}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest(record):
    return _load(QUALIFICATION / "manifests" / f"{record['manifest_id']}.json")


def test_every_attempt_is_published():
    """V3 is about every attempt, not whichever files happen to exist."""
    assert RECEIPTS, "the Sprint 3 receipts are part of the evidence handoff"
    attempts = max(_load(p)["outcome"]["budget"]["attempts"] for p in RECEIPTS)
    published = sorted(int(p.stem.split("-")[1]) for p in RECEIPTS)
    assert published == list(range(1, attempts + 1))


@pytest.mark.parametrize(
    "path", sorted(QUALIFICATION.rglob("*.json")), ids=lambda p: p.name
)
def test_published_evidence_excludes_private_paths_and_credentials(path):
    leaks = PRIVATE.findall(path.read_text(encoding="utf-8"))
    assert not leaks, leaks[:3]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_every_published_attempt_resolves_to_its_manifest(receipt):
    record = _load(receipt)
    manifest = _manifest(record)
    assert manifest["id"] == record["manifest_id"] == record["outcome"]["manifest_id"]
    public = {k: v for k, v in manifest.items() if k != "published_digest"}
    assert manifest_digest(public) == manifest["published_digest"]
    assert manifest["owner_choice"]["time_model"]
    assert manifest["hermes_timeouts"]["terminal_timeout"]
    assert manifest["allowlist"] and manifest["time_params"]
    prefix = manifest["rendered_prefix"]  # measured, or not-measured with a reason
    assert prefix.get("tokens") is not None or prefix.get("reason")
    if manifest["plan"] != "calibration":
        calibration = manifest["calibration_record"]
        assert RATES <= set(calibration["rates"])
        assert calibration["checkpoint_bytes"] > 0
        assert calibration["frozen_checkpoints"] >= 0
        assert calibration["sprint_budget_s"] > 0
    assert all(session["arm"] for session in manifest["sessions"])
    outcome = record["outcome"]
    assert outcome["reason"], "every attempt keeps its stop cause"
    assert outcome["cleanup_seconds"] <= 5 and outcome["backend_listener_closed"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_launched_attempts_record_the_launch_and_admission(receipt):
    record = _load(receipt)
    launches = [e for e in record["events"] if e["kind"] == "launch"]
    if not launches:  # refused before launch: no launch to record
        return
    command = launches[0]["command"]
    assert "--slot-save-path" in command and "--predict" not in command
    admission = next(e for e in record["events"] if e["kind"] == "admission")
    assert admission["sample"]["ram_available"] and admission["cpu_needed"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_sessions_record_their_first_rendered_prefix(receipt):
    for session in _load(receipt)["sessions"]:
        first = session.get("first_request")
        if first is None:  # stopped before any request reached the wire
            continue
        assert first["input_tokens"] > 0 and len(first["prompt_sha256"]) == 64


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_every_request_names_its_missing_fields(receipt):
    for request in _load(receipt)["requests"]:
        absent = [f for f in REQUEST_FIELDS if request.get(f) is None]
        assert set(absent) <= set(request["missing"]), (request["request_id"], absent)


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_stopped_requests_keep_their_own_cause_and_elapsed_time(receipt):
    """A stopped request's cause is its own session's recorded stop, or the attempt's
    stop when its session was still running at the attempt stop."""
    record = _load(receipt)
    session_stop = {
        s["session"]: s.get("stop") for s in record["sessions"] if not s["stopped"]
    }
    for request in record["requests"]:
        if request.get("outcome") == "stopped":
            cause = session_stop.get(request["session"]) or record["outcome"]["reason"]
            assert request["stop_reason"] == cause, request["request_id"]
            assert request["seconds"] is not None


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_completed_calibrated_requests_carry_every_l1_and_m3_field(receipt):
    """AC7, L1 and M3 by presence, not by being named: every request completed after
    calibration carries every field. The one exception is ``id_slot``: b10964's
    stream does not return it. The wire reads it from ``/slots`` since the round-2
    repair, after these attempts ran, so here it must be named missing."""
    record = _load(receipt)
    if not _manifest(record)["calibration_record"]:
        return  # the calibration attempt predicts nothing yet
    for request in record["requests"]:
        if request.get("outcome") == "response_end":
            for field in REQUEST_FIELDS:
                if field == "id_slot" and request.get(field) is None:
                    assert field in request["missing"], request["request_id"]
                    continue
                assert request.get(field) is not None, (request["request_id"], field)


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_long_sessions_carry_tool_call_validity(receipt):
    """M3: every long session, finished or cut short, records each tool call's parse
    and argument validity."""
    for session in _load(receipt)["sessions"]:
        if str(session.get("workload", "")).startswith("long"):
            assert isinstance(session.get("tool_calls"), list), session["session"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_machine_time_is_recomputable_from_the_receipt(receipt):
    record = _load(receipt)
    for span in record["machine_time"]:
        ended = [
            r
            for r in record["requests"]
            if r["session"] == span["session"] and r["ended_s"] is not None
        ]
        assert span["first_request_s"] == min(r["started_s"] for r in ended)
        assert span["last_response_s"] == max(r["ended_s"] for r in ended)
        assert span["machine_time_s"] == pytest.approx(
            span["last_response_s"] - span["first_request_s"], abs=1e-3
        )


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_attempt_stopped_long_sessions_are_scored(receipt):
    """L2's "being stopped" branch: a long session an attempt stop cut short is scored
    from its fixture state."""
    record = _load(receipt)
    if not record["outcome"]["reason"].startswith("stopped:"):
        return
    started = [e for e in record["events"] if e["kind"] == "session_start"]
    if not started or not started[-1]["workload"].startswith("long"):
        return
    scored = {s["session"]: s for s in record["sessions"]}
    session = scored[started[-1]["session"]]
    assert session["verification"]["score"]["of"] == 4
    assert session["verification"]["contamination"] == []
    # An empty screen must not pass as a clean one: it saw the session's tool calls.
    screened = session["verification"]["screened"]
    if session["requests"]:
        assert screened["messages"] > 0 and screened["tool_calls"] > 0
    assert len(session["tool_calls"]) == screened["tool_calls"]
    if session.get("scored", "").startswith("at publish"):
        # Screened from the last request's conversation: complete only if that
        # request was still in flight, so no executed tool call came after it.
        own = [r for r in record["requests"] if r["session"] == session["session"]]
        last = max(own, key=lambda r: r["request_id"])
        assert last["outcome"] == "stopped", last["request_id"]
