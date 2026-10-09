# Test Critique — Sprint 3

Round 7, an independent read-only critic run at head `f56cf5f195`, after
the round-6 response. It passed with caveats. Each caveat is addressed in
the round-7 response commits. The dispositions are in the
[test report](test-report.md), and the re-review is in
[critique](critique.md).

## Concerns

### C-001: The policy's echo prefill saving and its peak-input figure are contradicted by the published receipts
- **Where:** `docs/lineage/local-operating-policy.md`: the "Reasoning echo" paragraph, recommended default 2, and the Context row; `policy_evidence_review` in `e2e-tests.md`
- **Quote:** "Echo removed about 60% of the prefill work"; "Peak rendered input was 7,867 tokens."
- **Failure mode:** evidence-drift
- **Why it matters:**
  - Attempt 09 (R1, echo off) has 7,943 uncached prompt tokens and 93.7 s of prompt time. Attempt 13 (R2, echo on) has 8,259 tokens and 90.3 s.
  - Only the median uncached tokens per continued request fell, from 161 to 60.
  - The peak rendered input was 9,935 tokens (attempt 13).
  - The echo-on recommendation cites a saving the receipts do not show.
- **Suggested response:** tighten-assertion. Restate the saving as the median, with the totals beside it, correct the peak, and re-record P1.

### C-002: The published screen receipt records three arms as contaminated twice, but the policy ranks them from an unpublished re-scan
- **Where:** `qualification/attempt-06-screen.json`; `screen.py`; the policy's "Sampling" table; `live_sampling_screen`
- **Quote:** the published events include `contaminated_twice` for sessions 5, 7 and 11. The policy says "greedy 259 s < model default (1.0 / 0.95 / 20) 319 s".
- **Failure mode:** evidence-drift
- **Why it matters:** By the published evidence, off-model-default and on-mid-probe are L4 failures. The ranking rests on `screen.py`'s re-scan, which is unpublished, and nothing ties the published evidence to the recorded `screen_winners`.
- **Suggested response:** add-test. Publish the re-scanned verdicts beside the live ones, and assert that ranking them reproduces `screen_winners`.

### C-003: The round-6 schema-3 receipt rules can never run, so the C-003 "Fixed" disposition does not hold
- **Where:** `test_local_qualification_receipts.py` reads only Sprint 3's directory; `prepare.py` `"schema": 3`; backlog T-224, which publishes under `docs/sprints/s4/`
- **Quote:** "Only receipts from schema-2 manifests (the live runs) may use the exceptions; the repaired lab writes schema 3 (round 6)."
- **Failure mode:** weak-assertion
- **Why it matters:** All 13 published manifests are schema 2, and the suite would never read Sprint 4's receipts. T-224's checklist also omits `id_slot` and `decoded_tokens_observed`.
- **Suggested response:** defer-with-rationale. Make the suite read the replay's receipts, name it as T-224's acceptance check, add the missing items, and reword the disposition.

### C-004: The decoded-token "upper bound" for stopped requests is not a bound by the receipts' own decode rates, and its inputs are unpublished
- **Where:** the ledger's round-6 corrections; the test report's AC2 row and round-6 C-001 disposition; the policy note; T-216's correction
- **Quote:** "Their time after prefill bounds the missing decode at the calibrated rate"; "Decode slows as context grows, so the true counts are lower."
- **Failure mode:** evidence-drift
- **Why it matters:** 23 of 162 completed requests decoded faster than 3.55 tok/s, the fastest at 3.743. In attempt 12, 7 of 10 ran above 3.55. The seconds-after-prefill inputs are in no published receipt.
- **Suggested response:** tighten-assertion. Bound at the fastest rate the receipts show, or call it an estimate, and publish the inputs.

## Confidence
proceed-with-caveats
