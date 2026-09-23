Finalized - DO NOT EDIT

# Sprint 1 Build Plan

## Intents

- [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) — state: planned; acceptance criteria covered: 1-4.
- [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) — state: planned; provisional acceptance criteria covered: 1-4. This sprint replaces provisional research criteria with detailed follow-on intent proposals; it does not implement AACD.

## Schema Tree

- Evidence-backed AACD architecture research
  - Pinned predecessor lineage
    - T-101: Ferric chapter
    - T-102: Kinesin chapter
  - Current-system evidence
    - T-104: Hermes attachment points
    - T-107: sanitized local-session case
  - Synthesis and decision boundary
    - T-103: architecture comparison and lessons register
    - T-108: bounded evaluation protocol
    - T-105: detailed AACD intent proposals

## Execution Sequence

### T-101: Publish the Ferric lineage chapter
- **Intent:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- **Touches:** `docs/lineage/animus-ferric.md`, `docs/SUMMARY.md`
- **Depends on:** (none; source research is `sprint-research/lineage-findings.md`)
- **Acceptance criterion:** INT-0002 AC1.
- **Success criterion (EARS):**
  - **WHEN** the chapter is reviewed, **THEN** every material success, failure, abandoned direction, and architecture claim **SHALL** link a source at full Ferric commit `51af84e933c0f6ff4a42f1508cb9aefad00847c5` and distinguish reported historical evidence from verified runtime code.
  - **WHEN** its reuse recommendation is read, **THEN** it **SHALL** distinguish `ferric-core` policy, `ferric-loop` grammar construction, external enforcement, the corrected native adapter, and the abandoned recovery-controller result.

### T-102: Publish the Kinesin lineage chapter
- **Intent:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- **Touches:** `docs/lineage/kinesin.md`, `docs/SUMMARY.md`
- **Depends on:** (none; source research is `sprint-research/lineage-findings.md`)
- **Acceptance criterion:** INT-0002 AC1.
- **Success criterion (EARS):**
  - **WHEN** the chapter is reviewed, **THEN** it **SHALL** cite the pinned tools/constraint contract, scoped positive observations, Sprint 15/16 failures, and superseded INT-0004/0008/0011/0015 with their successor and qualification limits.
  - **WHEN** its resource or cache claims are read, **THEN** byte budgets **SHALL** remain distinct from token budgets and observed cache reuse **SHALL** remain distinct from a causal `cache_prompt` benefit.

### T-104: Publish the Hermes integration chapter
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Touches:** `docs/lineage/hermes-decoding-seams.md`, `docs/SUMMARY.md`
- **Depends on:** (none; source research is `sprint-research/hermes-seams.md`)
- **Acceptance criterion:** INT-0002 AC2; INT-0003 AC3.
- **Success criterion (EARS):**
  - **WHEN** an integration path is evaluated, **THEN** the chapter **SHALL** identify the actual endpoint/profile/middleware/client path, its inputs and limits, native response semantics, and existing tool authority.
  - **WHEN** an adaptive or context policy is proposed, **THEN** the chapter **SHALL** state cache/profile invariants and the managed-growth-before-compression caveat, distinguish installed and fork source identities, and name applicable integration coverage for a later implementation.

### T-107: Publish the sanitized local-session case
- **Intent:** [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Touches:** `docs/lineage/local-session-case-study.md`, `docs/SUMMARY.md`
- **Depends on:** (none; source research is `sprint-research/local-session-evidence.md`)
- **Acceptance criterion:** INT-0003 AC4.
- **Success criterion (EARS):**
  - **WHEN** the case is reviewed, **THEN** its session/message identifiers and sampled token/cache/latency figures **SHALL** resolve to identified private evidence coordinates without committing raw logs, credentials, configuration, or transcript.
  - **WHEN** its conclusion is read, **THEN** it **SHALL** distinguish generation cost, cold prefill, restart/growth, and failed compression from unmeasured paging, memory peaks, thermals, and crash causality.

### T-103: Publish the comparison and stable lessons register
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Touches:** `docs/lineage/architecture-comparison.md`, `docs/lineage/lessons-register.md`, `docs/SUMMARY.md`
- **Depends on:** T-101, T-102, T-104, T-107
- **Acceptance criterion:** INT-0002 AC2-3; INT-0003 AC3.
- **Success criterion (EARS):**
  - **WHEN** the comparison is reviewed, **THEN** it **SHALL** cover enforcement location, shape versus semantics, adaptation, failure handling, backend dependencies, and cache/resource costs for Ferric, Kinesin, and Hermes.
  - **WHEN** a mechanism or lesson is recommended for Amalgam, **THEN** the comparison **SHALL** identify whether it is language/runtime independent or depends on Rust, a serving runtime, or a specific backend capability.
  - **WHEN** a lesson is cited, **THEN** it **SHALL** have a unique stable `L-NN` identifier, evidence links, and an `adopt`, `adapt`, `avoid`, or `open question` disposition.

### T-108: Publish a bounded local evaluation protocol
- **Intent:** [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Touches:** `docs/lineage/local-evaluation-protocol.md`, `docs/SUMMARY.md`
- **Depends on:** T-103, T-104, T-107
- **Acceptance criterion:** INT-0003 AC3-4.
- **Success criterion (EARS):**
  - **WHEN** the protocol is used to prepare a future experiment, **THEN** it **SHALL** specify fixed-context external-runtime isolation, an inventory and manifest, a small smoke/cancellation gate, provisional numeric resource/time limits, explicit stop conditions, measurements, and missing-data handling.
  - **WHEN** variants are compared, **THEN** the protocol **SHALL** hold model/configuration controls fixed, identify baseline native grammar, separate context-policy effects, use paired repeated trials and independent completion checks, and define advancement gates for adaptation and a new decoder.
- **Notes:** No benchmark runs in this sprint. In the absence of a contrary owner preference, the protocol starts with a smaller responsive model and retains the 27B model as a bounded comparison. Exact model and product latency targets remain future experiment inputs.

### T-105: Write detailed AACD intent proposals
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- **Touches:** `docs/intents/`, `docs/intents/README.md`, `docs/README.md`, `docs/SUMMARY.md`, `docs/work/tasks.md`
- **Depends on:** T-103, T-108
- **Acceptance criterion:** INT-0002 AC4; INT-0003 AC1-4.
- **Success criterion (EARS):**
  - **WHEN** detailed intent proposals are reviewed, **THEN** they **SHALL** cite stable lesson IDs and define deterministic adaptation, its supporting rationale, evaluated alternatives and reasons for rejection or continued deferral, backend scope, non-goals, semantic/authority/cache invariants, observable resource/task metrics, and acceptance gates without claiming implementation success.
  - **WHEN** the Book is handed back, **THEN** it **SHALL** separate the recommended first experiment from conditional provider/new-engine alternatives and leave future implementation tasks queued with unresolved owner decisions explicit.
- **Notes:** Preserve INT-0003 history. Do not declare AACD delivered. Follow-on implementation intents remain proposed until selected. T-106 remains backlog.
