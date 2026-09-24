"""Sprint 2 lab contracts: frozen identity, per-device admission and paging stops.

The page-in rule is a regression for attempts 05 and 09, where global page-in from
file/image reads stopped the owner while RAM stayed above 8.7 GiB and page-out was ~0.
"""

import copy
import json
from pathlib import Path

import pytest

from evals.local_qualification.policy import (
    PagingGuard,
    admission_requirements,
    admitted,
    identity_mismatch,
    manifest_digest,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (
    ROOT / "docs" / "sprints" / "s2" / "sprint-tests" / "qualification" / "manifests"
)


@pytest.fixture
def manifest():
    frozen = [
        m
        for m in (json.loads(p.read_text()) for p in sorted(MANIFESTS.glob("*.json")))
        if "page_in_stop_below_ram_bytes" in m["limits"]
    ]
    assert frozen, "expected a published manifest with the continuation limits"
    return frozen[0]


def _artifacts(m):
    return {"model": m["model"]["sha256"], "backend": m["backend"]["sha256"]}


def test_published_manifest_identity_resolves_to_its_digest(manifest):
    assert manifest_digest(manifest) == manifest["id"]
    assert (
        identity_mismatch(manifest, manifest["source_commit"], _artifacts(manifest))
        is None
    )


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
    ],
)
def test_changed_parameter_artifact_or_source_refuses_launch(
    manifest, change, expected
):
    m, artifacts, commit = (
        copy.deepcopy(manifest),
        _artifacts(manifest),
        [manifest["source_commit"]],
    )
    change(m, commit, artifacts)
    assert expected in identity_mismatch(m, commit[-1], artifacts)


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
