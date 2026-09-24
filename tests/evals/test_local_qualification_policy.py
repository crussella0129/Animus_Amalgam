"""Sprint 2 lab contracts: frozen identity, receipts, admission, reserves and paging stops.

The page-in rule is a regression for attempts 05 and 09, where global page-in from
file/image reads stopped the owner while RAM stayed above 8.7 GiB and page-out was ~0.
"""

import copy
import json
import re
from pathlib import Path

import pytest

from evals.local_qualification.policy import (
    PagingGuard,
    admission_requirements,
    admitted,
    identity_mismatch,
    manifest_digest,
    reserve_breached,
    server_identity_mismatch,
)

ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "docs" / "sprints" / "s2" / "sprint-tests" / "qualification"
CONTINUATION_MANIFEST = (
    "df1d80e16c394a1777ee19827001fe0f116999554e857aebe2dca412db9dcdb5"
)
BRING_UP_FIELDS = {
    "schema", "source_commit", "source_dirty", "model", "backend", "placement",
    "limits", "owner_choice", "sampling", "dependencies", "rendered_prefix", "tools",
}  # fmt: skip
# Full M1 identity (interpreter, task corpus, tokenizer/template, seed) from the first
# revision that carried it; earlier bring-up manifests must never have run inference.
FULL_M1_FIELDS = BRING_UP_FIELDS | {"interpreter", "task_corpus_sha256"}
PRIVATE_PATTERNS = re.compile(
    r"[A-Za-z]:[\\/]+Users|/Users/|/home/|Bearer\s|\b[0-9a-f]{48}\b"
)


def _load(manifest_id):
    return json.loads((QUALIFICATION / "manifests" / f"{manifest_id}.json").read_text())


@pytest.fixture
def manifest():
    return _load(CONTINUATION_MANIFEST)


def _artifacts(m):
    return {"model": m["model"]["sha256"], "backend": m["backend"]["sha256"]}


def _rendered_prefix_is_honest(prefix):
    # Either an explicit pre-admission unknown with a reason, or a measured count.
    if prefix.get("status") == "not-measured":
        return bool(prefix.get("reason"))
    return prefix.get("status") == "measured" and isinstance(prefix.get("tokens"), int)


def test_published_evidence_excludes_private_paths_and_credentials():
    for path in QUALIFICATION.rglob("*.json"):
        leaks = PRIVATE_PATTERNS.findall(path.read_text(encoding="utf-8"))
        assert not leaks, (path.name, leaks[:3])


def test_every_published_attempt_resolves_to_a_valid_frozen_manifest():
    attempts = json.loads((QUALIFICATION / "attempts.json").read_text())
    previous = {"launches": 0, "requests": 0}
    for attempt in attempts:
        m = _load(attempt["manifest_id"])
        assert manifest_digest(m) == m["id"] == attempt["outcome"]["manifest_id"]
        assert BRING_UP_FIELDS <= set(m), attempt["attempt"]
        full_m1 = FULL_M1_FIELDS <= set(m) and all(
            m["model"].get(k) for k in ("tokenizer_sha256", "template_sha256")
        )
        full_m1 = full_m1 and "seed" in m["sampling"]
        if not full_m1:
            assert attempt["outcome"]["budget"]["requests"] == 0, attempt["attempt"]
        for artifact in ("model", "backend"):
            assert len(m[artifact]["sha256"]) == 64
        assert _rendered_prefix_is_honest(m["rendered_prefix"]), attempt["attempt"]
        outcome = attempt["outcome"]
        assert outcome["reason"], "every attempt keeps its stop cause"
        assert outcome["cleanup_seconds"] <= 5
        assert outcome.get("backend_listener_closed", True)
        budget = outcome["budget"]
        for counter in ("launches", "requests"):
            assert previous[counter] <= budget[counter]  # never reset across revisions
            previous[counter] = budget[counter]
        assert budget["launches"] <= m["limits"]["max_launches"]
        assert budget["requests"] <= m["limits"]["max_requests"]


@pytest.mark.parametrize(
    "change, expected",
    [
        (
            lambda m, c, a: m["limits"].__setitem__(
                "input_tokens", m["limits"]["input_tokens"] + 1
            ),
            "digest",
        ),
        (lambda m, c, a: a.__setitem__("model", "0" * 64), "model artifact"),
        (lambda m, c, a: a.__setitem__("backend", "0" * 64), "backend artifact"),
        (lambda m, c, a: c.append("f" * 40), "source revision"),
        (lambda m, c, a: m.__setitem__("source_dirty", True), "digest"),
    ],
)
def test_changed_parameter_artifact_or_source_refuses_launch(
    manifest, change, expected
):
    assert (
        identity_mismatch(
            manifest, manifest["source_commit"], _artifacts(manifest), False
        )
        is None
    )
    m, artifacts, commit = (
        copy.deepcopy(manifest),
        _artifacts(manifest),
        [manifest["source_commit"]],
    )
    change(m, commit, artifacts)
    assert expected in identity_mismatch(m, commit[-1], artifacts, False)


