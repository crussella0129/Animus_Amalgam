"""Sprint 3 lab contracts: session state, the hidden verifier, contamination and selection.

Behavior contracts over the lab's pure pieces, after operational confidence (T-214). The
lab's scripts import their siblings as top-level modules, so their directory goes first on
``sys.path``; the runner's per-file process isolation keeps that local to this file.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

LAB_DIR = Path(__file__).resolve().parents[2] / "evals" / "local_qualification"
sys.path.insert(0, str(LAB_DIR))

import driver  # noqa: E402
import policy  # noqa: E402
import prepare  # noqa: E402
import publish  # noqa: E402
import run  # noqa: E402
import screen  # noqa: E402
import verify_long  # noqa: E402

TASK_PYTHON = Path(sys.executable)


# M1 ------------------------------------------------------------------------------------


def test_arm_manifest_drives_server_flags():
    profile = {
        "context": 32768,
        "ctx_checkpoints": 4,
        "checkpoint_min_step": 512,
        "trace": True,
    }
    flags = prepare.launch_flags(profile, 5)

    def value(flag):
        return flags[flags.index(flag) + 1]

    assert value("--ctx-size") == "32768"
    assert value("--ctx-checkpoints") == "5"
    assert value("--checkpoint-min-step") == "512"
    assert value("--spec-type") == "none"
    assert value("-lv") == "4"
    assert "--predict" not in flags and "-n" not in flags
    plain = prepare.launch_flags(
        {**profile, "checkpoint_min_step": None, "trace": False}, 5
    )
    assert "--checkpoint-min-step" not in plain and "-lv" not in plain


# M2 and the C3 repair ------------------------------------------------------------------


def test_sessions_get_fresh_state_at_the_same_paths(tmp_path):
    """Hermes renders home and cwd into the system prompt (C3), so the paths repeat; the
    state does not."""
    first = run.fresh_session(tmp_path, "long:1-3")
    (first[2] / "left-behind.txt").write_text("from session 1")
    assert run.renamed(first[0], tmp_path / "session-01")
    second = run.fresh_session(tmp_path, "long:1-3")
    assert second == first
    assert not (second[2] / "left-behind.txt").exists()
    assert (second[2] / "check.py").exists()  # a pristine fixture copy
    assert (tmp_path / "session-01" / "fixture" / "left-behind.txt").exists()


def test_session_env_is_private_and_repository_free(tmp_path, monkeypatch):
    repo = LAB_DIR.parents[1]
    monkeypatch.setenv("TEMP", str(tmp_path / "owner-temp"))
    monkeypatch.setenv("SYSTEMDRIVE", "C:")
    monkeypatch.setenv("PYTHONPATH", str(repo))
    # An activated repo venv puts a repository path on the operator's PATH.
    monkeypatch.setenv(
        "PATH",
        os.pathsep.join([str(repo / ".venv" / "Scripts"), str(tmp_path / "bin")]),
    )
    home, venv = tmp_path / "home", tmp_path / "venv"
    env = run.session_env(home, venv)
    # Git Bash mounts /tmp on TEMP: a shared one carried files between sessions.
    assert env["TEMP"] == env["TMP"] == str(home / "tmp")
    assert (home / "tmp").is_dir()
    assert env["SYSTEMDRIVE"] == "C:"
    assert "PYTHONPATH" not in env
    assert not any(str(repo).lower() in v.lower() for v in env.values())
    assert str(tmp_path / "bin") in env["PATH"].split(os.pathsep)
    assert env["PATH"].split(os.pathsep)[0] == str(
        venv / ("Scripts" if os.name == "nt" else "bin")
    )


def test_session_config_holds_timers_at_or_above_the_backstop(tmp_path):
    config = run.session_config("http://127.0.0.1:1/v1", 32768, True, 940.0, tmp_path)
    assert config["agent"]["environment_probe"] is False
    assert config["model"]["reasoning_echo"] is True
    timers = [
        config["providers"]["custom"]["request_timeout_seconds"],
        config["providers"]["custom"]["stale_timeout_seconds"],
        config["agent"]["local_stream_stale_timeout"],
        config["agent"]["turn_liveness"]["timeout_s"],
    ]
    assert min(timers) >= 940.0


# Kernel cache (attempt 02 repair) ------------------------------------------------------


def test_kernel_cache_growth_is_seen_and_routed_to_the_backend(tmp_path):
    cache = run.KernelCache(tmp_path / "kernel-cache")
    assert not cache.grew()
    (cache.path / "entry").write_bytes(b"x" * 64)
    assert cache.grew() and not cache.grew()
    env = cache.env({"APPDATA": "fresh-per-attempt"})
    assert env["CUDA_CACHE_PATH"] == str(cache.path)


def _calibration_events(attempt, slow_compiled):
    rows = [
        {
            "kind": "admission",
            "cpu_needed": 16 << 30,
            "sample": {"ram_available": 20 << 30},
        },
        {"kind": "sample", "ram_available": 6 << 30},  # post-load: never the headroom
        {
            "kind": "response_end",
            "session": 1,
            "kernel_compiled": slow_compiled,
            "first_event_seconds": 0.02,
            "timings": {
                "prompt_n": 1167,
                "prompt_ms": 68_000.0,
                "predicted_n": 6,
                "predicted_ms": 7000.0,
            },
        },
        {
            "kind": "response_end",
            "session": 2,
            "kernel_compiled": False,
            "first_event_seconds": 0.02,
            "timings": {
                "prompt_n": 1167,
                "prompt_ms": 12_000.0,
                "predicted_n": 6,
                "predicted_ms": 1700.0,
            },
        },
        {
            "kind": "response_end",
            "session": 3,
            "kernel_compiled": False,
            "first_event_seconds": 0.02,
            "timings": {
                "prompt_n": 1180,
                "prompt_ms": 12_200.0,
                "predicted_n": 111,
                "predicted_ms": 31_500.0,
            },
        },
    ]
    attempt.mkdir()
    (attempt / "events.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (attempt / "backend.log").write_text(
        "created context checkpoint 1 of 4 (pos_min = 1, pos_max = 1, n_tokens = 2, size = 149.626 MiB)\n"
    )


def test_calibration_excludes_requests_that_compiled_kernels(tmp_path):
    attempt = tmp_path / "attempt"
    _calibration_events(attempt, slow_compiled=True)
    run.write_calibration(
        tmp_path,
        attempt,
        9.0,
        45.0,
        [{"cli_start_seconds": 3.0}],
        run.TimeParams(),
        lambda *a, **k: None,
    )
    record = json.loads((tmp_path / "calibration.json").read_text())
    # Only the two warm samples count: compile time is not throughput.
    assert record["rates"]["prefill_tps"] == pytest.approx(
        (1167 / 12.0 + 1180 / 12.2) / 2
    )


def test_checkpoint_headroom_comes_from_the_admission_receipt(tmp_path):
    """Attempt 04 was handed the post-load sample, read negative headroom and froze 0."""
    attempt = tmp_path / "attempt"
    _calibration_events(attempt, slow_compiled=False)
    run.write_calibration(
        tmp_path,
        attempt,
        9.0,
        45.0,
        [{"cli_start_seconds": 3.0}],
        run.TimeParams(),
        lambda *a, **k: None,
    )
    record = json.loads((tmp_path / "calibration.json").read_text())
    assert record["frozen_checkpoints"] == min(
        32, (4 << 30) // int(149.626 * (1 << 20))
    )


# L2 ------------------------------------------------------------------------------------


def _apply_reference(fixture, turns):
    from tools.environments.local import _find_bash, _git_bash_bin_dirs

    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([
        str(TASK_PYTHON.parent),
        *_git_bash_bin_dirs(),
        env["PATH"],
    ])
    reference = json.loads((verify_long.TASK / "reference.json").read_text())
    for steps in reference["turns"][:turns]:
        for step in steps:
            if "command" in step:
                subprocess.run(
                    [_find_bash(), "-c", step["command"]],
                    cwd=fixture,
                    env=env,
                    check=False,
                    capture_output=True,
                )


@pytest.mark.parametrize("turns,expected", [(0, 0), (3, 1), (8, 4)])
def test_verify_scores_fixture_state(tmp_path, turns, expected):
    fixture = tmp_path / "fixture"
    shutil.copytree(verify_long.TASK / "fixture", fixture)
    _apply_reference(fixture, turns)
    score = verify_long.score(fixture, TASK_PYTHON)
    assert score["passed"] == expected and score["of"] == 4


# L4 ------------------------------------------------------------------------------------


def _conversation(*commands, workdir=None):
    return [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "terminal",
                        "arguments": json.dumps({
                            "command": c,
                            **({"workdir": workdir} if workdir else {}),
                        }),
                    }
                }
            ],
        }
        for c in commands
    ]


@pytest.fixture
def session(tmp_path):
    live = tmp_path / "attempt" / "live"
    (live / "fixture").mkdir(parents=True)
    (live / "home" / "tmp").mkdir(parents=True)
    git_bin = tmp_path / "Git" / "usr" / "bin"
    git_bin.mkdir(parents=True)
    allow = [str(tmp_path / "venv"), str(git_bin), str(live / "home")]
    return live / "fixture", allow, live / "home" / "tmp"


@pytest.mark.parametrize(
    "command",
    [
        "cat ../../secret",
        "ls /c/Users/someone/repo",
        "cat $HOME/x",
        "ls ~",
        "cd .. && ls",
        r"type C:\Users\someone\repo\AGENTS.md",
        "python -c \"open('C:\\\\Users\\\\someone\\\\x')\"",
    ],
)
def test_contamination_flags_paths_outside_the_fixture(session, command):
    fixture, allow, temp = session
    assert verify_long.contamination(_conversation(command), fixture, allow, temp)


@pytest.mark.parametrize(
    "command",
    [
        "cat inventory/models.py",
        "find . -type f -not -path './.git/*'",
        "find . -type f -not -path '*/.git/*'",
        'for f in inventory/*; do head -5 "$f"; done',
        "echo hi > /dev/null",
        'python -c "print(25 / 100)"',
        "cat > /tmp/patch.py <<'EOF'\nprint('x')\nEOF",
    ],
)
def test_contamination_spares_fixture_and_session_paths(session, command):
    fixture, allow, temp = session
    assert verify_long.contamination(_conversation(command), fixture, allow, temp) == []


def test_reference_path_is_clean(session):
    fixture, allow, temp = session
    reference = [m for m in verify_long.reference_messages() if m.get("tool_calls")]
    assert verify_long.contamination(reference, fixture, allow, temp) == []


def test_tmp_follows_the_session_temp(session, tmp_path):
    """A shared TEMP leaks between sessions; a private one is the session's own."""
    fixture, allow, private = session
    write = _conversation("echo x > /tmp/helper.txt")
    assert verify_long.contamination(write, fixture, allow, private) == []
    assert verify_long.contamination(write, fixture, allow, tmp_path / "owner-temp")


