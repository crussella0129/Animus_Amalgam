# Test Critique — Sprint 3

Round 9, an independent read-only critic run at head `7322017d5b`, after
the round-8 response. It passed with caveats. Each caveat is addressed in
the round-9 response commits. The dispositions are in the
[test report](test-report.md), and the re-review is in
[critique](critique.md).

## Concerns

### C-001: When the wire refuses a request because another one is already in flight, no receipt is written, and Sprint 3's only live retry is missing from the request receipts
- **Where:** `wire._handle`, where the refusal sends a 409 and records nothing; `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused`; `qualification/attempt-10-R2.json`; backlog T-224
- **Quote:** `assert results == {"a": 200, "b": 409}` / `assert "concurrent" in wire.failure`
- **Failure mode:** negative-path
- **Why it matters:** Every other refusal records a `wire_failure`. Attempt 10's retry after its cap-cut response was refused at this gate and left no request receipt.
- **Suggested response:** add-test. Record a `wire_failure` before the 409, assert it, and state the gap in the attempt-10 record.

### C-002: The round-8 identity check is weaker than the records say
- **Where:** `test_every_published_attempt_resolves_to_its_manifest`; the test report's INT-0004 row; the ledger's round-8 bullet
- **Quote:** "the manifest pins INT-0004 AC1's identity"
- **Failure mode:** weak-assertion
- **Why it matters:**
  - `backend.sha256` hashes only `llama-server.exe`. The CUDA and server libraries are hashed in `backend.libraries`, which is not asserted.
  - `source_dirty`, `interpreter` and `seed` are checked as keys only.
- **Suggested response:** tighten-assertion.

### C-003: The screen re-rank test takes its ranking inputs on trust, and the thinking-on pick rests on a 1.2% gap
- **Where:** `test_published_screen_reproduces_the_recorded_winners`; attempt 06's `screen.sessions`
- **Quote:** `winners, report = screen.report(published["sessions"])`
- **Failure mode:** weak-assertion
- **Why it matters:** The test does not tie `machine_s`, `decoded`, `arm`, `selectable` or `rerun_of` to the receipt, and it does not require every ended long session to be present. The thinking-on pick (514.7 s against 520.9 s) would survive a drifted block.
- **Suggested response:** tighten-assertion.

### C-004: Small record drifts left after round 8
- **Where:**
  - INT-0004's work evidence, which links completed tasks as plan tasks;
  - the V2 accounting, which explains 18 of the 20 API reds;
  - the `live_full_run_R2` attempt list;
  - the policy's live-profile proposal, which lacks the T-225 caveat.
- **Quote:** "The 7 API reds of rounds 1 and 2 … The 11 API reds of rounds 3 to 5"
- **Failure mode:** evidence-drift
- **Why it matters:** These are link and accounting slips. No acceptance claim changes.
- **Suggested response:** tighten-assertion (wording and links only).

## Confidence
proceed-with-caveats
