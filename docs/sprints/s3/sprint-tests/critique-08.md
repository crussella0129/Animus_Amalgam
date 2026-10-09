# Test Critique — Sprint 3

Round 8, an independent read-only critic run at head `4e55d1be05`, after
the round-7 response. It passed with caveats. Each caveat is addressed in
the round-8 response commits. The dispositions are in the
[test report](test-report.md), and the re-review is in
[critique](critique.md).

## Concerns

### C-001: The thinking-off screen ranking leaves out attempt 05's cut-short off-greedy session, and no record says so. Under the sprint's own O1 reading the winner changes
- **Where:**
  - `qualification/attempt-05-screen.json`: session 3, `off-greedy`, `long:1-3`, 3 requests, 116.016 s, 0 verified, stopped by the telemetry read race;
  - the policy's "Sampling" table and recommended default 1;
  - `live_sampling_screen`;
  - the ledger's attempt-06 table;
  - the test report's AC2 row.
- **Quote:** "Under the plan's rule (build-plan O1), failures and stops count", against "Thinking off | greedy 259 s < model default (1.0 / 0.95 / 20) 319 s".
- **Failure mode:** evidence-drift
- **Why it matters:** Counted the way attempt 07 is counted for R0, greedy costs (259.406 + 116.016) / 1 = 375.4 s per verified item, against model default's 318.5 s (320.0 s pooled). The off-mode winner then depends on treating attempt 05 as a replayed lab failure, and no record states that exclusion.
- **Suggested response:** defer-with-rationale. State that S2 ranks the completed screen (attempt 06), give the all-attempts figures beside it, and note the full-length comparison as unmeasured.

### C-002: INT-0004 AC1's identity fields are not asserted on any Sprint 3 manifest, yet AC1 is reported "Closed"
- **Where:** `test_every_published_attempt_resolves_to_its_manifest`; the identity checks live only in `test_local_qualification_policy.py`, which reads Sprint 2; the test report's INT-0004 row
- **Quote:** "AC1 and AC4 (identity, correlated receipts) | **Closed.**"
- **Failure mode:** weak-assertion
- **Why it matters:** A Sprint 3 manifest missing a tokenizer hash, the corpus hash or the source commit would still pass. The published manifests do carry them, so no claim is false today.
- **Suggested response:** tighten-assertion. Apply the identity fields and hash checks to every published manifest.

### C-003: Small record drifts left after round 7
- **Where:**
  - the test report's AC2 row;
  - the test name `test_a_stopped_requests_unreturned_decode_is_bounded_by_the_receipt` and a `publish.py` comment;
  - INT-0007's work evidence.
- **Quote:** "it is about 586.1 at most", against "This is an estimate from the receipts, not a strict bound."
- **Failure mode:** evidence-drift
- **Why it matters:**
  - The AC2 row calls the estimate a bound.
  - INT-0007's work evidence omits T-223 and T-224, which are tagged to it.
- **Suggested response:** tighten-assertion (wording and links only).

## Confidence
proceed-with-caveats
