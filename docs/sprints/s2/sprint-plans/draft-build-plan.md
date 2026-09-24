# Sprint 2 Build Plan — draft for owner approval

## Intents

- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) —
  state: proposed pending approval. Covers AC1, the smoke/resource/cancellation
  gate in AC2, and gate-level receipts in AC4. AC3, AC5 and AC6, plus useful
  task-level AC4 measurements, remain T-202. This sprint cannot realize the
  full intent or authorize adaptive-policy work.

## Approval boundary

This is planning scratch, not a finalized build plan. The installed skill
requires owner approval before implementation and a subsequent independent
critic before locking the plans. Codex exposes no EnterPlanMode or ExitPlanMode
tool in this session; source remains unchanged and the approval boundary is
preserved explicitly. Approval applies to this bounded experiment, not to
changes in the installed Hermes profile or arbitrary repeated benchmarks.

After approval, promote this draft and the draft test plan to the canonical
plan files, transition INT-0004 to planned with linked work evidence, run the
required read-only critic, address concerns and finalize through the helper.
Material scope expansion returns to the owner; routine correctness revisions
inside these boundaries do not require another approval.

## Schema Tree

- T-201 operating-envelope gate, 27B first
  - T-201: reproducible candidate and environment manifest
  - T-206: independent Rust process/resource supervisor
  - T-207: isolated Python driver through real Hermes paths
  - T-208: bounded admission, smoke and cancellation attempt
  - T-209: complete receipts and Book handoff

The current combined T-201 backlog entry is decomposed by this plan; T-202
and later work remain queued. No new decoder, provider plugin, agent loop,
daemon, UI or production-core change is included.

## Fixed experiment policy

- Selected model: existing 27B file and SHA-256 in the research inventory.
  No automatic 7B fallback or replacement download.
- Source starts at `cd2185c288398b19941b968e4352bf38bbcafbda` and records the
  exact evaluation implementation commit separately. New harness uses a
  standalone Rust crate under `evals/local_qualification/` and thin Python
  glue for the existing Python Hermes interfaces. Freeze dependencies and
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
- Workload: no-tool synthetic smoke with independently checked `AMALGAM_OK`
  answer, then separate main and compression cancellation requests. Complete
  rendered input is at most 4,096 tokens, output at most 128 including
  reasoning. Sampling uses temperature zero, top-p one and seed 42; record
  remaining sampling defaults explicitly. Freeze any template reasoning
  option and its verified support.
  No trimming instructions to meet the budget, mid-session tool changes,
  automatic compression, hidden retries or concurrent generation.
- 300 seconds per load and per request; three launches and three physical
  inference requests maximum, 30 minutes total including startup/cleanup.
  Cancellation tests trigger five seconds after backend acceptance while
  active. If already complete, cancellation coverage is inconclusive, not a
  pass and not an automatic rerun. Metadata/tokenization probes are logged
  separately with bounded deadlines; they cannot perform generation.
- At least 4 GiB system RAM and 1 GiB dedicated VRAM free. Compare resident
  weights plus explicit KV/scratch/host allowances with CPU and GPU capacity
  separately. Reject even the optimistic aggregate lower bound if it fails.
  Current research snapshot fails that bound. Recheck once at execution.
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

### T-201: Freeze the candidate, environment and admission manifest
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/Cargo.toml`, `Cargo.lock`, `src/manifest.rs`, `README.md`, Python driver dependency specification, `docs/sprints/s2/sprint-tests/qualification/manifest.json`
- **Depends on:** none
- **Acceptance criterion:** AC1; preflight part of AC2.
- **Success criterion (EARS):**
  - **M1 WHEN** a candidate is frozen, **THEN** its manifest **SHALL** contain verified artifact/tokenizer/template/runtime hashes, Hermes and harness commits, dependency/interpreter identity, owner choices, limits, synthetic task definitions, seed, toolset, actual rendered-prefix evidence or an explicit pre-admission `not-measured` reason, and a manifest digest used by every receipt.
  - **M2 WHEN** identity, required telemetry, explicit placement or resource admission is missing or fails, **THEN** validation **SHALL** refuse model launch and emit an exact reason; a changed artifact or parameter set requires a new manifest identity.
- **Notes:** Reuse the existing GGUF header reader and canonical host facts from Python. Rust owns the bounded envelope. Distinguish a valid candidate manifest from a fully observed live-run manifest; do not invent runtime fields when admission rejects.

### T-206: Implement independent process and resource supervision
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/src/{main,supervisor,telemetry}.rs`, `evals/local_qualification/tests/`
- **Depends on:** T-201
- **Acceptance criterion:** AC2; resource/stop portion of AC4.
- **Success criterion (EARS):**
  - **S1 WHEN** an owned driver/backend stalls, a deadline expires, the owner exits, or cancellation is requested, **THEN** the supervisor **SHALL** terminate its full owned process tree within the fixed cleanup budget, record the cause and leave an unrelated sentinel process alive.
  - **S2 WHEN** a critical probe fails/stales, a headroom/paging/lag limit is breached, or an extra request/launch would exceed policy, **THEN** the supervisor **SHALL** reject or stop the attempt without a model-dependent callback or an automatic retry.
