# Sprint 2 Build Plan

## Intents

- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) —
  state: planned. Covers AC1, the smoke/resource/cancellation
  gate in AC2, development receipts in AC4, and reverse-E2E development in
  AC7. AC3, comparative context-policy AC5 and advancement AC6 remain T-202.
  Operational tasks here are development probes, not paired qualification.
  This sprint cannot realize the
  full intent or authorize adaptive-policy work.

## Approval boundary

The owner approved the revised reverse-E2E plan with “ok now continue” on
2026-09-24. Native Plan Mode tools are unavailable in this Codex session;
planning preserved the source-unchanged and explicit owner-approval boundary.
The independent critic and canonical finalization helper must pass before
Build. Approval covers this bounded experiment and focused repairs; live
Hermes configuration and unrelated processes remain outside it.

## Schema Tree

- T-201 operating-envelope gate, 27B first
  - T-201: disposable working environment and candidate manifest
  - T-206: minimum independent observation and stop controls
  - T-207: actual Hermes entry point and diagnostic adapter
  - T-208: operate, break, diagnose, repair and replay
  - T-209: focused formal verification and evidence handoff

The current combined T-201 backlog entry is decomposed by this plan; T-202
and later work remain queued. No new decoder, provider plugin, agent loop,
daemon or UI is included. Focused Hermes repairs are permitted when a real
operation demonstrates the defect; inspect area guidance and the production
path before editing. Do not build speculative infrastructure first.

## Reverse-E2E execution order

1. Create a disposable Hermes home, dependency environment and fixture
   workspace, using a worktree if source isolation is needed. Start with the
   real CLI/custom-provider path. Reuse available diagnostics; build only
   missing observation and stop controls needed to operate safely.
2. Bring it up, inspect the actual outgoing request and practically exercise
   the stop mechanism. These few operational bring-up checks are not a
   prerequisite unit/integration suite or an exhaustive mock matrix.
3. Operate the admitted 27B through a real short task: read a fixture, make
   an edit, run its checker, handle a failing command and continue the same
   conversation. Probe bounded context accumulation and interruption. A
   no-tool `AMALGAM_OK` smoke is only startup confirmation.
4. On failure, stop that attempt, retain evidence, diagnose, make the smallest
   relevant repair and replay the failing operation. A failed attempt does
   not end development. Change settings only between recorded attempts, keep
   limits fixed and retain the aggregate budget across all revisions.
5. Declare operational confidence only after independently checked task
   completion, successful repair replays in fresh and continued sessions,
   no unresolved blocking defect and demonstrated main/auxiliary cleanup.
6. Only then run official unit/integration suites. Add focused regression
   coverage for observed defects and essential contracts. If a suite exposes
   a real failure, return to its operational reproduction/repair before the
   relevant suite is rerun. Do not repeat green suites without a new reason.

A resource rejection is an observed blocker to investigate, not evidence
that the operational loop succeeded. Do not replace unavailable operation
with more mocks. Keep confidence and formal verification pending if the
blocker cannot be resolved within the authorized envelope.

## Fixed experiment policy

- Selected model: existing 27B file and SHA-256 in the research inventory.
  No automatic 7B fallback or replacement download.
- Source starts at `cd2185c288398b19941b968e4352bf38bbcafbda` and records the
  exact evaluation implementation commit separately. New harness uses a
  minimal Rust owner under `evals/local_qualification/` only for missing
  process/resource controls, with thin Python glue where existing Hermes
  interfaces need observation. Do not build a general evaluation framework.
  Freeze dependencies and
  interpreter in a separate evaluation environment; leave live venv intact.
- Fresh Hermes home/process, fixed custom loopback endpoint, no inherited
  credentials/plugins/memories, managed runtime disabled. Bind server to
  loopback on a newly reserved port and use an ephemeral local authentication
  token where supported. Exclude that token from published evidence.
- Server: 8,192 context, one slot, fit off, no context shift, no speculation,
  no warmup inference, q8_0 K/V, flash attention on, batch/ubatch 256/128,
  six CPU threads, prompt-cache RAM zero. Freeze explicit GPU placement from
  tensor accounting before launch; refuse unknown placement rather than
  auto-tune. Record actual allocation and all inherited-default overrides.
