"""The host-calibrated time model behaves as a contract between rates and windows (T-215).

H1: only qualifying samples move the rates; floors stay fixed; predictions are monotonic.
H2: the stall rule and backstops stop exactly the steps they should.
H3: every token-work window scales inversely with the host's rates.
"""

import dataclasses

import pytest

from hermes_cli.local_runtime.throughput import (
    Calibration,
    RateTracker,
    StallClock,
    TimeParams,
    floors,
    gap_window,
    load_backstop,
    predict_seconds,
    request_backstop,
    sprint_budget,
    stall_window,
    uncalibrated_stall_window,
)

PARAMS = TimeParams()
CAL = Calibration(
    prefill_tps=96.8, decode_tps=3.55, overhead_s=0.02, load_s=15.0, cli_start_s=3.0
)
PERIOD = 0.5


def test_rates_use_only_qualifying_samples():
    tracker = RateTracker(PARAMS, CAL)
    before = (tracker.prefill_tps, tracker.decode_tps)
    # A warm 1-token prefill and a 3-token decode are timing noise, not rates.
    assert not tracker.observe_prefill(1, 0.001)
    assert not tracker.observe_prefill(PARAMS.min_prefill_sample_tokens - 1, 0.01)
    assert not tracker.observe_decode(PARAMS.min_decode_sample_tokens - 1, 0.01)
    assert (tracker.prefill_tps, tracker.decode_tps) == before

    assert tracker.observe_prefill(1000, 1000 / 50.0)
    assert tracker.observe_decode(100, 100 / 2.0)
    assert tracker.prefill_tps < before[0] and tracker.decode_tps < before[1]
    # Floors come from the calibration record, never from the tracker.
    assert floors(CAL, PARAMS) == (
        CAL.prefill_tps * PARAMS.floor_fraction,
        CAL.decode_tps * PARAMS.floor_fraction,
    )


@pytest.mark.parametrize("uncached,output", [(0, 0), (100, 10), (4096, 768)])
def test_prediction_is_monotonic_in_work(uncached, output):
    base = predict_seconds(uncached, output, CAL.prefill_tps, CAL.decode_tps, 0.02)
    assert (
        predict_seconds(uncached + 1, output, CAL.prefill_tps, CAL.decode_tps, 0.02)
        >= base
    )
    assert (
        predict_seconds(uncached, output + 1, CAL.prefill_tps, CAL.decode_tps, 0.02)
        >= base
    )


def test_stall_and_backstop_semantics():
    window = stall_window("decode", CAL, PARAMS, PERIOD)
    backstop = request_backstop(CAL, PARAMS, 32768, 768)
    # Events arriving inside the window keep the step alive until the backstop.
    clock, now = StallClock(0.0, window), 0.0
    while now < backstop:
        now += window * 0.9
        assert not clock.stalled(now)
        clock.progress(now)
    assert now >= backstop  # only the backstop can end a progressing step
    # A silent step is stopped by the stall rule, just past its window.
    silent = StallClock(0.0, window)
    assert not silent.stalled(window)
    assert silent.stalled(window + 0.001)


def test_window_shapes_follow_the_floors():
    p_min, d_min = floors(CAL, PARAMS)
    batch = PARAMS.min_prefill_sample_tokens
    k = PARAMS.stall_multiple
    assert stall_window("pre_first_event", CAL, PARAMS, PERIOD) == pytest.approx(
        k * max(CAL.overhead_s, batch / p_min)
    )
    assert stall_window("prefill", CAL, PARAMS, PERIOD) == pytest.approx(
        k * batch / p_min
    )
    assert stall_window("decode", CAL, PARAMS, PERIOD) == pytest.approx(k / d_min)
    assert load_backstop(CAL, PARAMS) == pytest.approx(
        PARAMS.margin * CAL.load_s / PARAMS.floor_fraction
    )
    # During calibration the stall window is the attempt's own load time.
    assert uncalibrated_stall_window(47.0, PARAMS, PERIOD) == 47.0


def test_no_window_is_shorter_than_the_observation_floor():
    fast = dataclasses.replace(CAL, prefill_tps=1e9, decode_tps=1e9, overhead_s=0.0)
    floor_s = PARAMS.min_observation_periods * PERIOD
    for phase in ("pre_first_event", "prefill", "decode"):
        assert stall_window(phase, fast, PARAMS, PERIOD) == floor_s
    assert (
        gap_window(dataclasses.replace(fast, cli_start_s=0.0), PARAMS, PERIOD)
        == floor_s
    )
    assert uncalibrated_stall_window(0.0, PARAMS, PERIOD) == floor_s


@pytest.mark.parametrize("scale", [0.1, 2.0, 10.0])
def test_windows_scale_inversely_with_host_rate(scale):
    """Overhead terms are zeroed so every term is token work at the scaled rates."""
    base = dataclasses.replace(CAL, overhead_s=0.0, load_s=0.0, cli_start_s=0.0)
    fast = dataclasses.replace(
        base, prefill_tps=base.prefill_tps * scale, decode_tps=base.decode_tps * scale
    )
    plan = [(6, 48, 768), (1, 30, 768)]
    pairs = [
        (
            stall_window("prefill", base, PARAMS, 0.0),
            stall_window("prefill", fast, PARAMS, 0.0),
        ),
        (
            stall_window("decode", base, PARAMS, 0.0),
            stall_window("decode", fast, PARAMS, 0.0),
        ),
        (
            request_backstop(base, PARAMS, 32768, 768),
            request_backstop(fast, PARAMS, 32768, 768),
        ),
        (sprint_budget(base, PARAMS, plan), sprint_budget(fast, PARAMS, plan)),
    ]
    for slow_value, fast_value in pairs:
        assert fast_value == pytest.approx(slow_value / scale)
