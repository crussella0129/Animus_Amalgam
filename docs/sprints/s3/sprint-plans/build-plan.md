Finalized - DO NOT EDIT

# Sprint 3 Build Plan

## Intents

- [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md) — state: planned.
  - **Covered in Sprint 3:** AC1; AC2 for thinking off and bounded thinking,
    with the sampling screen; AC3; AC6 for the settings measured here; AC7
    for the lab route.
  - **Deferred, backlog:** AC2's unbounded-thinking arm (T-218); AC4 MTP
    (T-217); AC5 compression, and AC7 on Hermes's own local-route request,
    load, stream-stale and compression deadlines (T-219).
- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) — state: active. Covered: the AC1 and AC4 gaps carried from Sprint 2; AC2's time gate (host-derived) and main-cancellation replay; the carry-forward replays. AC3, AC5 and AC6 remain T-202. Auxiliary cancellation moves with compression to T-219, since Sprint 3 sends no auxiliary traffic.

## Approval boundary

The owner approved the Sprint 3 plan in Claude Code Plan Mode on 2026-09-24,
held it after the first plan critique, and settled every open point in chat:

- ratify attempt-scoped charging;
- derive budgets from measured throughput × the work about to be done;
- derive backstops from the running host's token rate, because the software
  must run on other machines of unknown speed;
- screen sampling experimentally;
- prefer throughput over per-step latency;
- scope Sprint 3 to the core, moving MTP, uncapped thinking and compression
  to Sprint 4.

The envelope is approved once (L-18). A new resource class returns to the
owner: a larger model, a download, stopping the owner's applications or WSL,
or exceeding the host-derived sprint budget.

Live-profile baseline, for P2:

| File | Bytes | SHA-256 |
|---|---:|---|
| `config.yaml` | 6700 | `a48b4add7508261c13ddb54c66f9d5a4e9b3e62ada7f0520d34f4ccd3d848f1c` |
| `presets.ini` | 580 | `bb35c72da07c0cfce2409ba22340d5bc1157821a03ac2788500f549253f8d0a1` |

Both are unchanged since Sprint 1.

## Host-calibrated time model (INT-0007 AC7)

The only parameters are dimensionless ratios and token-count thresholds, frozen in each manifest:

- margin `m` = 2.0;
- stall multiple `k` = 20;
- floor fraction `f` = 0.5;
- planning allowance `U` = 2048 uncached tokens per request;
- minimum samples: prefill `n_batch` tokens, decode 16 tokens.

**Rates.**

- Prefill `P` and decode `D` (tokens/s) are averaged only over samples
  meeting those minimums. Tiny warm prefills never set a rate.
- Overhead `O` is the measured time from request send to the first progress
  event.
- `T_load` is the measured model-load time. `T_cli` is the measured CLI
  start-up time.
- **Calibration record.** T-222 writes `P`, `D`, `O`, `T_load`, `T_cli`,
  checkpoint size and the observed cleanup time to a record that seeds every
  later attempt.
- **Floors.** `P_min = f × P_cal` and `D_min = f × D_cal`, fixed from the
  calibration record for the whole sprint.
  Rates observed below the floors, and the attempt's observed p99 event
  gap, are recorded as degradation metrics only. They never widen a window
  within an attempt, per the INT-0004 boundary.

**Prediction, recorded for every request:** `O + uncached/P + cap/D`. It is
rearmed at the first progress event (exact `total − cache`) and on each
later progress event and token. It is never enforced.

**Enforcement.** A step is stopped only by one of these:

- **Stall.** No progress signal within `k ×` the expected interval.
  - Progress signals: an SSE progress event, a token, or a rise in the
    active slot's `n_prompt_tokens_processed` or `n_decoded` on `/slots`,
    polled by the wire. That covers deltas the server's parser withholds.
  - Expected interval: `max(O_cal, n_batch/P_min)` from send to the first
    event, because template rendering, tokenizing and checkpoint restore grow
    with the prompt; `n_batch/P_min` during prefill; `1/D_min` during decode.
  - No stall window is shorter than 4 × the observation period (the `/slots`
    poll).
  - During the calibration attempt, before any floor exists, the window is
    that attempt's measured `T_load`, and no request backstop applies.
- **Request backstop.** `m × (O_cal + context/P_min + cap/D_min)`: the worst-case
  work at this host's floors. Stopping a request here is a recorded failure
  (AC7).