- Workload: a no-tool `AMALGAM_OK` startup smoke, main/auxiliary cancellation,
  then actual Hermes file/command operations against disposable fixtures.
  Choose the minimal existing toolset at conversation start and keep it
  stable. Independently check files and command results. Complete
  rendered input is at most 4,096 tokens, output at most 128 including
  reasoning. Sampling uses temperature zero, top-p one and seed 42; record
  remaining sampling defaults explicitly. Freeze any template reasoning
  option and its verified support.
  No trimming instructions to meet the budget, mid-session tool changes,
  automatic compression, hidden retries or concurrent generation.
- Approved development budget: 300 seconds per load and per request; six
  launches, eighteen physical inference requests and 60 minutes total,
  including startup/cleanup, across all repairs and manifests. This replaces
  the draft's three-request smoke-only budget so the operational repair loop
  is possible; the revised budget was approved with this plan.
  Cancellation tests trigger five seconds after backend acceptance while
  active. If already complete, cancellation coverage is inconclusive, not a
  pass. Diagnose and use a recorded reproduction within the remaining budget;
  do not conceal or erase the first attempt. Metadata/tokenization probes are logged
  separately with bounded deadlines; they cannot perform generation.
- At least 4 GiB system RAM and 1 GiB dedicated VRAM free. Compare resident
  weights plus explicit KV/scratch/host allowances with CPU and GPU capacity
  separately. Reject even the optimistic aggregate lower bound if it fails.
  Current research snapshot fails that bound. Recheck before each launch.
- Observe RAM and job health every 250 ms, VRAM and hard paging every second;
  a critical sample older than three seconds blocks/stops execution. A valid
  below-reserve sample stops immediately. Hard page-in exceeding 64 MiB/s
  for three consecutive one-second samples, or supervisor scheduler lag over
  two seconds, stops the job. Measure ten seconds of baseline before launch;
  an already-failing baseline prevents launch. These are conservative pilot
  thresholds, not measured crash predictors. Soft page faults are not hard
  page-ins; lack of a reliable hard-paging probe blocks live admission.
- On stop, signal graceful cancellation with a two-second grace, then kill
  the owned Windows Job Object. Require no owned child, listener or active
  slot within five seconds of the trigger. Loss of the supervisor must also
  close the job. Never kill by process-name pattern or touch unrelated apps.

## Execution Sequence

### T-201: Bring up a disposable environment and record the candidate
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/Cargo.toml`, `Cargo.lock`, `src/manifest.rs`, `README.md`, Python driver dependency specification, `docs/sprints/s2/sprint-tests/qualification/manifest.json`
- **Depends on:** none
- **Acceptance criterion:** AC1; preflight part of AC2.
- **Success criterion (EARS):**
  - **M1 WHEN** a candidate is frozen, **THEN** its manifest **SHALL** contain verified artifact/tokenizer/template/runtime hashes, Hermes and harness commits, dependency/interpreter identity, owner choices, limits, synthetic task definitions, seed, toolset, actual rendered-prefix evidence or an explicit pre-admission `not-measured` reason, and a manifest digest used by every receipt.
  - **M2 WHEN** identity, required telemetry, explicit placement or resource admission is missing or fails, **THEN** validation **SHALL** refuse model launch and emit an exact reason; a changed artifact or parameter set requires a new manifest identity.
- **Notes:** Reuse the existing GGUF header reader and canonical host facts from Python. Start with a runnable environment, not a manifest framework. Freeze each attempted revision before executing it; distinguish candidate fields from observations and do not invent missing runtime evidence.

### T-206: Add only the observation and stop controls needed for operation
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/src/{main,supervisor,telemetry}.rs`, `evals/local_qualification/tests/`
- **Depends on:** T-201
- **Acceptance criterion:** AC2; resource/stop portion of AC4.
- **Success criterion (EARS):**
  - **S1 WHEN** an owned driver/backend stalls, a deadline expires, the owner exits, or cancellation is requested, **THEN** the supervisor **SHALL** terminate its full owned process tree within the fixed cleanup budget, record the cause and leave an unrelated sentinel process alive.
  - **S2 WHEN** a critical probe fails/stales, a headroom/paging/lag limit is breached, or an extra request/launch would exceed policy, **THEN** the supervisor **SHALL** reject or stop the attempt without a model-dependent callback or an automatic retry.
- **Notes:** Windows-native Job Object with kill-on-close; attach children before they can escape ownership. Isolate collectors so a blocked GPU/paging probe cannot stall the watchdog. Bound logs/queues and preserve final receipts after a child fails. Support the actual Windows host first; do not fake OS identity in tests.

