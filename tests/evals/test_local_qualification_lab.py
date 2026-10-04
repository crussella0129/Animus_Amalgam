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

import prepare  # noqa: E402
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
