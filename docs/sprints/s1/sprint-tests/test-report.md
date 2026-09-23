# Sprint 1 Test Report

## Intent Verification

| Intent | Acceptance criterion | EARS / tests | Result | Intent evidence update |
|---|---|---|---|---|
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC1: pinned Ferric and Kinesin chapters cover successes, failures, and abandoned/superseded directions | T-101 clauses 1-2 / `ferric_evidence_audit`; T-102 clauses 1-2 / `kinesin_evidence_audit` | pass | Test evidence links this report; completion and documentation evidence identify the finished chapters and task ledger. |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC2 and boundary: three-system comparison plus language/runtime transferability | T-104 clauses 1-2 / `hermes_path_audit`; T-103 clauses 1-2 / `comparison_coverage` | pass | The comparison covers seven required dimensions and four transfer categories. |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC3: stable lessons register | T-103 clause 3 / `lessons_integrity` | pass | Fourteen unique sequential lessons have allowed dispositions and resolvable evidence. |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC4: detailed AACD intents cite the register | T-105 clauses 1-2 / `intent_traceability`; `book_navigation_e2e` | pass | INT-0004 through INT-0006 explicitly map L-01 through L-14 and queue their gated follow-on tasks. |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC1: detailed scope and observable follow-on criteria | T-105 clauses 1-2 / `intent_traceability`; `scope_and_content_review` | pass | INT-0004/0005/0006 replace the provisional criteria without claiming implementation. |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC2: adaptive definition, rationale, and alternatives | T-105 clause 1 / `intent_traceability` | pass | INT-0005 defines deterministic, logged adaptation and records rejected/deferred alternatives. |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC3: separate policy, enforcement, semantics, resources; existing seam first | T-104 clauses 1-2 / `hermes_path_audit`; T-103 clauses 1-2 / `comparison_coverage`; T-108 clauses 1-2 / `experiment_gate_review` | pass | The custom endpoint is the control; service/plugin/engine work remains conditional on measured gaps. |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC4: sanitized session evidence and bounded comparison | T-107 clauses 1-2 / `session_receipt_audit`; T-108 clauses 1-2 / `experiment_gate_review` | pass | Four private fingerprints still match, causal unknowns remain explicit, and the future protocol has bounded native/static/adaptive gates. |

## Summary

- Unit tests: 9 passed / 0 failed / 9 total
- Integration tests: 3 passed / 0 failed / 3 total
- E2E tests: 1 passed / 0 failed / 1 total
- CI status: not-configured

## CI Confirmation

- **Head SHA:** `ebc5ff0524c06f3b9e16415792e99bd73909dc59`
- **CI run:** CI not configured — local confirmations only
- **Conclusion:** success
- **Confirmations:** [unit results](unit-tests.md),
  [integration results](integration-tests.md), and
  [E2E result](e2e-tests.md). The installed Book checks reported a valid
  six-intent v2 Book, `substrate-complete`, and research budget `files=20
  sources=5`; `git diff --check` was clean. The evidence checks resolved 25
  predecessor source objects and 24 line anchors, 30 Hermes source/test
  objects, all seven Sprint 1 task commits, and all four private evidence
  fingerprints. The terminal navigation scan resolved 187 local links and
  heading anchors across 36 stable Book and Sprint 1 documents.

The upstream Python runner was not applicable to this docs-only sprint. No
source code changed, and the locked plan specified document/evidence checks.

## Failures

None. The first two critic passes blocked on a missing Kinesin successor,
implicit lesson mappings, and then a stale tested-head reference. The
corrections are preserved in [critique 01](critique-01.md) and
[critique 02](critique-02.md); the [final critique](critique.md) is clean.

## Technical Debt Identified

- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
  owns the still-unrun fixed-context resource and native/static qualification.
- [INT-0005](../../../intents/INT-0005-adaptive-action-policy.md) owns adaptive
  policy only after INT-0004 establishes a safe control.
- [INT-0006](../../../intents/INT-0006-constraint-engine-research.md) remains
  conditional on a reproducible existing-engine gap.
- T-106 retains the separate upstream-sync and reusable Book-test-harness
  follow-up; it was outside Sprint 1's AACD research scope.

## Coverage Observations

- Documentation verification proves the research and intent contracts. It is
  not evidence that a local model, static grammar, adaptive policy, provider,
  sidecar, or new decoder succeeds at runtime.
- The supplied session establishes prompt/cache/resource events but does not
  measure peak RSS/commit, live RAM/VRAM headroom, paging, thermals, or exact
  crash causality. INT-0004 requires those receipts.
- No external CI run exists for this local docs-only verification. All
  authoritative confirmations are linked above and identify the tested head.
