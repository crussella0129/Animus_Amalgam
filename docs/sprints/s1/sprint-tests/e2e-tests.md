# Sprint 1 End-to-End Test Results

- **Tested build head:** `1e3c15a9606fb23e6af35ca92b4dbb86ebd21f4f`
- **Date:** 2026-09-23

## `book_navigation_e2e`

- **Input:** begin at [`docs/SUMMARY.md`](../../../SUMMARY.md) and follow the
  links through project intent, Sprint 1 plans and results, work ledgers,
  predecessor/Hermes chapters, the lessons register, the evaluation protocol,
  and detailed follow-on intents.
- **Expected output:** every local target and Markdown heading anchor resolves;
  lifecycle state remains in intent headers and does not appear as a competing
  authority in the navigation page.
- **Result:** pass. A post-edit resolver traversed 160 local links and heading
  anchors across 34 stable Book and Sprint 1 documents and found no missing
  target. This count precedes the required critique/report links; the final
  test report records the terminal navigation check.

## Runtime E2E boundary

Runtime local-model E2E is intentionally not a Sprint 1 result. No model was
started, no live profile was changed, and this documentation pass is not a
successful benchmark. [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md)
and backlog tasks T-201/T-202 unlock the fixed-context smoke, cancellation,
native/static paired trials, resource receipts, and independent task checks.
INT-0005 later unlocks a paired adaptive arm, and INT-0006 remains conditional
on a reproduced constraint-engine gap.

Deferral is required by the locked scope: the owner approved architecture
research and a bounded protocol, while exact model priority and acceptable
interactive latency remain explicit owner inputs for T-201.