- **Notes:** Windows-native Job Object with kill-on-close; attach children before they can escape ownership. Isolate collectors so a blocked GPU/paging probe cannot stall the watchdog. Bound logs/queues and preserve final receipts after a child fails. Support the actual Windows host first; do not fake OS identity in tests.

### T-207: Exercise actual Hermes main and compression paths in isolation
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `evals/local_qualification/driver.py`, `tests/evals/test_local_qualification_driver.py`
- **Depends on:** T-201, T-206
- **Acceptance criterion:** main/auxiliary part of AC2; request identity portion of AC1/AC4.
- **Success criterion (EARS):**
  - **D1 WHEN** the real main or compression path sends a synthetic request, **THEN** local wire evidence **SHALL** show the intended endpoint/model, exactly one physical request, stable serialized prompt/tool bytes, explicit 128-token output budget and no unrelated profile or external-provider fallback.
  - **D2 WHEN** complete prompt tokenization, server identity, context/slot configuration or output-limit capability differs from the manifest, **THEN** the driver **SHALL** reject generation and report the mismatch; cancellation **SHALL** cover the actual auxiliary path under the same external owner.
- **Notes:** Use existing internal budget and auxiliary observer seams; configuration output caps alone are known ineffective. Test temporary homes A→B→A with real imports. If a required contract cannot be met using existing seams, record a blocked gate and propose follow-on work instead of modifying core or weakening the limit.

### T-208: Execute one bounded 27B admission and smoke gate
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `docs/sprints/s2/sprint-tests/qualification/` manifests and receipts; ignored local raw receipt/profile storage
- **Depends on:** T-201, T-206, T-207 and passing offline tests
- **Acceptance criterion:** AC2 and gate-level AC4.
- **Success criterion (EARS):**
  - **R1 WHEN** fresh host admission rejects the candidate, **THEN** the run **SHALL** record `not-run: resource gate` or another precise admission reason, the measured comparison and zero live requests; all live subchecks remain explicitly not run.
  - **R2 WHEN** admission succeeds, **THEN** the ordinary smoke **SHALL** run inside the frozen envelope and record independent answer verification, token/timing/cache observations and resource extrema, with a timeout or breach retained as a failure and no next trial.
  - **R3 WHEN** smoke succeeds, **THEN** main and auxiliary cancellation checks **SHALL** each prove backend activity at the trigger and owned cleanup within five seconds; failure/inconclusive activity stops further work without counting cancellation as passed.
- **Notes:** Three launches allow restarting the owned server after cancellation; all fall within one run ledger and total budget. No replay of the original long session. Rejected or cancelled trials have no invented completion rate. Under current memory conditions, a no-launch result is expected but not predetermined.

### T-209: Publish complete evidence and keep qualification scope honest
- **Intent:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
- **Touches:** `docs/sprints/s2/sprint-tests/`, `docs/sprints/s2/sprint-meta.md`, `docs/work/{tasks,completed-tasks}.md`, `docs/intents/INT-0004-bounded-local-model-qualification.md`, `docs/SUMMARY.md`
- **Depends on:** T-208
- **Acceptance criterion:** AC1/AC2/AC4 evidence; explicit deferred AC3/AC5/AC6 boundary.
- **Success criterion (EARS):**
  - **P1 WHEN** receipts are published, **THEN** they **SHALL** retain every attempt, exclusion, stop cause and unavailable measurement, resolve to a manifest digest, and exclude raw private configuration, credentials, user paths and unrelated transcripts.
  - **P2 WHEN** this sprint closes, **THEN** the Book **SHALL** distinguish offline gate tests, live pass/failure and not-run evidence, keep INT-0004 unfinished and T-202 queued, and make no native/static, adaptive-policy or general model-quality claim.
- **Notes:** Runtime failures may yield a useful negative finding; they do not erase failed planned checks. A resource rejection is a valid T-208 branch with live AC2 unproven. Follow the Test/Loop phase contracts for the eventual sprint verdict and human-approved merge checkpoint.
