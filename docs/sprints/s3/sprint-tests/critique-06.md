# Test Critique — Sprint 3

Round 6, an independent read-only critic run at head `cf895ec191`, after
the round-5 response. It passed with caveats. Each caveat is addressed in
the round-6 response commits. The dispositions are in the
[test report](test-report.md), and the re-review is in
[critique](critique.md).

## Concerns

### C-001: Stopped requests' decoded tokens are never named missing, so O1 and the policy count them as zero
- **Where:** `publish.REQUEST_FIELDS` has no `decoded_tokens`; `run.stopped_request` carries no decode count; `test_completed_calibrated_requests_carry_every_l1_and_m3_field`; the policy's ranking rows 1 and 3; the ledger's round-2 O1 table; build-plan O1 and INT-0007 AC2
- **Quote:** "**205.3 s**, 557.5 tokens" (R0) and "**384.3 s**, 1,171.6 tokens" (R2). These give 0 tokens to the stopped requests of attempts 07, 11 and 12, whose machine time is counted.
- **Failure mode:** evidence-drift
- **Why it matters:** The token figures are lower bounds but read as exact. The repaired stop path still records no decode count. The time ranking is not affected.
- **Suggested response:** tighten-assertion. Add `decoded_tokens` to the named-missing set, carry the last `/slots` decode count in `stopped_request`, and label the token figures.

### C-002: The capture backend computes the decode count from the wire's own tool-call string, so "the parts add up" holds only in the test double
- **Where:** `CaptureBackend.chunks` and `test_streamed_tool_call_is_reassembled_and_counted`; the integration-tests row; the test-report round-5 C-002 disposition; the README
- **Quote:** `answer_words = len(f"terminal {self.tool_arguments}".split())` and `predicted_n: decoded`, against `reasoning + visible + tool_call == predicted_n`.
- **Failure mode:** stub-leak
- **Why it matters:** Real output always leaves a markup remainder, and the equality cannot catch an over-count that would make the remainder negative. No published receipt counts tool-call tokens yet.
- **Suggested response:** tighten-assertion. Give the double a markup overhead, assert that the parts are at most the decoded count and that the published remainder equals the overhead, and fix the wording.

### C-003: The receipt tests do not hold post-round-5 receipts to the new behavior, though T-224 relies on them
- **Where:** `LATER_FIELDS` in `test_completed_calibrated_requests_carry_every_l1_and_m3_field`; `test_long_sessions_validate_every_delivered_tool_call`; `test_attempt_stopped_long_sessions_are_scored`; backlog T-224
- **Quote:** the exemptions apply to every receipt, whatever its source; `assert 0 <= unvalidated <= cut`; `assert len(session["tool_calls"]) == screened["tool_calls"]`.
- **Failure mode:** weak-assertion
- **Why it matters:** A replay receipt whose wire dropped the new fields, or left a cut call unvalidated, would still pass. A correct cut-short receipt whose history dropped a cap-cut call would fail.
- **Suggested response:** tighten-assertion. Scope the exemptions to receipts recorded before the repair, require `unvalidated_tool_calls == 0` after it, and relax the screened equality to allow only cap-cut calls missing from the history.

### C-004: Small record drifts left by round 5
- **Where:**
  - the published request records, which carry `"tool_call_validity": null`;
  - the test-report INT-0007 AC7 row, which names only `id_slot` missing;
  - the T-211 and T-210 completion entries, which describe validity and the split as they were before round 5;
  - INT-0004's documentation evidence, which links only the Sprint 2 ledger.
- **Quote:** "carry every L1 field, asserted by presence; `id_slot` is named missing"
- **Failure mode:** evidence-drift
- **Why it matters:** The records describe the code and receipts before round 5 in places. No acceptance claim changes.
- **Suggested response:** tighten-assertion (wording only).

## Confidence
proceed-with-caveats