# S2 ------------------------------------------------------------------------------------


def _candidate(arm, verified, machine_s, decoded, selectable=True):
    return {
        "arm": arm,
        "verified": verified,
        "machine_s": machine_s,
        "decoded": decoded,
        "selectable": selectable,
    }


def test_screen_ranking_rule():
    ordered, inconclusive = screen.rank([
        _candidate("a", 1, 300, 900),
        _candidate("b", 2, 500, 2000),
        _candidate("c", 1, 250, 950),
        _candidate("probe", 4, 10, 10, selectable=False),
    ])
    assert [c["arm"] for c in ordered] == ["b", "c", "a"] and not inconclusive
    tie = screen.rank([_candidate("x", 1, 300, 900), _candidate("y", 1, 300, 800)])[0]
    assert [c["arm"] for c in tie] == ["y", "x"]
    zero, inconclusive = screen.rank([
        _candidate("p", 0, 400, 1),
        _candidate("q", 0, 200, 9),
    ])
    assert [c["arm"] for c in zero] == ["q", "p"] and inconclusive


def test_contaminated_twice_is_a_failure_and_once_is_excluded():
    clean = {"session": 2, "contamination": [], "verified": 1}
    flagged = {"session": 1, "contamination": [{"token": "/x"}], "verified": 1}
    assert screen.pick([flagged, clean]) is clean
    failed = screen.pick([flagged, {**flagged, "session": 2}])
    assert failed["verified"] == 0 and failed["failed_by_contamination"]


