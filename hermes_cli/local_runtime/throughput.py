"""Host-calibrated throughput model and time rules for a local llama.cpp route.

Every time limit derives from rates measured on the host that is running: prefill and decode
tokens/s, request overhead, model-load and CLI start-up time. The same policy therefore serves
hosts of any speed. The only parameters are dimensionless ratios and token-count thresholds.

Enforcement is a stall rule (no progress within a window scaled to the calibrated floor rates)
plus a worst-case backstop (the most work a step can contain at the floors, times the margin).
Predictions are recorded for accuracy but never enforced, so a slow step that keeps making
progress is only ever stopped by its backstop. Pure: no I/O, clocks are passed in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TimeParams:
    margin: float = 2.0  # m: multiplies worst-case work
    stall_multiple: float = 20.0  # k: expected progress intervals before a stall
    floor_fraction: float = 0.5  # f: floors are this share of calibrated rates
    planning_uncached_tokens: int = 2048  # U: per-request allowance for budgets
    min_prefill_sample_tokens: int = (
        256  # one full server batch; smaller samples are noise
    )
    min_decode_sample_tokens: int = 16
    rate_smoothing: float = 0.3  # weight of each new qualifying sample
    min_observation_periods: int = 4  # no window shorter than this many polls


@dataclass(frozen=True)
class Calibration:
    """Rates and durations measured on this host by a calibration launch."""

    prefill_tps: float
    decode_tps: float
    overhead_s: float
    load_s: float
    cli_start_s: float
    hash_s: float = 0.0


def floors(cal: Calibration, params: TimeParams) -> tuple[float, float]:
    """(prefill, decode) floor rates, fixed for the calibration's lifetime."""
    return (
        cal.prefill_tps * params.floor_fraction,
        cal.decode_tps * params.floor_fraction,
    )


class RateTracker:
    """Smoothed rates from qualifying samples only; a 1-token warm prefill never sets a rate."""

    def __init__(self, params: TimeParams, cal: Calibration | None = None):
        self.params = params
        self.prefill_tps = cal.prefill_tps if cal else None
        self.decode_tps = cal.decode_tps if cal else None

    def _blend(self, current: float | None, sample: float) -> float:
        if current is None:
            return sample
        w = self.params.rate_smoothing
        return (1 - w) * current + w * sample

    def observe_prefill(self, tokens: int, seconds: float) -> bool:
        if tokens < self.params.min_prefill_sample_tokens or seconds <= 0:
            return False
        self.prefill_tps = self._blend(self.prefill_tps, tokens / seconds)
        return True

    def observe_decode(self, tokens: int, seconds: float) -> bool:
        if tokens < self.params.min_decode_sample_tokens or seconds <= 0:
            return False
        self.decode_tps = self._blend(self.decode_tps, tokens / seconds)
        return True


def predict_seconds(
    uncached_tokens: int,
    output_tokens: int,
    prefill_tps: float,
    decode_tps: float,
    overhead_s: float,
) -> float:
    """Expected time for one request; recorded, never enforced."""
    return overhead_s + uncached_tokens / prefill_tps + output_tokens / decode_tps


def stall_window(
    phase: str,
    cal: Calibration,
    params: TimeParams,
    observation_period_s: float,
) -> float:
    """Seconds without any progress signal before a step counts as stalled.

    ``phase`` is ``pre_first_event`` (send until the first progress event: template, tokenize
    and checkpoint restore grow with the prompt), ``prefill`` or ``decode``.
    """
    p_min, d_min = floors(cal, params)
    batch = params.min_prefill_sample_tokens
    interval = {
        "pre_first_event": max(cal.overhead_s, batch / p_min),
        "prefill": batch / p_min,
        "decode": 1 / d_min,
    }[phase]
    return max(
        params.stall_multiple * interval,
        params.min_observation_periods * observation_period_s,
    )


def uncalibrated_stall_window(
    load_s: float, params: TimeParams, observation_period_s: float
) -> float:
    """Stall window during the calibration attempt itself: its own measured load time."""
    return max(load_s, params.min_observation_periods * observation_period_s)


def request_backstop(
    cal: Calibration, params: TimeParams, context_tokens: int, output_cap: int
) -> float:
    """Worst-case request: a full-context reprocess plus the full output cap at the floors."""
    p_min, d_min = floors(cal, params)
    return params.margin * (
        cal.overhead_s + context_tokens / p_min + output_cap / d_min
    )


def load_backstop(cal: Calibration, params: TimeParams) -> float:
    return params.margin * cal.load_s / params.floor_fraction


def gap_window(
    cal: Calibration, params: TimeParams, observation_period_s: float
) -> float:
    """Idle time allowed between requests (no CLI-tree CPU or output) before a stall."""
    return max(
        params.stall_multiple * cal.cli_start_s,
        params.min_observation_periods * observation_period_s,
    )


def sprint_budget(
    cal: Calibration,
    params: TimeParams,
    attempts: Iterable[tuple[int, int, int]],
) -> float:
    """Charged-time budget for planned ``(sessions, requests, output_cap)`` attempts."""
    per_attempt = (
        cal.hash_s
        + cal.load_s
        + sessions * cal.cli_start_s
        + requests
        * predict_seconds(
            params.planning_uncached_tokens,
            output_cap,
            cal.prefill_tps,
            cal.decode_tps,
            cal.overhead_s,
        )
        for sessions, requests, output_cap in attempts
    )
    return params.margin * sum(per_attempt)


class StallClock:
    """Tracks the last progress signal for one step; the caller supplies monotonic time."""

    def __init__(self, started: float, window: float):
        self.last_progress = started
        self.window = window

    def progress(self, now: float, window: float | None = None) -> None:
        self.last_progress = now
        if window is not None:
            self.window = window

    def stalled(self, now: float) -> bool:
        return now - self.last_progress > self.window
