"""Published Sprint 3 receipts are correlated, complete and private (T-214 V3, M4).

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


def test_sprint3_receipts_are_published():
    assert RECEIPTS, "the Sprint 3 receipts are part of the evidence handoff"


@pytest.mark.parametrize(
    "path", sorted(QUALIFICATION.rglob("*.json")), ids=lambda p: p.name
)
def test_published_evidence_excludes_private_paths_and_credentials(path):
    leaks = PRIVATE.findall(path.read_text(encoding="utf-8"))
    assert not leaks, leaks[:3]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_every_published_attempt_resolves_to_its_manifest(receipt):
    record = json.loads(receipt.read_text(encoding="utf-8"))
    manifest = json.loads(
        (QUALIFICATION / "manifests" / f"{record['manifest_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["id"] == record["manifest_id"] == record["outcome"]["manifest_id"]
    public = {k: v for k, v in manifest.items() if k != "published_digest"}
    assert manifest_digest(public) == manifest["published_digest"]
    assert manifest["owner_choice"]["time_model"]
    assert manifest["hermes_timeouts"]["terminal_timeout"]
    assert manifest["allowlist"] and manifest["time_params"]
    if manifest["plan"] != "calibration":
        assert manifest["calibration_record"]["rates"]
    assert all(session["arm"] for session in manifest["sessions"])
    outcome = record["outcome"]
    assert outcome["reason"], "every attempt keeps its stop cause"
    assert outcome["cleanup_seconds"] <= 5 and outcome["backend_listener_closed"]


@pytest.mark.parametrize("receipt", RECEIPTS, ids=lambda p: p.stem)
def test_request_receipts_name_every_missing_field(receipt):
    record = json.loads(receipt.read_text(encoding="utf-8"))
    for request in record["requests"]:
        if request.get("outcome") != "response_end":
            continue
        present = [
            k
            for k in ("input_tokens", "uncached_prompt_tokens", "decode_ms")
            if request.get(k) is not None
        ]
        # A field is either present or named missing, never silently absent.
        assert set(present) | set(request["missing"]) >= {
            "input_tokens",
            "uncached_prompt_tokens",
            "decode_ms",
        }
