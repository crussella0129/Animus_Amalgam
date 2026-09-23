# Plan Critique — Sprint 1 (first pass)

## Concerns

### C-001: Adaptive rationale and rejected alternatives lack explicit verification
- **Where:** `INT-0003-animus-adaptive-constrained-decoding.md` AC2; `build-plan.md` T-105 clause 1; `test-plan.md` `intent_traceability`.
- **Quote:** AC2 requires “a definition of ‘adaptive’, with its rationale and the alternatives that were rejected.” T-105 required only deterministic adaptation and metrics/invariants.
- **Failure mode:** plan-test-mismatch
- **Why it matters:** The stable intent could omit the reasoning and rejected alternatives required by AC2.
- **Suggested response:** fix-in-plan
- **Response:** Addressed by extending T-105 clause 1 and `intent_traceability` to require the definition, rationale, evaluated alternatives, and reasons for rejection or continued deferral.

### C-002: Language and runtime transferability distinction is not covered
- **Where:** `INT-0002-lineage-lessons-ferric-kinesin.md` Boundaries; `build-plan.md` T-103; `test-plan.md` `comparison_coverage`.
- **Quote:** INT-0002 requires the analysis to distinguish lessons that hold regardless of language/runtime from Rust- or backend-dependent mechanisms.
- **Failure mode:** intent-drift
- **Why it matters:** Accurate system descriptions alone would not prove which parts can be reused in Amalgam.
- **Suggested response:** fix-in-plan
- **Response:** Addressed by adding a T-103 transferability clause and explicit `comparison_coverage` checks.

## Confidence

block
