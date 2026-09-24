"""Pure identity, admission and stop decisions for the operational lab; no I/O."""

from __future__ import annotations

import hashlib
import json

PAGING_RATE_LIMIT = 64 << 20
PAGING_STREAK_LIMIT = 3


def manifest_digest(manifest: dict) -> str:
    identity = {k: v for k, v in manifest.items() if k != "id"}
    return hashlib.sha256(
        json.dumps(
            identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def identity_mismatch(
    manifest: dict,
    source_commit: str,
    artifact_sha256: dict[str, str],
    source_dirty_now: bool,
) -> str | None:
    if manifest_digest(manifest) != manifest["id"]:
        return "candidate manifest digest mismatch"
    if (
        manifest["source_dirty"]
        or source_dirty_now
        or source_commit != manifest["source_commit"]
    ):
        return "source revision differs from frozen candidate"
    for artifact in ("model", "backend"):
        if artifact_sha256.get(artifact) != manifest[artifact]["sha256"]:
            return f"{artifact} artifact differs from frozen candidate"
    return None


def server_identity_mismatch(
    props: dict, model_path: str, context: int, same_file
) -> str | None:
    """Refuse generation unless the ready server is the frozen one-slot
    candidate. ``same_file`` compares paths so tests need no real files."""
    if (
        props["total_slots"] != 1
        or props["default_generation_settings"]["n_ctx"] != context
    ):
        return "server context/slot identity mismatch"
    if not same_file(props["model_path"], model_path):
        return "server model path mismatch"
    return None


def admission_requirements(placement: dict, limits: dict) -> tuple[int, int]:
    cpu = (
        placement["cpu_weight_bytes"]
        + placement["cpu_overhead_bytes"]
        + limits["ram_reserve_bytes"]
    )
    gpu = (
        placement["gpu_weight_bytes"]
        + placement["context_bytes_upper"]
        + placement["gpu_overhead_bytes"]
        + limits["vram_reserve_bytes"]
    )
    return cpu, gpu


def admitted(sample: dict | None, placement: dict, limits: dict) -> bool:
    cpu, gpu = admission_requirements(placement, limits)
    return (
        sample is not None
        and sample["ram_available"] >= cpu
        and sample["vram_free"] >= gpu
    )


def reserve_breached(ram_available: int, vram_free: int, limits: dict) -> bool:
    return (
        ram_available < limits["ram_reserve_bytes"]
        or vram_free < limits["vram_reserve_bytes"]
    )


class PagingGuard:
    """Consecutive-sample paging stops. Global page-in also counts file and
    image reads, so after load it only stops the owner under RAM pressure;
    page-out always counts."""

    def __init__(self, limits: dict):
        self.pressure_below = limits["page_in_stop_below_ram_bytes"]
        self.page_in_streak = 0
        self.page_out_streak = 0

    def observe(
        self, sample: dict, ram_available: int, load_allowance: bool
    ) -> str | None:
        ram_pressure = ram_available < self.pressure_below
        high_in = sample["hard_page_in_bytes_per_second"] > PAGING_RATE_LIMIT
        high_out = sample["page_out_bytes_per_second"] > PAGING_RATE_LIMIT
        counts_in = high_in and ram_pressure and not load_allowance
        self.page_in_streak = self.page_in_streak + 1 if counts_in else 0
        self.page_out_streak = self.page_out_streak + 1 if high_out else 0
        if self.page_in_streak >= PAGING_STREAK_LIMIT:
            return "hard page-in rate breached"
        if self.page_out_streak >= PAGING_STREAK_LIMIT:
            return "page-out rate breached"
        return None