def test_manifest_frozen_from_a_dirty_tree_refuses_launch(manifest):
    # Re-freeze with a valid digest so the source_dirty branch, not the digest, decides.
    dirty = {**copy.deepcopy(manifest), "source_dirty": True}
    dirty["id"] = manifest_digest(dirty)
    assert "source revision" in identity_mismatch(
        dirty, dirty["source_commit"], _artifacts(dirty), False
    )


def test_uncommitted_changes_at_launch_refuse_a_valid_manifest(manifest):
    # The digest and commit still match; only the working tree changed after freezing.
    assert "source revision" in identity_mismatch(
        manifest, manifest["source_commit"], _artifacts(manifest), True
    )


def test_admission_requires_measured_capacity_on_each_device(manifest):
    placement, limits = manifest["placement"], manifest["limits"]
    cpu, gpu = admission_requirements(placement, limits)
    exact = {"ram_available": cpu, "vram_free": gpu}
    assert admitted(exact, placement, limits)
    assert not admitted({**exact, "ram_available": cpu - 1}, placement, limits)
    assert not admitted({**exact, "vram_free": gpu - 1}, placement, limits)
    assert not admitted(None, placement, limits)
    # Spare VRAM cannot pay for missing RAM: the devices are priced separately.
    assert not admitted(
        {"ram_available": cpu - 1, "vram_free": gpu + (8 << 30)}, placement, limits
    )


def test_running_attempt_stops_one_byte_below_either_reserve(manifest):
    limits = manifest["limits"]
    ram, vram = limits["ram_reserve_bytes"], limits["vram_reserve_bytes"]
    assert not reserve_breached(ram, vram, limits)
    assert reserve_breached(ram - 1, vram, limits)
    assert reserve_breached(ram, vram - 1, limits)


@pytest.mark.parametrize(
    "props_change, expected",
    [
        (lambda p: p.__setitem__("total_slots", 2), "slot"),
        (lambda p: p["default_generation_settings"].__setitem__("n_ctx", 16384), "context"),
        (lambda p: p.__setitem__("model_path", "other.gguf"), "model path"),
    ],
)  # fmt: skip
def test_ready_server_must_match_the_frozen_candidate(manifest, props_change, expected):
    context = manifest["limits"]["context"]
    props = {
        "total_slots": 1,
        "default_generation_settings": {"n_ctx": context},
        "model_path": "pilot.gguf",
    }
    assert server_identity_mismatch(props, "pilot.gguf", context, str.__eq__) is None
    props_change(props)
    assert expected in server_identity_mismatch(
        props, "pilot.gguf", context, str.__eq__
    )


def _sample(page_in=0, page_out=0):
    return {
        "hard_page_in_bytes_per_second": page_in,
        "page_out_bytes_per_second": page_out,
    }


def test_page_in_stops_only_under_ram_pressure_while_page_out_always_counts(manifest):
    limits = manifest["limits"]
    high = 1 << 30
    roomy, pressured = (
        limits["page_in_stop_below_ram_bytes"],
        limits["page_in_stop_below_ram_bytes"] - 1,
    )

    guard = PagingGuard(limits)
    assert all(
        guard.observe(_sample(page_in=high), roomy, False) is None for _ in range(10)
    )

    guard = PagingGuard(limits)
    stops = [guard.observe(_sample(page_in=high), pressured, False) for _ in range(3)]
    assert stops[:2] == [None, None] and "page-in" in stops[2]

    guard = PagingGuard(limits)
    assert all(
        guard.observe(_sample(page_in=high), pressured, True) is None for _ in range(10)
    )

    guard = PagingGuard(limits)
    guard.observe(_sample(page_in=high), pressured, False)
    guard.observe(_sample(page_in=high), pressured, False)
    guard.observe(_sample(), pressured, False)  # a quiet sample breaks the streak
    assert guard.observe(_sample(page_in=high), pressured, False) is None

    guard = PagingGuard(limits)
    stops = [guard.observe(_sample(page_out=high), roomy, True) for _ in range(3)]
    assert "page-out" in stops[2]
