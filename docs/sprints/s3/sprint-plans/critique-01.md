# Plan Critique — Sprint 3

Round 1, an independent read-only review of the first drafts. The verdict was
`block`. The owner then held the plan for discussion and made the decisions
recorded in the build plan's Approval boundary (host-derived backstops,
sampling screen, throughput criterion, and a core-now / rest-Sprint-4 split).
The plans were rewritten, and [critique.md](critique.md) holds the re-review.

## Concerns

### C-001: Fixed 300 s caps remain in the lab and driver
- **Where:** T-211 Notes; `run.py` (request, readiness, load, outside-request gap from `driver_start`); `wire.py` socket; `driver.py` `run_budget=300` with an 80% wrap-up notice, plus `max_turns`, `max_tokens` and `reasoning`.
- **Failure mode:** hidden-dep
- **Suggested response:** fix-in-plan

### C-002: The compression settings cannot produce the trial, and compression-on arms fail at start-up
- **Where:** T-212 compression. Hermes raises the threshold to 0.75 below 512K, the prune values were unset, and the explicit-pin floor exception requires compression off.
- **Failure mode:** hidden-dep
- **Suggested response:** fix-in-plan

### C-003: Summary requests inherit the main output cap, so O4 could pass on a failed summary; the auxiliary 300 s timeout floor was uncovered
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-004: Output caps are not sized to the task, and truncation retries go uncounted
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-005: The time-accounting terms are unclear, and the backstop can never fire
- **Failure mode:** EARS-vague
- **Suggested response:** fix-in-plan

### C-006: A slow step that is still progressing could be killed, against AC7's rationale; `return_progress` was unconfirmed
- **Failure mode:** intent-drift
- **Suggested response:** fix-in-plan

### C-007: INT-0004's deadline and ratification changes appear only in sprint prose
- **Failure mode:** intent-drift
- **Suggested response:** fix-in-plan

### C-008: The test plan weakened INT-0007 AC1, AC2, AC3 and AC6
- **Failure mode:** intent-drift
- **Suggested response:** fix-in-plan

### C-009: Checkpoint and MTP memory is unpriced, and A5 has no trigger and no test
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-010: The per-launch 24K fallback can leave arms at different contexts
- **Failure mode:** intent-drift
- **Suggested response:** fix-in-plan

### C-011: O3 and the A4 selection cannot be measured as written
- **Failure mode:** EARS-vague
- **Suggested response:** fix-in-plan

### C-012: The temperature-0 thinking-mode degradation risk has no task, test or deferral
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-013: Sprint 2 carry-forwards in backlog T-211 are dropped with no deferral
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-014: The declared Touches and ordering miss paths the work has to change
- **Failure mode:** hidden-dep
- **Suggested response:** fix-in-plan

### C-015: T-211 and T-212 each bundle several separate outcomes
- **Failure mode:** granularity
- **Suggested response:** fix-in-plan

### C-016: The model's terminal could reach the verifier, the defect descriptions or earlier fixtures
- **Failure mode:** missing-risk
- **Suggested response:** fix-in-plan

### C-017: Smaller traceability and evidence gaps
- **Where:** no named bring-up check, echo untested, the probe setting in a WHEN clause, no live-profile baseline, unqueued task links.
- **Failure mode:** plan-test-mismatch
- **Suggested response:** fix-in-plan

## Confidence
block
