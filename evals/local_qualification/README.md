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

Every deadline, stall window and backstop comes from
`hermes_cli/local_runtime/throughput.py` and the calibration record measured
on the running host, so the same lab serves hosts of any speed. The fixed
values that remain are all observation cadences or OS-level kill safety, not
token work:

- the telemetry, supervisor-loop and `/slots` periods;
- the 2 s grace and 5 s cleanup.

## Usage

Run from the repository root with the disposable venv. `<lab>` must be
outside the repository.

    PYTHONPATH=. <venv>/python evals/local_qualification/bringup.py
    PYTHONPATH=. <venv>/python evals/local_qualification/prepare.py --model <gguf> --server <llama-server> --lab <lab> --plan calibration
    PYTHONPATH=. <venv>/python evals/local_qualification/run.py --lab <lab> --manifest <lab>/manifests/<plan>-<id>.json

Commit first: `run.py` refuses a manifest frozen from a different or dirty
revision, and re-checks for uncommitted changes at launch. Create `<lab>/STOP`
to stop an attempt through the owned cleanup path.
