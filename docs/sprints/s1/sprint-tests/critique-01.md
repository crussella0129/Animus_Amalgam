# Test Critique — Sprint 1 (first pass)

## Concerns

### C-001: Kinesin cache successor is missing despite a passing successor audit

- **Where:** `unit-tests.md` `kinesin_evidence_audit`; locked `build-plan.md`
  T-102 clause 1; `docs/lineage/kinesin.md` “Failures and superseded claims.”
- **Quote:** The executed result claims coverage of “INT-0004/0008/0011/0015
  with successor limits.” The chapter's INT-0004 paragraph describes the
  corrected observation but does not identify its successor.
- **Failure mode:** weak-assertion
- **Why it matters:** At pinned Kinesin commit
  `a4491211e605d2358e0e1daa00598920c8b213dd`, INT-0004's transition history
  explicitly names **INT-0026 — Session context continuity** as its successor.
  T-102 promises successor coverage, but this successor and its continuing
  ownership of unproved session/lifetime criteria are absent from the chapter.
- **Suggested response:** tighten-assertion — identify and link INT-0026 at the
  pinned commit, preserve its qualification limits, and rerun a
  successor-by-successor audit before reporting T-102 clause 1 as passed.

### C-002: Integration receipt overstates lesson-to-intent traceability

- **Where:** `integration-tests.md` `intent_traceability`;
  INT-0004/0005/0006 rationale and acceptance criteria.
- **Quote:** “`L-01` through `L-14` trace into INT-0004/0005/0006.”
- **Failure mode:** evidence-drift
- **Why it matters:** The explicit lesson citations collectively cover
  L-01–L-05, L-07, L-09, L-10, and L-12–L-14; L-06, L-08, and L-11 lack that
  recorded mapping. Some corresponding ideas appear implicitly, but the
  receipt presents complete traceability without identifying their destination
  or deferral.
- **Suggested response:** tighten-assertion — record the actual
  lesson-to-criterion/boundary mappings, explicitly identify deferred or
  unmapped lessons, and narrow the passing claim accordingly. Add stable
  citations where those lessons already govern a successor intent.

## Confidence

block