- **Load.**
  - Progress is backend memory growth (RSS + VRAM) or new log output.
  - Stall: none within `k` telemetry samples.
  - Backstop after calibration: `m × T_load / f`, which applies the floor
    rate like every other backstop. The very first load has no
    time backstop, only the load stall and the resource stops.
- **Gap between requests** (tools, CLI work).
  - Owned CLI-tree CPU time growth or output counts as progress.
  - Idle window: `k × T_cli_cal`. During calibration it is `k ×` that
    session's measured `T_cli`.
  - The lab adds no time backstop for a busy tool. Hermes's terminal command
    timeout bounds it; the value is recorded in the manifest and moves with
    T-219.
- **Per-session request limit.** 3 × the session's planned requests (screen
  24, full run 90), enforced by the wire. An over-limit session is a
  recorded arm failure that counts in the denominators. Hermes's per-turn
  `max_turns` is 30.
- **Sprint budget.** After calibration:
  `m × Σ(hash_cal + T_load + sessions × T_cli + planned requests × (O + U/P + cap/D))`
  over the planned attempts below.
  - The comparator is the attempt-scoped charged time, which covers
    hashing, load, CLI start-up, requests and tool gaps.
  - Calibration is charged but excluded from the Σ, and reported
    separately.
  - Exceeding the budget triggers a stop-and-report to the owner.
- **Resource stops:** the Sprint 2 RAM/VRAM reserves, page-out, and page-in
  under RAM pressure.

**Constants classification** (T-221 T3).

- *Replaced by host-derived rules:*
  - `run.py`: request 300, readiness 300, load 300, out-of-request 300, and
    the `main-cancel` 5 s trigger (now "first decoded token");
  - `wire.py`: socket 300, and metadata-probe `backend_timeout` 2 (now
    `k × max(O_cal, n_batch/P_min)`);
  - `driver.py`: `run_budget` 300 (removed, together with its wrap-up
    notice); `max_turns` 6 (now 30 per user turn, plus the per-session request limit);
    `max_tokens` 128 and `reasoning="none"` (now arm fields);
  - `prepare.py`: `load_page_in_allowance_seconds` 60 (now "until ready or
    load stall"); `request_seconds` and `load_seconds` (now the time-model
    parameters); `owner_choice.pilot_seconds` (now the owner's time-model
    decision).
- *Retained, with reasons* (none is token work):
  - the telemetry cadence (250 ms and 1 s);
  - its health guards, expressed as multiples of the cadence: stale is 3
    periods, lag is 2 periods, and the load stall is `k` samples. These are
    excluded from H3 scaling;
  - the baseline of 10 samples;
  - the OS-level kill safety of INT-0004 AC2: 2 s grace and 5 s cleanup;
  - the wire's internal 1 s lock handoff;
  - the `/slots` observation period (500 ms);
  - git tool timeouts.

**Hermes's own timers stay behind the lab.** The lab home config sets
Hermes's stream-stale and request timeouts to at least the lab's request
backstop (M2), so the lab's rules govern. The manifest records the effective
values. The Hermes-side application of AC7 is T-219.

**Server output limit (decision).** `--predict` is removed from the server
argv. The server default is unlimited, which Sprint 2 observed
(`n_predict = -1`); only the per-request cap binds, and M1's test asserts
that.

**One implementation:** `hermes_cli/local_runtime/throughput.py` (T-215).

## Approved envelope

- **Model:** the existing Qwen3.8-27B file (Sprint 2 inventory hash). No
  downloads.
- **Context:** one context for the whole sprint, 32768. If the calibration
  launch cannot be admitted at 32K, every attempt uses 24576. If a later
  launch cannot be admitted at the sprint context, the owner is asked to free
  memory; the context never drops silently.
- **Output caps:** 512 for thinking off, 768 for thinking with
  `reasoning_budget_tokens` 256.
- **Input ceiling:** `context − cap − 512`, as an arm field. A request over
  the ceiling is a recorded arm failure.
- **Checkpoints:** calibration measures checkpoint size at trace verbosity,
  with `--ctx-checkpoints 4`. The count is then frozen for the whole sprint:
  `min(32, floor(calibration RAM headroom above the admission need ÷
  size))`, and added to admission. If a later launch lacks RAM for it, the
  owner is asked; the count is never reduced silently. If the count is below
  2, R1's rollbacks are full reprocesses (recorded) and R3 is recorded
  not-run. `--checkpoint-min-step` stays at its default except in R3.
