# Test Critique — Sprint 2

Round 1, an independent read-only critic run at head `eb6f3fb8cf`. Every
concern was addressed in `73a76ff4a0` / `5be1ed4331`; see
[critique-02](critique-02.md) for the re-review.

## Concerns

### C-001: D1 claims stable prompt bytes, but the receipts show two different smoke prompts
- **Where:** `integration-tests.md` D1 row; build-plan T-207 D1; `qualification/attempts.json` requests 6 and 17.
- **Quote:** "stable serialized prompt/tool bytes"
- **Failure mode:** EARS-coverage
- **Why it matters:** The same no-tool smoke rendered 1169 tokens (attempts 07 and 10) and 1127 tokens (08, 09 and 13) under the same effective configuration. No formal test checks cross-session byte stability.
- **Suggested response:** add-test, or restate D1 as within-session stable and make cross-session variance an entry condition for T-202.

### C-002: Owner-approved limit relaxations are listed as "repairs"; the time-budget change was never ratified
- **Where:** `e2e-tests.md` `operational_repair_replay`; ledger "Owner continuation 2".
- **Quote:** "paging policy (05/09→10) … input ceiling (09→10)"
- **Failure mode:** evidence-drift
- **Why it matters:** The task reached 4543 tokens, which the locked 4096 ceiling would have refused. The attempt-scoped time accounting lacks owner ratification.
- **Suggested response:** tighten-assertion. Separate amendments from repairs and record ratification status.

### C-003: The "integration" wire test never touches Hermes, and the fresh-home rationale is false
- **Where:** `integration-tests.md` D1/D2 rows and A→B→A deferral.
- **Quote:** "Each attempt runs one fresh disposable `HERMES_HOME`"
- **Failure mode:** integration-drift
- **Why it matters:** One lab home persisted across all 13 attempts. Fixtures are only written when absent. Wire receipts cannot see a request that bypasses the wire.
- **Suggested response:** add-test, or defer-with-rationale with corrected facts.

### C-004: D2's server-identity and output-limit rejections are untested and unexercised
- **Where:** build-plan T-207 D2; `run.py::readiness`.
- **Quote:** "server identity, context/slot configuration or output-limit capability differs from the manifest"
- **Failure mode:** negative-path
- **Why it matters:** The mismatch branch never fired and has no test. No output-limit capability check exists. No request reached 128 decoded tokens.
- **Suggested response:** add-test (extract the props predicate), or restate D2 as a request-level cap only.

### C-005: S2's budget, reserve, stale-probe and lag stops lack negative tests; the deferral target doesn't carry them
- **Where:** build-plan T-206 S2; `unit-tests.md` "Not unit-tested"; T-210.
- **Quote:** "or an extra request/launch would exceed policy"
- **Failure mode:** negative-path
- **Why it matters:** `reserve_breached` and request-budget exhaustion are untested. Stale telemetry and lag were deferred to a task that does not name them.
- **Suggested response:** add-test; give the deferral a real home.

### C-006: S1 evidence doesn't assert the 5-second budget; some triggers were never exercised
- **Where:** `test_owner_exit_kills_router_tree_not_external`; `sentinel-survival.json`.
- **Quote:** "`_wait(...)`, which defaults to `timeout=10`"; "alive_after_attempts": [8, 9]
- **Failure mode:** weak-assertion
- **Why it matters:** The reused test tolerates 10 s. The stall and deadline triggers were never exercised. No sentinel was running during attempts 10–11.
- **Suggested response:** tighten-assertion; defer the untested triggers to a task that names them.

### C-007: The "checked independently by the driver" claim is inaccurate for attempts 07–09
- **Where:** `e2e-tests.md` `live_smoke`.
- **Failure mode:** evidence-drift
- **Why it matters:** The driver check was added in `a85c947692`, after attempts 07–09. The receipts had no verification field.
- **Suggested response:** tighten-assertion.

### C-008: The M1 test is circular; the receipt audit and scope review were never recorded as executed
- **Where:** `unit-tests.md` M1 row.
- **Failure mode:** weak-assertion
- **Why it matters:** The test fed the manifest's own values back in. Server configuration and the rendered prefix are absent from the manifests.
- **Suggested response:** add-test (an audit over attempts.json).

### C-009: AC4 receipt metrics are missing without being marked missing
- **Where:** INT-0004 AC4; attempts.json.
- **Failure mode:** intent-coverage
- **Suggested response:** tighten-assertion (mark missing fields, or state that AC4 is only partly met).

### C-010: The "confidence before suites" record was written after the tests were committed
- **Where:** ledger header; `e2e-tests.md` "Order".
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion (record the anchored timeline; correct the `c42152ca0b` sentence).

### C-011: The context-floor repair is tested only on the compression condition
- **Where:** `tests/agent/test_minimum_context_explicit_local.py`.
- **Failure mode:** negative-path
- **Suggested response:** add-test (non-local and mismatched-window refusals; assert 8192).

### C-012: Committed Book links point to untracked files (INT-0007, direction review)
- **Failure mode:** evidence-drift
- **Suggested response:** commit them or remove the links.

### C-013: The capture backend ignores tool schemas when rendering the prompt
- **Where:** `test_local_qualification_wire.py::CaptureBackend`.
- **Failure mode:** stub-leak
- **Suggested response:** tighten-assertion (render tools; add a tools-overflow case).

### C-014: Timing and shared-fixture flake risk
- **Where:** `wire.py` 2 s backend timeout; unnamed flaky file; `frozen[0]` fixture.
- **Failure mode:** flake-risk
- **Suggested response:** tighten-assertion.

### C-015: Gaps in the regression proof and hygiene records
- **Where:** `test_prompt_builder.py` never ran on either tree; Ruff results unrecorded.
- **Failure mode:** evidence-drift
- **Suggested response:** add-test (run it alone on both trees) and record Ruff results.

## Confidence
block
