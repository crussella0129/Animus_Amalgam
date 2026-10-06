"""Published Sprint 3 receipts are correlated, complete and private (T-214 V3, M3, M4, L1).

Every attempt receipt resolves to its published manifest. A manifest keeps the ``id`` the
lab verified over the private original at launch; sanitizing local paths changes the
bytes, so ``published_digest`` covers the public copy instead.
"""

import json
from pathlib import Path
import re

import pytest

from evals.local_qualification.policy import manifest_digest, supervisor_lagged
from hermes_cli.local_runtime.throughput import (
    Calibration,
    TimeParams,
    request_backstop,
)

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
    "decoded_tokens",
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
RATES = {"prefill_tps", "decode_tps", "overhead_s", "load_s", "cli_start_s"}
# Fields the live runs' wire could not record: b10964 streams no id_slot (correlated
# from /slots since round 2), and tool-call tokens are counted since round 5. Only
# receipts from schema-2 manifests, the live runs, may name them missing.
LATER_FIELDS = {"id_slot", "tool_call_tokens"}
REPAIRED_SCHEMA = 3
TELEMETRY_PERIOD = 1.0  # the retained telemetry cadence (lab README)
AC1_REQUESTS = 20  # INT-0007 AC1


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest(record):
    return _load(QUALIFICATION / "manifests" / f"{record['manifest_id']}.json")


def _before_repair(record):
    return _manifest(record)["schema"] < REPAIRED_SCHEMA


def _cut_calls(record, session):
    """Tool calls delivered in responses cut at the output cap."""
    return sum(
        r["tool_calls"]
        for r in record["requests"]
        if r["session"] == session
        and r.get("finish_reason") == "length"
        and r.get("tool_calls")
    )


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
                if (
                    field in LATER_FIELDS
                    and request.get(field) is None
                    and _before_repair(record)
                ):
                    assert field in request["missing"], request["request_id"]
                    continue
                assert request.get(field) is not None, (request["request_id"], field)


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_long_sessions_validate_every_delivered_tool_call(receipt):
    """M3: every long session, finished or cut short, records each delivered tool
    call's parse and argument validity, or names the shortfall. Only a call cut at
    the output cap can be missing from Hermes's history, the pre-round-5 source."""
    record = _load(receipt)
    for session in record["sessions"]:
        if not str(session.get("workload", "")).startswith("long"):
            continue
        own = [r for r in record["requests"] if r["session"] == session["session"]]
        delivered = sum(r.get("tool_calls") or 0 for r in own)
        unvalidated = session.get("unvalidated_tool_calls", 0)
        assert len(session["tool_calls"]) + unvalidated == delivered
        # Since the repair the wire validates every delivered call itself.
        allowed = (
            _cut_calls(record, session["session"]) if _before_repair(record) else 0
        )
        assert 0 <= unvalidated <= allowed, session["session"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_the_token_split_accounts_for_decoded_output(receipt):
    """L1: reasoning, visible content and tool-call output never exceed what was
    decoded, and the remainder is published."""
    for request in _load(receipt)["requests"]:
        parts = [
            request.get(k)
            for k in ("decoded_tokens", "reasoning_tokens", "visible_tokens")
        ]
        if None in parts:
            continue
        counted = parts[1] + parts[2] + (request.get("tool_call_tokens") or 0)
        assert request["unsplit_decoded_tokens"] == parts[0] - counted >= 0


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_supervisor_lag_is_recorded_and_stops_only_past_two_periods(receipt):
    """M3: maximum supervisor lag is the host-responsiveness proxy; past two
    telemetry periods it stops the attempt, and only then."""
    outcome = _load(receipt)["outcome"]
    lag = outcome["max_supervisor_lag_seconds"]
    assert lag >= 0
    assert supervisor_lagged(0.0, lag, TELEMETRY_PERIOD) == (
        "scheduler lag" in outcome["reason"]
    )


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_long_all_sessions_record_ac1_coverage(receipt):
    """L2: every long:all session, completed or stopped, records AC1 coverage."""
    for session in _load(receipt)["sessions"]:
        if session.get("workload") == "long:all":
            covered = session["requests"] >= AC1_REQUESTS
            assert session["ac1_request_coverage"] is covered, session["session"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_hermes_timers_hold_at_or_above_each_sessions_backstop(receipt):
    """M2: after calibration, every session's Hermes timers, and the manifest's
    declared ones, sit at or above the request backstop for its own output cap."""
    record = _load(receipt)
    manifest = _manifest(record)
    calibration = manifest["calibration_record"]
    if not calibration:
        return  # during calibration the timers follow the measured load time
    cal = Calibration(**{k: calibration["rates"][k] for k in RATES})
    params = TimeParams(**manifest["time_params"])
    context = manifest["launch"]["context"]
    caps = {s["arm_name"]: s["arm"]["output_cap"] for s in manifest["sessions"]}
    declared = [
        v
        for k, v in manifest["hermes_timeouts"].items()
        if k not in ("note", "terminal_timeout")  # a tool bound, not a request's
    ]
    assert min(declared) >= request_backstop(cal, params, context, max(caps.values()))
    for start in (e for e in record["events"] if e["kind"] == "session_start"):
        backstop = request_backstop(cal, params, context, caps[start["arm"]])
        assert start["hermes_timer_seconds"] >= backstop, start["session"]


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
    # Validity covers every delivered call; the screened history lacks only calls
    # Hermes dropped, which were cut at the output cap.
    dropped = len(session["tool_calls"]) - screened["tool_calls"]
    assert 0 <= dropped <= _cut_calls(record, session["session"])
    if session.get("scored", "").startswith("at publish"):
        # Screened from the last request's conversation: complete only if that
        # request was still in flight, so no executed tool call came after it.
        own = [r for r in record["requests"] if r["session"] == session["session"]]
        last = max(own, key=lambda r: r["request_id"])
        assert last["outcome"] == "stopped", last["request_id"]