- **Streaming:** the wire forces `stream: true` and `return_progress: true`
  upstream, because the pinned build sends progress only on streaming
  requests. For every client, streaming or not, it consumes and strips the
  progress chunks, and it reassembles a JSON response for a non-streaming
  client.
- **Slot erase:** the server runs with `--slot-save-path <attempt dir>`,
  because the pinned build refuses slot actions, including erase, without
  it.
- **Task interpreter:** a disposable standard-library venv, created once
  per sprint in the lab root outside the repository with
  `python -m venv`. It is built from the managed runtime's base
  interpreter, with no download, so model commands never run inside the
  live Hermes install. It comes first on the session `PATH`, so the
  scripted turns just say `python`.
- **L4 allowlist,** recorded in the manifest: that venv, the OS system
  binary directories, and the terminal tool's resolved `bash` together with
  its `usr/bin` and `mingw64/bin` directories.
- **Sampling:** seeded (42), fully specified per configuration (T-212 S1).
- **Counts:** at most 12 launches and 400 physical requests.
- **Host:** the owner's applications and WSL are never stopped without
  asking.

## Planned attempts

| Attempt | Task | Launches | Sessions | Planned requests |
|---|---|---:|---|---:|
| Dirty-tree refusal | T-222 | 0 | — | 0 |
| Calibration and replay | T-222 | 1 | 2 smoke (cross-session), 1 decode sample, 1 main-cancel | 5 |
| Sampling screen | T-212 | 1 | 6 configurations, each a fresh home, fixture and slot | 48 |
| R0, R1, R2 | T-216 | 3 | 1 full task each | 90 |
| R3 (conditional) | T-216 | 1 | 1 full task | 30 |
| Repair replays (reserve) | any live task | ≤ 5 | as needed | ≤ 228 |

## Schema Tree

- Keep a long local session fast (INT-0007), on a hardened lab (INT-0004)
  - Time model
    - T-215: host-calibrated throughput and deadline module
  - Lab
    - T-211: arm manifests, per-session fresh state outside the repo, clean environment, receipt and manifest fields
    - T-221: apply the time model in the lab; extract stop predicates; forced streaming; bring-up stop check
    - T-222: live replay, calibration record, main-cancel, cross-session prefix
  - Task
    - T-210: long multi-file task, hidden verifier, pre-check, contamination detection
  - Experiments
    - T-212: sampling × thinking screen
    - T-216: full runs R0–R2 (+R3), reasoning echo, sprint-wide repair provenance and accuracy
  - Outcome
    - T-213: default local operating policy (partial; not applied)
    - T-214: formal checks after operational confidence

Backlog T-210 and T-211 are decomposed here. The Sprint 4 work is queued in
the backlog: T-217 to T-219, plus T-220 (A→B→A).

## Execution Sequence

### T-215: Host-calibrated throughput and deadline module
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** `hermes_cli/local_runtime/throughput.py` (new)
- **Depends on:** (none)
- **Acceptance criterion:** INT-0007 AC7.
- **Success criterion (EARS):**
  - **H1 WHEN** timings or progress samples are observed, **THEN** the
    module **SHALL** update `P` and `D` only from samples meeting the
    minimum-sample rules. It **SHALL** keep the floors fixed from the
    calibration record, and its prediction **SHALL** be monotonic
    non-decreasing in uncached and output tokens. A 1-token prefill
    **SHALL NOT** change `P`.
  - **H2 WHEN** events keep arriving within the stall window, **THEN** no
    rule **SHALL** stop the step before the request backstop. **WHEN** no
    event arrives within the window, **THEN** the stall rule **SHALL** fire.
    **WHEN** a progressing step reaches the backstop, **THEN** the backstop
    **SHALL** fire and be reported as a failure.
  - **H3 WHEN** the same work is evaluated with all calibrated rates scaled
    by `s`, **THEN** every stall window, backstop and budget **SHALL** scale
    by `1/s`, apart from the measured-overhead terms. The module **SHALL**
    contain no fixed-seconds constant, shown by computation.
- **Notes:** a pure module with no I/O; parameters are passed in. Hermes
  config wiring comes with its first Hermes consumer (T-219).

