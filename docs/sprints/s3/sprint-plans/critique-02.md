# Plan Critique — Sprint 3

Round 2, an independent read-only re-review of the first rewrite. The verdict
was `block`. Every concern was addressed in the second rewrite, and
[critique.md](critique.md) holds the re-review. Round 1 is
[critique-01](critique-01.md).

## Concerns

### C-001: Running-minimum rate floors collapse on tiny prefills, pushing windows to hours and widening them during a run
- **Failure mode:** EARS-vague
- **Response:** rates come only from qualifying samples (at least one full batch of prefill, at least 16 decoded tokens); floors are frozen from the calibration record; degradation is recorded but never widens the windows (H1).

### C-002: H2 let the backstop stop a progressing step, contradicting AC7
- **Failure mode:** intent-drift
- **Response:** AC7 now defines enforcement as the stall rule plus a worst-case backstop, and a backstop stop is a recorded failure. H2 and the tests are aligned.

### C-003: The first-use windows and the cleanup bound were undefined or circular
- **Failure mode:** EARS-vague
- **Response:** a calibration record seeds later attempts. The first-use windows are defined (`T_load`, `k × O_cal`). A load is judged by memory-growth progress, the gap window is floored at `T_cli`, and tool CPU counts as progress. Cleanup is INT-0004 AC2's 5 s.

### C-004: Progress events exist only for streaming requests
- **Failure mode:** hidden-dep
- **Response:** the wire forces streaming upstream and reassembles responses for non-streaming clients (T4). The pinned source lines are cited in the research report.

### C-005: The screen could not rank on verified quality
- **Failure mode:** EARS-vague
- **Response:** the opening is 3 turns and includes one scored fix; machine time is defined; a single unit is used throughout; there is a rule for the all-zero case.

### C-006: The screen shared one backend cache and fixture
- **Failure mode:** hidden-dep
- **Response:** each session gets a fresh home and fixture and an erased slot. A planned-attempts table was added.

### C-007: Nothing checked that the long task fits the context
- **Failure mode:** missing-risk
- **Response:** L3 checks the peak prompt plus worst-case echoed reasoning. The input ceiling is an arm field, and overflow is an arm failure.

### C-008: The checkpoint count was recomputed per launch
- **Failure mode:** intent-drift
- **Response:** the count is frozen for the sprint after calibration. There is no silent reduction; a count below 2 is handled explicitly.

### C-009: AC7 was claimed in full while Hermes-side deadlines had no owner
- **Failure mode:** intent-drift
- **Response:** AC7 is covered for the lab route only. T-219 now names the Hermes request, load and stream-stale deadlines, and the manifest records Hermes's effective timeouts.

### C-010: The list of fixed timers was incomplete, and A5 was untested
- **Failure mode:** plan-test-mismatch
- **Response:** the constants are classified as replaced or retained-with-reason, and T3 plus a behavioral test are scoped to that list.

### C-011: The sprint budget could not be computed
- **Failure mode:** EARS-vague
- **Response:** a planned-attempts table was added, with a planning allowance `U` and calibration charged separately.

### C-012: AC1 "turns" vs requests, and fewer than 20 requests failed the arm
- **Failure mode:** intent-drift
- **Response:** AC1 now defines a turn as one model request. Fewer than 20 is AC1 coverage not met, separate from completion, and `max_turns` is a shared constant.

### C-013: The INT-0004 AC1 and AC4 fields sat in Notes
- **Failure mode:** plan-test-mismatch
- **Response:** EARS M3 and M4 were added and bound to tests.

### C-014: The rewritten stop path had no live check before the trials
- **Failure mode:** missing-risk
- **Response:** a live main-cancel was added (C4), and auxiliary cancellation moves to T-219.

### C-015: Contamination was detection-only, and `PYTHONPATH` exposed the repo
- **Failure mode:** missing-risk
- **Response:** the CLI and tool environment has no repo path (M2), paths are resolved before flagging, and a flag means exclude and re-run.

### C-016: T-211 bundled seven outcomes
- **Failure mode:** granularity
- **Response:** T-211 was split into T-211, T-221 and T-222, and repair provenance covers every live task.

### C-017: Smaller gaps
- **Failure mode:** plan-test-mismatch
- **Response:** run names changed to R0–R3 and the formal clauses to V1–V3. Sampler sets are fully specified and sourced (vendor card). The research report was revised, T-212's Touches expanded, and AC3 needs both R1 and R2.

## Confidence
block
