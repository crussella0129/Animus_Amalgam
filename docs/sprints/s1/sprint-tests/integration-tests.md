# Sprint 1 Integration Test Results

- **Tested build head:** `1e3c15a9606fb23e6af35ca92b4dbb86ebd21f4f`
- **Date:** 2026-09-23

## Results

| Test | Intent / EARS coverage | Result | Cross-artifact assertion |
|---|---|---|---|
| `comparison_coverage` | INT-0002 AC2; INT-0003 AC3; T-103 clauses 1-2 | pass | The pinned Ferric and Kinesin chapters and the version-labeled Hermes chapter feed every required comparison dimension. The comparison's recommended custom-endpoint baseline, conditional Rust service/plugin, and deferred decoder agree with the lessons register and evaluation protocol without changing the source claims. |
| `intent_traceability` | INT-0002 AC4; INT-0003 AC1-4; T-105 clauses 1-2 | pass | All lessons trace explicitly: INT-0004 cites L-04, L-07 through L-09, and L-12/L-13; INT-0005 cites L-01 through L-06, L-10/L-11, and L-13; INT-0006 cites L-14. Those intents trace to T-201 through T-205; INT-0003 preserves its transition history and records the superseding chapters. The plan, completed-task ledger, backlog, intent headers, lineage chapters, and navigation agree that Sprint 1 produced research and proposals, not an AACD implementation or model qualification. |
| `book_schema_integration` | all Sprint 1 EARS clauses | pass | The installed validators report `check-book: valid v2 Book (6 intent chapters)`, `substrate-complete`, and `files=20 sources=5`. `git diff --check` is clean. A relative-link/anchor scan resolved 153 links across 33 Sprint 1 and stable Book documents before these result pages were populated; the E2E result below records the post-edit navigation pass. |

## Canonical confirmations

The project's runtime runner, `scripts/run_tests.sh`, was not invoked because
Sprint 1 changed Book Markdown only and its locked plan explicitly defines
document/evidence checks rather than Python behavior tests. The canonical
Sprint Loops Book validators were run instead:

```text
check-book: valid v2 Book (6 intent chapters)
substrate-complete
files=20 sources=5
git-diff-check: clean
```

No integration result repeats a runtime unit test: these checks validate the
relationships among pinned sources, synthesized lessons, intent lifecycle,
task state, and Book structure.