### T-207: Wire the real Hermes entry point and observe its requests
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** isolated Hermes CLI/configuration, `evals/local_qualification/driver.py`; focused repairs in the actual Hermes path if a reproduced defect requires them
- **Depends on:** T-201, T-206
- **Acceptance criterion:** main/auxiliary part of AC2; request identity portion of AC1/AC4.
- **Success criterion (EARS):**
  - **D1 WHEN** the real main or compression path sends a synthetic request, **THEN** local wire evidence **SHALL** show the intended endpoint/model, exactly one physical request, stable serialized prompt/tool bytes, explicit 128-token output budget and no unrelated profile or external-provider fallback.
  - **D2 WHEN** complete prompt tokenization, server identity, context/slot configuration or output-limit capability differs from the manifest, **THEN** the driver **SHALL** reject generation and report the mismatch; cancellation **SHALL** cover the actual auxiliary path under the same external owner.
- **Notes:** Use existing internal budget and auxiliary observer seams; configuration output caps alone are known ineffective. The CLI must operate the real agent; a diagnostic adapter is not a replacement agent loop. Repair reproduced integration defects at their real source. A new architecture requires follow-on intent; limits cannot be weakened to make an attempt pass. Formal A→B→A coverage comes after operational confidence.

### T-208: Operate the isolated 27B system and repair observed failures
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `docs/sprints/s2/sprint-tests/qualification/` manifests, fixtures and operational ledger; ignored local raw storage; narrowly relevant Hermes code/configuration for reproduced defects
- **Depends on:** T-201, T-206, T-207 as a minimal runnable slice; no official unit/integration prerequisite
- **Acceptance criterion:** AC2, development AC4 and AC7.
- **Success criterion (EARS):**
  - **R1 WHEN** fresh host admission rejects the candidate, **THEN** that attempt **SHALL** record `not-run: resource gate` or another precise admission reason, the measured comparison and zero inference requests for that attempt; its live subchecks remain explicitly not run.
  - **R2 WHEN** admission succeeds, **THEN** the ordinary smoke **SHALL** run inside the frozen envelope and record independent answer verification, token/timing/cache observations and resource extrema, retaining timeout/breach as a failed attempt before diagnosis and repair.
  - **R3 WHEN** main or auxiliary cancellation is exercised, **THEN** each check **SHALL** prove backend activity at the trigger and owned cleanup within five seconds; failed/inconclusive checks remain visible and block confidence until their cause is resolved and replayed.
  - **R4 WHEN** actual Hermes operation encounters an in-scope failure, **THEN** the development ledger **SHALL** link the operation, observed failure, diagnosis, repair revision and replay; confidence **SHALL** require a verified file-edit/check/recovery workflow plus successful relevant fresh/continued-session replays before official unit/integration suites run.
- **Notes:** All attempts share one aggregate budget. No replay of the original oversized session and no automatic retry of failed input. Inspect and repair between attempts. A budget/resource blocker leaves operational confidence pending; it does not justify endless fixtures or a false success claim.

### T-209: Run focused formal checks after operational confidence and publish evidence
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** affected Rust/Python test modules, `docs/sprints/s2/sprint-tests/`, `docs/sprints/s2/sprint-meta.md`, `docs/work/{tasks,completed-tasks}.md`, `docs/intents/INT-0004-bounded-local-model-qualification.md`, `docs/SUMMARY.md`
- **Depends on:** T-208 operational confidence for formal suites; blocker documentation is always permitted
- **Acceptance criterion:** AC1/AC2/AC4/AC7 evidence; explicit deferred AC3/AC5/AC6 boundary.
- **Success criterion (EARS):**
  - **P1 WHEN** receipts are published, **THEN** they **SHALL** retain every attempt, exclusion, stop cause and unavailable measurement, resolve to a manifest digest, and exclude raw private configuration, credentials, user paths and unrelated transcripts.
  - **P2 WHEN** this sprint closes, **THEN** the Book **SHALL** distinguish operational development, subsequent formal tests, live pass/failure and not-run evidence, keep INT-0004 unfinished and T-202 queued, and make no native/static, adaptive-policy or general model-quality claim.
- **Notes:** Formal coverage follows actual defects and essential contracts, not implementation snapshots. Runtime failures may yield useful negative findings but cannot establish operational confidence. On unresolved admission failure, publish the blocker and leave operation-dependent/formal checks pending instead of closing T-208 as fully qualified. Follow the Test/Loop contracts for the eventual sprint verdict and human-approved merge checkpoint.
