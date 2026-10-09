# Test Critique — Sprint 3

Round 5, an independent read-only critic run at head `5d62e8e2d5`, after
the round-4 response. Each concern is addressed in the round-5 response
commits. The dispositions are in the [test report](test-report.md), and the
re-review is in [critique](critique.md).

## Concerns

### C-001: Tool-call validity leaves out the sprint's only malformed call, and the validity test cannot detect a missing call
- **Where:**
  - `driver.py` computes `tool_call_validity(cli.conversation_history, known)`, and `run.run_session` publishes it;
  - `qualification/attempt-10-R2.json`;
  - `test_long_sessions_carry_tool_call_validity`;
  - the test report's INT-0004 AC1/AC4 row;
  - build-plan M3 and INT-0004 AC4.
- **Quote:** the test asserts only `isinstance(session.get("tool_calls"), list)`. In attempt 10, request 142 has `"finish_reason": "length"` and `"tool_calls": 1`, so 8 calls were delivered. The session's validity list has 7 entries, all `arguments_valid: true`.
- **Failure mode:** weak-assertion
- **Why it matters:** Validity comes from Hermes's accepted history, which drops a call Hermes rejected. The record can therefore never show the invalid case that M3 and AC4 exist to catch. The test passes on an incomplete list.
- **Suggested response:** tighten-assertion. Record validity per request at the wire, from the calls it delivered, and assert that a session's validity covers every delivered call. Republish attempt 10.

### C-002: The "visible" token count excludes tool-call output, so the reasoning/visible split does not account for the decoded tokens
- **Where:** `wire._handle` counts only `delta.content` as visible; `test_receipt_fields_complete_or_named_missing`; build-plan L1; INT-0007 AC1
- **Quote:** in attempt 08, request 97 records `tool_calls: 1`, `decoded_tokens: 185`, `reasoning_tokens: 0` and `visible_tokens: 0`.
- **Failure mode:** weak-assertion
- **Why it matters:** Every tool-call turn reports 0 reasoning and 0 visible tokens, so the per-turn split misstates where the decoded tokens went. No record defines "visible" as content only. O1 and O2 are unaffected.
- **Suggested response:** tighten-assertion. Count tool-call tokens, or publish them as their own field and define "visible". Test the split on a tool-call response.

### C-003: Four planned checks still have no assertion
- **Where:**
  - **M3 lag:** maximum supervisor lag is published in every outcome, but nothing asserts it.
  - **L2:** AC1 coverage is set inline in `run_session` and never on the being-stopped path. Attempts 07, 11 and 12 have no `ac1_request_coverage`.
  - **M2:** `test_session_config_holds_timers_at_or_above_the_backstop` passes a literal `940.0` and reads it back.
  - **Request limit:** `test_session_request_limit` does not check the `wire_failure` receipt.
- **Quote:** `assert min(timers) >= 940.0`
- **Failure mode:** EARS-coverage
- **Why it matters:** Three EARS sub-clauses and one test-plan assertion pass without their stated outcome being checked.
- **Suggested response:** add-test. Assert lag on every outcome. Record and assert AC1 coverage on every long:all session. Assert that the Hermes timer is at or above the backstop through `session_windows` and against the published manifests. Assert the request-limit receipt.

### C-004: The round-4 records misstate attempt 04, and one round-4 assertion cannot fail
- **Where:** the ledger's round-4 corrections; the test-report C-002 disposition; the unit-tests V2 row; `test_a_stall_stop_is_published_with_its_cause_and_a_cancel_is_not`
- **Quote:** the records say attempt 04's cancelled request now names its first token missing. It actually carries `meaningful_first_token_seconds: 12.344`, and only `tool_calls` was added to its `missing`. The test asserts `"meaningful_first_token_seconds" in stopped or (... in stopped["missing"])`.
- **Failure mode:** evidence-drift
- **Why it matters:** The assertion is always true, and the test stops before any token arrives. The first-token carry is therefore never shown from a live wire.
- **Suggested response:** tighten-assertion. Correct the wording. Stop only after `first_token` is set, and assert that the published value equals it.

### C-005: No sprint or task is named for the live replay of the post-confidence stop-path changes
- **Where:** the test-report "Concerns and limits"; the ledger's round-3 and round-4 corrections
- **Quote:** "Post-confidence lab changes were not replayed live (the launch envelope is spent)."
- **Failure mode:** e2e-cop-out
- **Why it matters:** Rounds 3 and 4 changed live stop behavior. Each change can be observed on the next real attempt, but without a named replay the formal tests remain the only evidence.
- **Suggested response:** defer-with-rationale. Name Sprint 4's first lab attempts as the replay, with the receipt checks that confirm each path.

## Confidence
block
