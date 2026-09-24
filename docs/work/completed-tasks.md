# Completed Tasks Log (Append-Only)

## T-001 (sprint 0)
- **Description:** Write the Book front matter (project identity, purpose, authority order, upstream boundary, intent index)
- **Intent:** [INT-0001](../intents/INT-0001-project-book-and-sprint-substrate.md)
- **Completed:** 2026-09-21T17:42:31Z
- **Files modified:** docs/README.md, docs/intents/README.md, docs/intents/INT-0001-project-book-and-sprint-substrate.md
- **Commit:** `c79d3a6a37b68c63899af13b10b6bb8910c907c0`

## T-002 (sprint 0)
- **Description:** Queue the Sprint 1 backlog (T-101 to T-106) and link each task from its intent's Work evidence
- **Intent:** [INT-0001](../intents/INT-0001-project-book-and-sprint-substrate.md)
- **Completed:** 2026-09-21T17:43:28Z
- **Files modified:** docs/work/tasks.md, docs/intents/INT-0001-project-book-and-sprint-substrate.md, docs/intents/INT-0002-lineage-lessons-ferric-kinesin.md, docs/intents/INT-0003-animus-adaptive-constrained-decoding.md
- **Commit:** `a6525d168dc26a5cf11c05e97cf662598850fece`

