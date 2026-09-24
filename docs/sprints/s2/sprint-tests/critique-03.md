# Test Critique — Sprint 2

Round 3, an independent read-only re-review at head `51a6b66f38`. The
responses are recorded in [test-report.md](test-report.md) under "Concern
dispositions".

Status of round 2:

- C-016, C-017, C-020, C-022 and C-023 resolved.
- C-019 legitimately deferred to T-211.
- C-018 and C-021 partly resolved; the rest belongs in the test report.

Regression judgment: the narrowing in `b1b813d74c` needs no new broad run.
The admitted set lies between two trees that produced identical failing test
IDs.

## Concerns

### C-024: The unratified time accounting is not carried into the result rows or the completed-task corrections
- **Where:** `e2e-tests.md` R3/R4 rows; ledger confidence section; completed-tasks T-208.
- **Quote:** "pass, under the amended envelope"
- **Failure mode:** evidence-drift
- **Why it matters:** Under the approved rule, the budget was spent before attempt 10 (7,628 s). R3, R4, AC7 and confidence hold only if the owner ratifies. Attempt 13's smoke is outside the budget on every reading.
- **Suggested response:** tighten-assertion. Mark the rows conditional, state what follows a decline, qualify attempt 13, and list AC2's time gate as unproven.

### C-025: No results file states the INT-0004 acceptance-criterion status; AC1 is partial without being marked
- **Failure mode:** intent-coverage
- **Suggested response:** tighten-assertion. Put an AC table in the test report and link T-211 from INT-0004.

### C-026: The test report must carry P2 `book_scope_review`, the tested head and the concern dispositions
- **Failure mode:** EARS-coverage
- **Suggested response:** add-test (report content).

### C-027: The launch-time dirty check is a new, unexercised refusal, described as "behavior-preserving"
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion. Relabel it, and assign the replay to the next lab launch.

### C-028: The explicit-pin served-window check covers only Ollama `num_ctx`
- **Failure mode:** weak-assertion
- **Suggested response:** defer-with-rationale. State the scope; the lab readiness `n_ctx` check guards the served window.

### C-029: The frozen-manifest `source_dirty` branch never decides any test
- **Failure mode:** negative-path
- **Suggested response:** add-test (re-freeze with `source_dirty` and a valid digest).

### C-030: Two claims cite unpublished evidence; one published file is outside the privacy screen
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion. Cite a fingerprint, name `output_limit`, and widen the glob.

## Confidence
proceed-with-caveats