# M1 against the published evidence -----------------------------------------------------

QUALIFICATION = (
    LAB_DIR.parents[1] / "docs" / "sprints" / "s3" / "sprint-tests" / "qualification"
)


def test_launch_flags_reproduce_the_published_full_run_argv():
    receipt = json.loads(
        (QUALIFICATION / "attempt-13-R2.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (QUALIFICATION / "manifests" / f"{receipt['manifest_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    profile = json.loads((LAB_DIR / "arms.json").read_text(encoding="utf-8"))[
        "launch_profiles"
    ]["sprint"]
    checkpoints = manifest["calibration_record"]["frozen_checkpoints"]
    assert prepare.launch_flags(profile, checkpoints) == manifest["launch"]["flags"]


def test_changing_a_launch_flag_changes_the_manifest_identity():
    receipt = json.loads(
        (QUALIFICATION / "attempt-13-R2.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (QUALIFICATION / "manifests" / f"{receipt['manifest_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    changed = json.loads(json.dumps(manifest))
    changed["launch"]["flags"][
        changed["launch"]["flags"].index("--ctx-checkpoints") + 1
    ] = "6"
    assert policy.manifest_digest(changed) != policy.manifest_digest(manifest)


# T1, T3: every session window comes from the throughput model ----------------------------


def test_session_windows_scale_with_the_host_rates():
    base = run.Calibration(
        prefill_tps=96.8, decode_tps=3.55, overhead_s=0.0, load_s=15.0, cli_start_s=3.0
    )
    fast = run.Calibration(
        prefill_tps=193.6, decode_tps=7.1, overhead_s=0.0, load_s=15.0, cli_start_s=3.0
    )
    slow_w = run.session_windows(base, run.TimeParams(), 15.0, 32768, 768, 0.0)
    fast_w = run.session_windows(fast, run.TimeParams(), 15.0, 32768, 768, 0.0)
    for phase in ("pre_first_event", "prefill", "decode"):
        assert fast_w["stall"][phase] == pytest.approx(slow_w["stall"][phase] / 2)
    for key in ("request_backstop", "hermes_timer", "settle", "probe"):
        assert fast_w[key] == pytest.approx(slow_w[key] / 2)
    # The gap window is CLI start-up work, measured on the host, not token work.
    assert fast_w["gap"] == slow_w["gap"]


def test_uncalibrated_windows_come_from_the_measured_load():
    params = run.TimeParams()
    short = run.session_windows(None, params, 10.0, 32768, 512, 0.5)
    long = run.session_windows(None, params, 20.0, 32768, 512, 0.5)
    assert long["stall"]["prefill"] == 2 * short["stall"]["prefill"] == 20.0
    assert long["hermes_timer"] == 2 * short["hermes_timer"]
    assert short["request_backstop"] is None  # no backstop before calibration
    tiny = run.session_windows(None, params, 0.0, 32768, 512, 0.5)
    assert tiny["stall"]["decode"] == params.min_observation_periods * 0.5


# T2: stop predicates fire exactly at their boundary --------------------------------------


def test_stop_predicates_fire_at_boundary():
    assert not policy.telemetry_stale(10.0, 13.0, 1.0)
    assert policy.telemetry_stale(10.0, 13.001, 1.0)
    assert not policy.supervisor_lagged(10.0, 12.0, 1.0)
    assert policy.supervisor_lagged(10.0, 12.001, 1.0)
    limits = {"max_launches": 12, "max_requests": 400}
    assert policy.launch_allowed(11, limits) and not policy.launch_allowed(12, limits)
    assert policy.request_allowed(399, limits) and not policy.request_allowed(
        400, limits
    )
    assert not policy.budget_exceeded(100.0, 100.0) and policy.budget_exceeded(
        100.001, 100.0
    )
    assert not policy.budget_exceeded(1e9, None)  # calibration has no budget yet
    quiet = {"vram_used": 5, "ram_available": 9}
    assert not policy.load_progressed(quiet, dict(quiet), log_grew=False)
    assert policy.load_progressed(
        quiet, {"vram_used": 6, "ram_available": 9}, log_grew=False
    )
    assert policy.load_progressed(
        quiet, {"vram_used": 5, "ram_available": 8}, log_grew=False
    )
    assert policy.load_progressed(quiet, dict(quiet), log_grew=True)


# Supervisor waits and the per-session erase (C-008) ---------------------------------------


def test_every_supervisor_wait_keeps_observing():
    """Attempt 02: waits that skipped observe() froze the guards and tripped the lag stop."""
    ticks, ready_after = [], 3
    assert run.wait_while(
        lambda: len(ticks) < ready_after, 5.0, lambda: ticks.append(1), 0.01
    )
    assert len(ticks) == ready_after
    observed = []
    assert not run.wait_while(lambda: True, 2.0, lambda: observed.append(1), 0.01)
    assert len(observed) > 1  # the guards kept running until the timeout


def test_only_the_planned_session_keeps_its_slot():
    """Attempt 04: a blanket erase before every session made C3 unmeasurable. The
    decision is ``run.erases_slot``, the one ``run_session`` makes."""
    arms = json.loads((LAB_DIR / "arms.json").read_text(encoding="utf-8"))
    for plan_name, kept in (("calibration", 2), ("screen", 2), ("R1", None)):
        sessions = prepare.resolve_sessions(arms, arms["attempt_plans"][plan_name])
        erased = [run.erases_slot(i, spec) for i, spec in enumerate(sessions, start=1)]
        assert erased == [i > 1 and i != kept for i in range(1, len(sessions) + 1)]


# C2 fails closed (C-009) ------------------------------------------------------------------


def test_calibration_fails_closed_on_a_missing_field(tmp_path):
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "events.jsonl").write_text(
        json.dumps({
            "kind": "response_end",
            "first_event_seconds": 0.02,
            "timings": {
                "prompt_n": 1167,
                "prompt_ms": 12_000.0,
                "predicted_n": 6,
                "predicted_ms": 1700.0,
            },
        })
        + "\n"
    )
    (attempt / "backend.log").write_text("no checkpoint was created\n")
    failures = []
    with pytest.raises(RuntimeError, match="fail closed"):
        run.write_calibration(
            tmp_path,
            attempt,
            9.0,
            45.0,
            [{"cli_start_seconds": 3.0}],
            run.TimeParams(),
            lambda kind, **data: failures.append((kind, data)),
        )
    assert failures[0][0] == "calibration_failed"
    assert {"decode", "checkpoint_size", "admission"} <= set(failures[0][1]["missing"])
    assert not (tmp_path / "calibration.json").exists()


def test_later_plans_refuse_to_freeze_without_a_calibration_record(
    tmp_path, monkeypatch
):
    lab = tmp_path / "lab"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare.py",
            "--model",
            str(tmp_path / "m.gguf"),
            "--server",
            str(tmp_path / "s.exe"),
            "--lab",
            str(lab),
            "--plan",
            "R0",
        ],
    )
    with pytest.raises(SystemExit, match="calibration plan first"):
        prepare.main()
    assert not (lab / "manifests").exists()


# L4 allowlist and M3 tool-call validity (C-012, C-004) ------------------------------------


def test_contamination_spares_the_allowlist(session, tmp_path):
    fixture, allow, temp = session
    venv_python = Path(allow[0]) / "Scripts" / "python.exe"
    git_env = Path(allow[1]) / "env"
    spared = _conversation(
        f"{venv_python} check.py", f"{git_env.as_posix()} python check.py"
    )
    assert verify_long.contamination(spared, fixture, allow, temp) == []


def test_tool_call_validity_names_bad_arguments_and_unknown_tools():
    conversation = [
        {
            "tool_calls": [
                {
                    "function": {
                        "name": "terminal",
                        "arguments": json.dumps({"command": "ls"}),
                    }
                },
                {"function": {"name": "terminal", "arguments": "{not json"}},
                {"function": {"name": "browser", "arguments": "{}"}},
            ]
        }
    ]
    assert driver.tool_call_validity(conversation, {"terminal"}) == [
        {"name": "terminal", "arguments_valid": True, "known_tool": True},
        {"name": "terminal", "arguments_valid": False, "known_tool": True},
        {"name": "browser", "arguments_valid": True, "known_tool": False},
    ]


# Stop paths (critique round 2) ------------------------------------------------------------


def test_stopped_request_keeps_its_cause_timing_and_predictions():
    active = {
        "request_id": 7,
        "started": 100.0,
        "predicted_initial": 50.0,
        "predicted_rearmed": 40.0,
    }
    assert run.stopped_request(active, "stopped: RAM reserve", 130.5) == {
        "request_id": 7,
        "reason": "stopped: RAM reserve",
        "seconds": 30.5,
        "predicted_initial_seconds": 50.0,
        "predicted_rearmed_seconds": 40.0,
    }


def test_request_extrema_are_recorded_when_a_guard_stops_the_loop():
    """A guard raising inside observe() used to drop the in-flight request's extrema."""
    recorded = []
    extrema = run.RequestExtrema(lambda kind, **data: recorded.append((kind, data)))
    sample = {
        "ram_available": 6 << 30,
        "vram_free": 2 << 30,
        "hard_page_in_bytes_per_second": 1e6,
        "page_out_bytes_per_second": 0.0,
        "gpu_temperature": 55,
    }
    with pytest.raises(RuntimeError):
        try:
            extrema.observe(9, sample)
            extrema.observe(9, {**sample, "ram_available": 5 << 30})
            raise RuntimeError("RAM or VRAM reserve breached")
        finally:
            extrema.close()
    assert recorded == [
        (
            "request_resources",
            {
                "request_id": 9,
                "ram_available_min": 5 << 30,
                "vram_free_min": 2 << 30,
                "page_in_max": 1e6,
                "page_out_max": 0.0,
                "gpu_temperature_max": 55,
            },
        )
    ]


def test_a_cut_short_session_is_scored_from_its_fixture(tmp_path, session):
    fixture = tmp_path / "live" / "fixture"
    shutil.copytree(verify_long.TASK / "fixture", fixture)
    _apply_reference(fixture, 3)

    class Wire:
        session = {"requests": 6}

    current = {"index": 2, "workload": "long:all", "fixture": fixture}
    stopped = run.stopped_session(
        current, Wire(), TASK_PYTHON.parent.parent, session[1]
    )
    assert stopped["session"] == 2 and stopped["requests"] == 6
    assert stopped["verification"]["score"]["passed"] == 1
    assert (
        run.stopped_session(None, Wire(), TASK_PYTHON.parent.parent, session[1]) is None
    )


def _attempt(
    tmp_path, events, reason="stopped: RuntimeError: RAM or VRAM reserve breached"
):
    attempt = tmp_path / "attempt-01-x"
    attempt.mkdir()
    (attempt / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )
    (attempt / "outcome.json").write_text(json.dumps({"reason": reason}))
    (attempt / "manifest.json").write_text(json.dumps({"id": "abc", "plan": "R2"}))
    return attempt


REQUEST = {
    "kind": "request",
    "at": 10.0,
    "request_id": 1,
    "session": 1,
    "input_tokens": 99,
    "prompt_sha256": "p",
    "system_sha256": "s",
    "tools_sha256": "t",
    "continuation_of_length_finish": False,
    "predicted_initial_seconds": 50.0,
}
STOPPED = {
    "kind": "request_stopped",
    "at": 40.0,
    "request_id": 1,
    "reason": "stopped: RAM",
    "seconds": 30.0,
    "predicted_initial_seconds": 50.0,
    "predicted_rearmed_seconds": 45.0,
}


@pytest.mark.parametrize(
    "after",
    [
        {
            "kind": "wire_failure",
            "at": 41.0,
            "request_id": 1,
            "error": "ConnectionAbortedError",
        },
        {"kind": "response_cancelled", "at": 41.0, "request_id": 1, "seconds": 31.0},
    ],
)
def test_a_stopped_request_stays_stopped_whatever_lands_after(tmp_path, after):
    resources = {
        "kind": "request_resources",
        "at": 39.0,
        "request_id": 1,
        "ram_available_min": 5,
    }
    record = publish.receipts(_attempt(tmp_path, [REQUEST, resources, STOPPED, after]))
    (request,) = record["requests"]
    assert request["outcome"] == "stopped" and request["stop_reason"] == "stopped: RAM"
    assert request["seconds"] == 30.0  # the stop's own timing, not the later record's
    assert request["predicted_initial_seconds"] == 50.0
    assert request["predicted_rearmed_seconds"] == 45.0
    assert request["resources"] == {"ram_available_min": 5}
    assert record["machine_time"] == [
        {
            "session": 1,
            "first_request_s": 0.0,
            "last_response_s": 30.0,
            "machine_time_s": 30.0,
        }
    ]


def test_publish_scores_a_cut_short_session_from_its_fixture(tmp_path):
    started = {"kind": "session_start", "at": 5.0, "session": 1, "workload": "long:all"}
    attempt = _attempt(tmp_path, [started, REQUEST, STOPPED])
    shutil.copytree(verify_long.TASK / "fixture", attempt / "live" / "fixture")
    record = publish.receipts(attempt, TASK_PYTHON)
    (session,) = record["sessions"]
    assert session["stopped"] and session["requests"] == 1
    assert session["verification"]["score"]["passed"] == 0