## T-101 (sprint 1)
- **Description:** Publish the commit-pinned Animus_Ferric architecture, successes, failures, and transfer boundaries
- **Intent:** [INT-0002](../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- **Completed:** 2026-09-23T15:40:42Z
- **Files modified:** docs/lineage/animus-ferric.md, docs/SUMMARY.md, docs/intents/INT-0002-lineage-lessons-ferric-kinesin.md
- **Commit:** `626c39c8186ad98c0ad70e5c79b1df61a293e1a3`

## T-102 (sprint 1)
- **Description:** Publish the commit-pinned Kinesin architecture, successes, failures, superseded claims, and transfer boundaries
- **Intent:** [INT-0002](../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- **Completed:** 2026-09-23T15:43:03Z
- **Files modified:** docs/lineage/kinesin.md, docs/SUMMARY.md
- **Commit:** `ab4fb4ea007ec939c08d69d433c590424a781520`

## T-104 (sprint 1)
- **Description:** Publish Hermes's existing constrained-decoding attachment points, cache invariants, context behavior, and implementation test seams
- **Intent:** [INT-0002](../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Completed:** 2026-09-23T15:46:30Z
- **Files modified:** docs/lineage/hermes-decoding-seams.md, docs/SUMMARY.md, docs/intents/INT-0003-animus-adaptive-constrained-decoding.md
- **Commit:** `4e86662d4b9feae37a8e29544afcb428a80d3cd4`

## T-107 (sprint 1)
- **Description:** Publish a sanitized, measured case study of the owner's long local Qwen Hermes session
- **Intent:** [INT-0003](../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Completed:** 2026-09-23T15:50:34Z
- **Files modified:** docs/lineage/local-session-case-study.md, docs/SUMMARY.md
- **Commit:** `358d80065b698df311d5083e1f4159fa56e24bbb`

## T-103 (sprint 1)
- **Description:** Publish the three-system architecture comparison and stable Amalgam lessons register
- **Intent:** [INT-0002](../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Completed:** 2026-09-23T15:52:55Z
- **Files modified:** docs/lineage/architecture-comparison.md, docs/lineage/lessons-register.md, docs/SUMMARY.md
- **Commit:** `9f779fa487f6512a3164657124a0db039892520e`

## T-108 (sprint 1)
- **Description:** Publish the bounded local-model evaluation protocol and architecture advancement gates
- **Intent:** [INT-0003](../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Completed:** 2026-09-23T15:55:46Z
- **Files modified:** docs/lineage/local-evaluation-protocol.md, docs/SUMMARY.md
- **Commit:** `fa8e9e55c6b0aec9d0267f877fd044f828cecbdf`

## T-105 (sprint 1)
- **Description:** Supersede the coarse AACD chapter with detailed bounded-baseline, adaptive-policy, and conditional-decoder intents
- **Intent:** [INT-0003](../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Completed:** 2026-09-23T15:58:45Z
- **Files modified:** docs/intents/INT-0003-animus-adaptive-constrained-decoding.md, docs/intents/INT-0004-bounded-local-model-qualification.md, docs/intents/INT-0005-adaptive-action-policy.md, docs/intents/INT-0006-constraint-engine-research.md, docs/intents/README.md, docs/README.md, docs/SUMMARY.md, docs/work/tasks.md
- **Commit:** `58d756c2df62cdf2a51a129b4355af803aea0ddb`

## T-201 (sprint 2)
- **Description:** Bring up a disposable environment and record the candidate. M1: every attempt resolves to a published manifest with artifact/tokenizer/template/runtime hashes, source commit, dependencies, limits, task corpus, seed, toolset and an explicit pre-admission `not-measured` rendered prefix. M2: identity/admission refusals are exact (attempts 03-04; `identity_mismatch`/`admitted` contracts). Realized across 1f6abe7eca, 04d40088b5, c42152ca0b and this entry.
- **Intent:** [INT-0004](../intents/INT-0004-bounded-local-model-qualification.md)
- **Completed:** 2026-09-24T16:49:29Z
- **Files modified:** evals/local_qualification/prepare.py, evals/local_qualification/README.md, hermes_cli/local_runtime/gguf.py, docs/sprints/s2/sprint-tests/qualification/manifests/
- **Commit:** `05330b2e7dddbe818f4133ad40b2a5a59a6b2aeb`

## T-206 (sprint 2)
- **Description:** Add only observation and stop controls needed for operation. S1: the existing kill-on-close Job Object owner (reused, not duplicated) terminated every owned tree within 5 s in attempts 08-11 while an unrelated sentinel survived; the Windows-only regression test_owner_exit_kills_router_tree_not_external pins owner loss. S2: identity, admission, reserve and paging stops are pure policy decisions with no model callback or retry, pinned by test_local_qualification_policy; the post-load page-in stop applies only under RAM pressure (owner continuation 2).
- **Intent:** [INT-0004](../intents/INT-0004-bounded-local-model-qualification.md)
- **Completed:** 2026-09-24T16:54:16Z
- **Files modified:** evals/local_qualification/policy.py, evals/local_qualification/run.py, evals/local_qualification/prepare.py, evals/local_qualification/telemetry.py, tests/evals/test_local_qualification_policy.py
- **Commit:** `501ff12df51b5c390a6fcc8e2bdc6be5d3ccb4d4`

## T-207 (sprint 2)
- **Description:** Wire the real Hermes entry point and observe requests. D1: the real HermesCLI main path and the real compress_now path sent every request through the lab wire to the pinned amalgam-pilot endpoint, one physical request at a time, with original and bounded bodies recorded and a 128-token backend cap (attempts 06-11); test_local_qualification_wire pins the bound, single forwarding and preserved original. D2: oversized rendered input or a wrong model never reaches generation (wire test; attempt 08 refused 5481 tokens live); auxiliary cancellation covered the actual compression request (attempt 11). Reproduced Hermes defect repaired at its source: the 64K floor now admits an explicitly pinned local custom window only with automatic compression disabled (fa747be391; regression test proven red on the pre-fix code).
- **Intent:** [INT-0004](../intents/INT-0004-bounded-local-model-qualification.md)
- **Completed:** 2026-09-24T16:54:28Z
- **Files modified:** agent/agent_init.py, evals/local_qualification/driver.py, evals/local_qualification/wire.py, tests/evals/test_local_qualification_wire.py, tests/agent/test_minimum_context_explicit_local.py
- **Commit:** `e5965195a85258a3a9f7edaa84d5e128a1cd60e0`

## T-208 (sprint 2)
- **Description:** Operate isolated 27B Hermes; diagnose, repair and replay failures. R1: admission refusals recorded exact shortfalls with zero inference (attempts 03, 04, 12). R2: smokes ran inside the frozen envelope with independent answer checks, timing/cache observations and resource extrema (07, 08, 09, 10, 13). R3: main (10) and auxiliary compression (11) cancellation were each triggered with the slot processing and finished owned cleanup in 2.6 s and 1.8 s. R4: the ledger links every failure, diagnosis, repair revision and replay. Attempt 10 completed the independently checked read/edit/check/recover task in a continued session. Operational confidence was declared after attempt 11, before any formal suite ran.
- **Intent:** [INT-0004](../intents/INT-0004-bounded-local-model-qualification.md)
- **Completed:** 2026-09-24T16:59:31Z
- **Files modified:** docs/sprints/s2/sprint-tests/operational-ledger.md, docs/sprints/s2/sprint-tests/qualification/attempts.json, docs/sprints/s2/sprint-tests/qualification/manifests/, evals/local_qualification/{driver,run,prepare,wire,telemetry}.py (repair commits d09b9470b3 through c42152ca0b)
- **Commit:** `d5b94380bd035e8798d6d4b04fa2c6766f6e2278`

## T-209 (sprint 2)
- **Description:** After operational confidence, run focused formal checks and publish evidence. The formal suites ran only after the attempt-11 confidence record: 12 new contract tests plus the existing affected coverage, all green on head. The affected-suite regression check against pre-sprint cd2185c288 found identical failing test IDs (120 on both), so zero regressions. P1: the receipt audit found 13 attempts resolving to 9 digest-valid manifests, every stop cause preserved, pre-admission unknowns labeled, and no user paths, credentials or tokens. P2: INT-0004 stays active with AC3/AC5/AC6 on T-202, and no native/static, adaptive or model-quality claim is made.
- **Intent:** [INT-0004](../intents/INT-0004-bounded-local-model-qualification.md)
- **Completed:** 2026-09-24T18:22:29Z
- **Files modified:** docs/sprints/s2/sprint-tests/unit-tests.md, docs/sprints/s2/sprint-tests/integration-tests.md, docs/sprints/s2/sprint-tests/e2e-tests.md, docs/sprints/s2/sprint-meta.md, docs/intents/INT-0004-bounded-local-model-qualification.md
- **Commit:** PENDING