### T-211: Arm manifests, fresh per-session state, clean environment, receipt and manifest fields
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/{prepare,run,driver,wire}.py`, `evals/local_qualification/arms.json` (new; arm and sampling definitions), `evals/local_qualification/README.md`
- **Depends on:** T-215
- **Acceptance criterion:** INT-0004 AC1 and AC4.
- **Success criterion (EARS):**
  - **M1 WHEN** an arm manifest is frozen, **THEN** the lab **SHALL** launch
    with exactly that arm's server flags, including `--slot-save-path` and
    without `--predict`. It **SHALL** forward every request
    with that arm's cap, input ceiling, thinking mode, reasoning budget and
    fully specified sampling. The lab home **SHALL** carry the arm's
    `model.reasoning_echo`.
  - **M2 WHEN** a session starts, **THEN** the lab **SHALL** create a fresh
    home and fixture outside the repository, set
    `agent.environment_probe: false`, pass `SYSTEMDRIVE` through, and give the
    CLI and its tools an environment with no repository path. The repo is
    importable only through the driver's own `sys.path`. The home config
    **SHALL** set Hermes's stream-stale and request timeouts at or above
    the lab's request backstop.
  - **M3 WHEN** a request completes, fails or is stopped, **THEN** its
    receipt **SHALL** carry:
    - meaningful first token;
    - `id_slot`;
    - `finish_reason`;
    - truncation continuations and retries;
    - tool-call parse and argument validity;
    - maximum supervisor lag, as a host-responsiveness proxy.

    Any field the backend does not provide **SHALL** be named missing.
  - **M4 WHEN** an attempt is published, **THEN** its receipt and manifest
    **SHALL** record:
    - the first rendered prefix (tokens and hash);
    - the admission host condition;
    - the time-model parameters and calibration record;
    - Hermes's effective timeouts;
    - the owner's time-model decision, which replaces `pilot_seconds`.

### T-221: Apply the time model in the lab; extract stop predicates; forced streaming; bring-up stop check
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md), [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** `evals/local_qualification/{run,wire,policy,telemetry,driver,prepare}.py`
- **Depends on:** T-215, T-211
- **Acceptance criterion:** INT-0004 AC2; INT-0007 AC7 (lab route).
- **Success criterion (EARS):**
  - **T1 WHEN** a request, load or inter-request gap is in progress, **THEN**
    the lab **SHALL** apply only the T-215 stall rules, the host-derived
    backstops and the resource stops. It **SHALL** record the predicted
    (initial and rearmed) and actual seconds.
  - **T2 WHEN** a telemetry sample goes stale, the supervisor lags, a launch
    or request count would exceed its cap, or the sprint budget is exceeded,
    **THEN** the corresponding extracted `policy.py` predicate **SHALL**
    stop or refuse at its boundary.
  - **T3 WHEN** any constant on the "replaced" list is exercised, **THEN**
    its behavior **SHALL** come from a host-derived rule. Only the constants
    on the "retained" list **SHALL** remain fixed.
  - **T4 WHEN** a client sends a streaming or non-streaming request,
    **THEN** the wire **SHALL** stream upstream with progress enabled, and
    progress chunks **SHALL NOT** reach the client. A non-streaming client
    **SHALL** receive one reassembled response, and `/slots` counters
    **SHALL** count as progress.
  - **T5 WHEN** the pre-live bring-up stop check runs with explicit
    synthetic rates, **THEN** a synthetic child that emits no events under
    the owned job **SHALL** be stopped by the stall rule, its tree **SHALL**
    be cleaned up within INT-0004 AC2's 5 s, and an unrelated sentinel
    **SHALL** survive. No model is loaded.

### T-222: Live replay, calibration, main-cancel and cross-session prefix
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md), [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** the Sprint 3 operational ledger, qualification receipts and calibration record; focused repairs only where reproduced
- **Depends on:** T-221
- **Acceptance criterion:** INT-0004 AC2 and the Sprint 2 post-attempt-13 replay; INT-0007 AC3 (cross-session) and AC7 (calibration).
- **Success criterion (EARS):**
  - **C1 WHEN** a deliberate untracked file exists at launch, **THEN** the
    attempt **SHALL** be refused with zero launches consumed. Once it is
    removed, the launch **SHALL** proceed, with the ready server's context
    and argv matching the arm and the explicit-pin served-window check
    admitting the pin.
  - **C2 WHEN** the calibration launch completes, **THEN** the calibration
    record **SHALL** contain `P`, `D`, `O`, `T_load`, `T_cli`, the
    checkpoint size and the frozen checkpoint count.
    - `D` comes from a decode-sample request: thinking off, at least 16
      decoded tokens, independently checked.
    - The prefill sample must cover at least one full batch, and a
      checkpoint must have been created.
    - If any field is missing, calibration **SHALL** fail closed: no later
      attempt starts, and the owner gets a stop-and-report. The sprint budget
    **SHALL** be computed from the record and written to the ledger before
    any other attempt.
  - **C3 WHEN** two fresh sessions send the same smoke, **THEN** their
    rendered system prompts **SHALL** be byte-identical. The receipt
    **SHALL** record whether the second reused the first's cached system
    prefix; a miss is recorded as AC3's cross-session half not met, with the
    cause.
  - **C4 WHEN** a main-cancel session reaches its first decoded token,
    **THEN** the lab **SHALL** cancel it. The slot **SHALL** be idle and
    owned cleanup complete within 5 s. Auxiliary cancellation is not
    exercised in Sprint 3 (there is no auxiliary traffic) and moves to T-219.

### T-210: Long multi-file task, hidden verifier, pre-check and contamination detection
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** `evals/local_qualification/tasks/long/` (fixture template, scripted user turns, reference edits), `evals/local_qualification/verify_long.py`, `evals/local_qualification/{driver,wire,prepare}.py` (task-corpus hash covers all task files), `evals/local_qualification/publish.py` (new)
- **Depends on:** T-211
- **Acceptance criterion:** INT-0007 AC1.
- **Success criterion (EARS):**
  - **L1 WHEN** a long-task session runs, **THEN** every request receipt
    **SHALL** contain:
    - input, cached and uncached-prompt tokens;
    - decoded reasoning and visible tokens;
    - prompt and decode ms, and the decode rate;
    - wall time;
    - predicted time;
    - resource extrema.
  - **L2 WHEN** a session ends by completing, failing or being stopped,
    **THEN** the hidden verifier **SHALL** score the 3 seeded defects and
    the added feature (4 items) from the fixture state alone, and the
    request count **SHALL** be recorded. Fewer than 20 requests **SHALL** be
    recorded as AC1 coverage not met, separately from completion.
  - **L3 WHEN** the task is frozen, **THEN** its pre-check **SHALL** show
    all of the following:
    - the largest reference edit fits the smallest cap;
    - the reference path needs at least 20 requests;
    - the reference path's peak rendered prompt, plus worst-case echoed
      reasoning (256 per request), fits the smallest sprint context's input
      ceiling.
  - **L4 WHEN** a tool call resolves to a path outside the session's fixture
    (after relative-path and environment-variable expansion), and is not on
    the manifest's allowlist of the task interpreter and system binaries,
    **THEN** the session **SHALL** be flagged as contaminated. A flagged session is
    excluded from selection and denominators and re-run once; a second flag
    counts as a failure.
- **Notes:**
  - The fixture is a small Python package with 3 seeded defects across
    files, a visible check runner and about 8 scripted user turns.
  - Turn 3 fixes the first defect, which makes the screen's opening
    scorable.
  - `max_turns` is 30 per user turn for every arm, plus the per-session
    request limit.
  - The defect specifics stay out of the Book until R2 finishes.

### T-212: Screen sampling × thinking mode
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** the Sprint 3 operational ledger and qualification receipts; `evals/local_qualification/arms.json` (screen results only); focused repairs only where reproduced
- **Depends on:** T-210, T-222
- **Acceptance criterion:** INT-0007 AC2 (sampling selection).
- **Success criterion (EARS):**
  - **S1 WHEN** the screen runs, **THEN** each configuration **SHALL** run
    the first 3 user turns in its own fresh home and fixture, with the slot
    erased before the session. All use seed 42, min-p 0 and repetition
    penalty 1.0, with no other samplers. Configurations:
    - thinking off:
      - greedy (temperature 0);
      - vendor non-thinking: 0.7 / 0.8 / 20, presence penalty 1.5;
      - model default (GGUF `general.sampling`): 1.0 / 0.95 / 20;
    - thinking on, budget 256:
      - greedy;
      - vendor thinking: 1.0 / 0.95 / 20;
      - mid probe: 0.6 / 0.95 / 20. This is reported only and is **not
        selectable**, because AC2 admits only greedy and the model's and
        vendor's recommended settings. For thinking on, the model default
        and the vendor thinking setting are identical, so there are two
        selectable candidates.
  - **S2 WHEN** the screen completes, **THEN** each thinking mode's
    selection **SHALL** rank only the AC2-admissible candidates, by:
    1. verified items, descending;
    2. machine time per verified item, ascending;
    3. decoded tokens, ascending.

    Machine time is session wall time from the first request start to the
    last response end, excluding load. If every configuration in a mode
    scores 0, the ranking **SHALL** use machine time and flag the screen
    inconclusive for that mode.
  - **S3 WHEN** screen results are reported, **THEN** they **SHALL** be
    labeled as single seeded screening runs, not statistical superiority.

### T-216: Full runs, reasoning echo, sprint-wide repair provenance and accuracy
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** the Sprint 3 operational ledger and qualification receipts; focused repairs only where reproduced
- **Depends on:** T-212
- **Acceptance criterion:** INT-0007 AC1, AC2 (off and bounded), AC3 and AC7 (live accuracy).
- **Success criterion (EARS):**
  - **O1 WHEN** each full run executes the long task at the sprint context,
    **THEN** its receipts **SHALL** report decoded tokens and machine time
    per verified item, with failures and stops in the denominators. Runs:
    - R0: best thinking-off configuration;
    - R1: best bounded-thinking configuration, echo off;
    - R2: R1 with `model.reasoning_echo: true`.
  - **O2 WHEN** R1 runs, **THEN** receipts **SHALL** show per-turn uncached
    tokens and the divergence point. **WHEN** R2 runs, **THEN** the same
    measure **SHALL** show whether history stays append-only, including
    whether the template's trimmed re-render matches the generated think
    block.
  - **O3 WHEN** R1's median uncached tokens per continued turn exceed 2,000
    and the frozen checkpoint count is at least 2, **THEN** R3 **SHALL**
    rerun R1 with `--checkpoint-min-step 512` and report rollback cost
    against checkpoint RAM. Otherwise the ledger **SHALL** record which
    condition was not met.
  - **O4 WHEN** an in-scope operation fails in T-222, T-212 or T-216,
    **THEN** the ledger **SHALL** link the operation, failure, diagnosis,
    repair revision and replay. A repair that changes an intent boundary
    **SHALL** go through an intent revision as its own task.
  - **O5 WHEN** all Sprint 3 requests are complete, **THEN** the ledger
    **SHALL** report T-215's prediction accuracy (predicted vs actual,
    initial and rearmed) and every stall, backstop or resource stop with its
    cause.

### T-213: Default local operating policy for the measured settings
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** `docs/lineage/local-operating-policy.md`, `docs/SUMMARY.md`
- **Depends on:** T-216
- **Acceptance criterion:** INT-0007 AC6, partial: settings measured in Sprint 3.
- **Success criterion (EARS):**
  - **P1 WHEN** the full runs complete, **THEN** the policy **SHALL**:
    - rank the settings that were varied (thinking mode, sampling, echo,
      checkpoint density) by machine time per verified item, with linked
      receipts;
    - state the fixed choices with their rationale: context, environment
      probe, time-model parameters, toolset;
    - mark MTP, uncapped thinking and compression as pending Sprint 4;
    - state that all results are single seeded runs.

    **WHEN** no arm verifies any item, or admission prevents the runs,
    **THEN** the policy **SHALL** instead document the negative result and
    name the limiting resource.
  - **P2 WHEN** the sprint closes, **THEN** the live `config.yaml` and
    `presets.ini` fingerprints **SHALL** equal the baseline above. Any
    live-profile snippet in the policy stays a proposal for the owner.

### T-214: Formal checks after operational confidence and evidence handoff
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md), [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- **Touches:** `tests/hermes_cli/test_local_runtime_throughput.py` (new), `tests/evals/`, affected `tests/agent/` files, `docs/sprints/s3/sprint-tests/`, `docs/intents/INT-0004-*.md`, `docs/intents/INT-0007-*.md`, `docs/SUMMARY.md`
- **Depends on:** operational confidence after T-216; recording blockers is always permitted
- **Acceptance criterion:** evidence for INT-0004 AC1, AC2 and AC4, and for INT-0007 AC1, AC2 (partial), AC3, AC6 (partial) and AC7 (lab route).
- **Success criterion (EARS):**
  - **V1 WHEN** formal tests run, **THEN** the ledger's confidence record and
    its anchoring receipt **SHALL** both predate the first formal run, and
    the runner log fingerprint **SHALL** be recorded.
  - **V2 WHEN** a defect was repaired in T-222, T-212 or T-216, **THEN** its
    regression **SHALL** fail on the pre-repair revision and pass after.
  - **V3 WHEN** Sprint 3 receipts are published, **THEN** every attempt
    **SHALL** resolve to a digest-valid manifest with its arm, and no user
    path, credential or ephemeral token **SHALL** appear in any published
    JSON.
- **Notes:** compare failing test IDs on base vs head for the affected
  suites, with the same settings on both trees.
