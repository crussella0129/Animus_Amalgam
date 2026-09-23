# Sprint 1 Test Plan

These are document and evidence verification procedures. They are not source-shape unit tests, runtime model benchmarks, or permanent test code added only to check reversible documentation.

## Intent Traceability

| Intent | Acceptance criterion | Build task / EARS clause | Verification |
|---|---|---|---|
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC1: pinned predecessor chapters | T-101 clauses 1-2; T-102 clauses 1-2 | `ferric_evidence_audit`; `kinesin_evidence_audit` |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC2 and boundary: three-system architecture comparison plus language/runtime transferability | T-104 clauses 1-2; T-103 clauses 1-2 | `hermes_path_audit`; `comparison_coverage` |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC3: stable lessons register | T-103 clause 3 | `lessons_integrity` |
| [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) | AC4: detailed intents cite lessons | T-105 clauses 1-2 | `intent_traceability`; `book_navigation_e2e` |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC1: detailed, scoped, observable criteria | T-105 clauses 1-2 | `intent_traceability`; `scope_and_content_review` |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC2: definition, rationale, and rejected/deferred alternatives for adaptive | T-105 clause 1 | `intent_traceability` |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC3: separate policy, enforcement, semantics, resources; existing seam first | T-104 clauses 1-2; T-103 clause 1; T-108 clauses 1-2 | `hermes_path_audit`; `comparison_coverage`; `experiment_gate_review` |
| [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) | AC4: session evidence and bounded comparison | T-107 clauses 1-2; T-108 clauses 1-2 | `session_receipt_audit`; `experiment_gate_review` |

## Unit Tests

### T-101 document checks
- **Intent:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- `ferric_evidence_audit` (T-101 clauses 1-2): resolve every pinned path and line anchor, inspect claim/source pairs, and verify negative-result and adapter-correction boundaries.

### T-102 document checks
- **Intent:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md)
- `kinesin_evidence_audit` (T-102 clauses 1-2): inspect the required intents and Sprint 15/16 evidence; verify byte/token and cache-causality distinctions.

### T-104 document checks
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `hermes_path_audit` (T-104 clauses 1-2): verify source coordinates/version labels and trace a coherent request path without executing a model.

### T-107 document checks
- **Intent:** [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `session_receipt_audit` (T-107 clauses 1-2): reconcile sampled rows with the identified log/database coordinates; screen committed output for secrets, raw private artifacts, and causal overclaims.

### T-103 document checks
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `comparison_coverage` (T-103 clauses 1-2): verify all named comparison dimensions for Ferric, Kinesin, and Hermes, and label each adopted/adapted mechanism as language/runtime independent or Rust-, runtime-, or backend-dependent.
- `lessons_integrity` (T-103 clause 3): verify unique lesson IDs, a disposition, and resolvable evidence for every row.

### T-108 document checks
- **Intent:** [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `experiment_gate_review` (T-108 clauses 1-2): trace every measured risk to an observable metric, control, stop condition, or explicit unknown; ensure the protocol does not assume a managed-growth toggle.

### T-105 document checks
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `intent_traceability` (T-105 clauses 1-2): verify every detailed acceptance clause cites lessons and planned evidence, preserves state history, records the adaptive definition with its rationale and rejected/deferred alternatives, and keeps implementation distinct from research.
- `scope_and_content_review` (T-105 clause 2; T-104 clause 2; T-107 clause 1): verify the diff contains only authorized Book documents and no raw user-state artifacts, live configuration, upstream implementation changes, or unrelated local changes.

## Integration Tests

### Cross-artifact consistency
- **Intents:** [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md), [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md)
- `comparison_coverage` (T-103 clauses 1-2): predecessor and Hermes chapters compose into every required comparison and transferability dimension without changing source claims.
- `intent_traceability` (T-105 clauses 1-2): the lessons register, evaluation protocol, detailed intents, task ledger, metadata, and navigation agree on state and scope.
- Structural checks: run the installed `check-book.sh`, `check-substrate.sh`, `research-budget.sh` with its recorded override, and `git diff --check`.

## End-to-End Tests

- **Status:** possible for the Book; runtime qualification is deferred to a proposed follow-on intent created by T-105.
- `book_navigation_e2e` (T-105 clause 2): follow `SUMMARY.md` to each intent, plan/task, lineage chapter, lessons entry, evaluation protocol, and evidence artifact; every relative target resolves and no second state authority appears.
- The future bounded-local-evaluation intent unlocks runtime E2E evidence: fixed-context startup, request cancellation, paired baseline/static/adaptive runs, resource stop conditions, independent task checks, and backend cache/timing receipts.

After required task and phase commits, the installed `check-tracked.sh` must report a clean Book. A documentation check pass must never be reported as a successful model benchmark.
