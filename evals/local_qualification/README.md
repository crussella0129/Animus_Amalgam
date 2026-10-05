# Local Hermes operational lab

The lab operates the real Hermes CLI against a local llama.cpp backend in
disposable homes and fixtures. Formal unit and integration verification
follows operational confidence. The locked sprint plans define the approved
limits and task sequence.

## Layout

- **`arms.json`** — time-model parameters, sampling sets, session arms
  (thinking mode, output cap, reasoning budget, sampling), launch profiles,
  attempt plans and the screen winners.
- **`prepare.py`** — freezes one attempt plan into a manifest. The manifest
  holds:
  - identity: source, model, tokenizer, template, backend and dependencies;
  - the launch flags, sessions and time parameters;
  - the host's calibration record;
  - Hermes's effective timeouts and the terminal-tool allowlist.

  `prepare.py` refuses a lab root inside the repository.
- **`run.py`** — owns one attempt. It verifies identity, samples telemetry,
  admits per device, launches under a kill-on-close Job Object, and runs
  each session in a fresh home and fixture with an erased slot. The
  calibration plan writes `calibration.json`, and fails closed if any field
  is missing.

  The one state that persists across attempts is the backend's CUDA kernel
  cache, `<lab>/kernel-cache`. It is driver state: a cold cache made the
  first prompt 30× slower. Its growth counts as progress, and a request that
  grew it is excluded from rate samples.

  Every session runs at the same paths (`<attempt>/live`), because Hermes
  renders its home and working directory into the system prompt. When the
  session ends, the lab closes its process tree and archives the state to
  `session-NN`. A session spec with `"erase": false` keeps the previous
  session's slot, to measure cross-session prefix reuse.
- **`verify_long.py`** — the long task's hidden verifier, kept outside the
  fixture.
  - It scores the fixture state (3 defects and 1 feature).
  - It runs the L3 pre-check on the first long request, with Hermes's own
    system prompt and tools.
  - It flags terminal paths outside the fixture (L4).
  - `build-reference` runs the reference path and records its outputs.
- **`publish.py`** — writes one attempt's correlated receipts into the
  Book. Prompts and tool output stay in the lab, and a privacy screen fails
  closed.
- **`wire.py`** — sits between Hermes and llama.cpp.
  - It applies each session's arm bounds and forwards every request once,
    upstream as streaming with `return_progress`.
  - It strips progress chunks from the client and reassembles responses for
    non-streaming clients.
  - It polls `/slots` as a second progress signal.
  - It records predicted and actual time, timings, `id_slot`,
    `finish_reason`, and the reasoning/visible token split.
- **`driver.py`** — one Hermes CLI session. The repository is importable only
  through its own `sys.path`, so the CLI and tool environment carry no
  repository path.
- **`policy.py`** — pure identity, admission, paging and stop predicates.
- **`bringup.py`** — the pre-live stop-control check (no model).

## Time model

Every deadline, stall window, backstop and backend probe timeout comes from
`hermes_cli/local_runtime/throughput.py` and the calibration record measured
on the running host (`run.session_windows`, `run.probe_window`), so the same
lab serves hosts of any speed. The fixed values that remain bound process
start-up, I/O or polling, never token work.

During the calibration attempt, the gap window between requests is k × the
attempt's own load time, like its other windows. The plan specified k × that
session's measured T_cli, but the driver reports T_cli only in its result,
after the session ends, so the supervisor has no T_cli to use while the
session runs. This is a recorded plan deviation, and it is the more
permissive window.

The locked plan retained the observation cadences (telemetry, supervisor
loop, `/slots`) and the guards counted in them, the 2 s grace and 5 s
cleanup, the wire's 1 s lock handoff and the `git` tool timeouts. Sprint 3
added the rest of this list during the Test phase (a recorded plan
deviation):

| Value | Bounds | Why it is fixed |
|---|---|---|
| Telemetry 1 s, loop 0.25 s, `/slots` 0.5 s | observation cadence | retained by the plan |
| Grace 2 s, cleanup 5 s | OS kill safety (INT-0004 AC2) | retained by the plan |
| Telemetry writer retry: half a sample period | `os.replace` against an open reader | keeps the sample cadence |
| `nvidia-smi` query 2 s | one GPU telemetry probe | a hung driver query must not stall sampling |
| Hidden verifier: 60 s process, 120 s thread | running the fixture's own quick checks | the checks run in milliseconds; this only catches a hung interpreter |
| `git rev-parse` and `git status` 10 s | the identity check | retained by the plan (`git` tool timeouts) |
| Wire close 1 s | the lock handoff from a finished handler at shutdown | retained by the plan |
| Task venv creation 600 s | one-time lab setup in `prepare.py` | not part of any attempt |
| Listener check 0.2 s | one loopback connect after cleanup | a closed local port refuses at once; it only records whether the backend's port closed |

## Usage

Run from the repository root with the disposable venv. `<lab>` must be
outside the repository.

    PYTHONPATH=. <venv>/python evals/local_qualification/bringup.py
    PYTHONPATH=. <venv>/python evals/local_qualification/prepare.py --model <gguf> --server <llama-server> --lab <lab> --plan calibration
    PYTHONPATH=. <venv>/python evals/local_qualification/run.py --lab <lab> --manifest <lab>/manifests/<plan>-<id>.json

Commit first: `run.py` refuses a manifest frozen from a different or dirty
revision, and re-checks for uncommitted changes at launch. Create `<lab>/STOP`
to stop an attempt through the owned cleanup path.
