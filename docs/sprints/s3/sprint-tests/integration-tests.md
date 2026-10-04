# Sprint 3 Integration Test Results (after operational confidence)

- **Tested head:** `efeb4ef4c4` (after critique round 1). These results are
  part of the final formal run recorded in [unit-tests](unit-tests.md) (171
  passed, 0 failed; runner log sha256 `13bd883f…`).
- **Runner:** `scripts/run_tests.sh` on the owner's Windows 11 host.
- **Ordering:** written and first run after the confidence record
  (2026-10-04T01:58Z).

## Lab wire

The real `Wire` runs over loopback HTTP against a capture backend shaped
like the pinned b10964. It renders, tokenizes and streams a progress chunk,
reasoning and content or tool-call deltas, and a final timings chunk with
**no `id_slot`**. Its `/slots` names the working slot, as the real server
does. The Sprint 2 wire tests were ported to the Sprint 3 Wire API (T-211
changed its constructor), keeping their invariants. Waits are event-based
(the backend signals its first chunk), and wall-clock bounds are at least
2 s.

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_admitted_request_is_bounded_once_and_original_is_preserved` | M1 | pass | A thinking arm forwards its cap, `enable_thinking`, `reasoning_budget_tokens`, the full greedy sampler set and seed, with `stream` and `return_progress` on and `reasoning_effort` dropped. It does so exactly once, and the original body is kept. |
| `test_oversized_or_misrouted_request_never_reaches_generation` (3) | M1 | pass | Over the ceiling (through messages or tools), or a wrong model, the request is refused before generation. No request is consumed. |
| `test_exhausted_request_budget_refuses_before_generation` | T2 | pass | The aggregate budget refuses before generation. |
| `test_session_request_limit` | per-session limit | pass | A request past the session limit is refused, with a recorded failure. |
| `test_wire_streams_and_reassembles` | T4 | pass | Progress chunks never reach the client. A non-streaming client gets one reassembled response with reasoning, content and finish reason. Both went upstream streaming. |
| `test_streamed_tool_call_is_reassembled_and_counted` | M3, T4 | pass | A streamed tool call is reassembled with its name and parsed arguments, and counted in the receipt. |
| `test_length_finish_marks_the_next_request_a_continuation` | M3 | pass | After a `length` finish, the next request is recorded as a truncation continuation. |
| `test_slot_counters_are_progress_while_deltas_are_withheld` | T4 | pass | While SSE deltas are withheld for seconds, rising `/slots` counters register as progress. |
| `test_receipt_fields_complete_or_named_missing` | M3, L1 | pass | The prediction is recorded at send. The response receipt carries timings, finish reason, the reasoning/visible split, first token and both predictions. The slot comes from `/slots` (`id_slot_source: "slots"`), because the stream carries none. `kernel_compiled` is present even when no cache is wired. |
| `test_cancel_returns_promptly_and_is_recorded_as_a_cancel` | C4, INT-0004 AC2 | pass | **Regression (attempt 02).** The cancel returns in under 2 s against a 6 s batch. It is recorded as `response_cancelled`, not as a wire failure, and keeps its elapsed time and prediction (AC7). |
| `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused` | M1 | pass | **Regressions (attempt 10 and T-214).** A retry sent at `[DONE]` during the previous request's accounting is accepted. A request arriving mid-stream is refused as concurrent, including after a finishing handler's cleanup. |

**Found by these tests:** a race in the attempt-10 repair. A finishing
handler's `finally` cleared the in-flight flag the next request had
already claimed. The flag now holds the owning handler's token, and only
that owner releases it (`0cd28ab8cc`).

## Published receipts and manifests

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_every_attempt_is_published` | V3 | pass | Attempt indices 1–13, taken from the final budget counter, each have a published receipt. |
| `test_published_evidence_excludes_private_paths_and_credentials` (25) | V3 | pass | No user path, `Bearer` value or 48-hex token appears in any published receipt or manifest. |
| `test_every_published_attempt_resolves_to_its_manifest` (13) | V3, M4 | pass | Each receipt resolves to its manifest by id. The public copy's digest is valid. The owner's time-model decision, Hermes timeouts (including the terminal timeout), the allowlist and the time parameters are present. The rendered prefix is measured, or not-measured with a reason. Post-calibration plans carry the full calibration record (rates, checkpoint size, frozen count, budget). Every session has an arm, a stop cause is kept, and cleanup took at most 5 s with the listener closed. |
| `test_launched_attempts_record_the_launch_and_admission` (13) | M1, M4 | pass | Every launched attempt's command has `--slot-save-path` and no `--predict`, and records its admission host condition. |
| `test_sessions_record_their_first_rendered_prefix` (13) | M4 | pass | Each session records its first rendered prefix (tokens and hash). |
| `test_every_request_names_its_missing_fields` (13) | L1, M3 | pass | Every request, completed or stopped, carries each of the 14 L1/M3 fields or names it missing. |
| `test_stopped_requests_keep_their_cause_and_elapsed_time` (13) | AC7 | pass | Each attempt-stopped request keeps its stop cause and elapsed time. |

## Windows file behaviour (`windows_only`)

| Test | Result | Assertion |
|---|---|---|
| `test_refused_telemetry_read_keeps_the_last_sample` | pass | **Regression (attempt 05).** While another handle denies sharing, the read keeps the last sample. |
| `test_telemetry_publish_survives_a_held_destination` | pass | **Regression (attempt 07).** With an injected bound, the writer retries until the reader closes. If the reader holds on, the sample is skipped without raising. |
| `test_lab_writers_emit_lf` | pass | Receipts and manifests are written with LF, so the published bytes and digests are host-independent. |

## Affected-suite regression check

The same file set ran with the same settings on base `5f6a0c7b60` (the
Sprint 2 checkpoint merge) and on head: `tests/hermes_cli/test_local_*.py`,
`tests/evals/`, and the four junk-fix files.

| Tree | Files | Passed | Failed | Skipped | Runner log sha256 |
|---|---|---|---|---|---|
| Base `5f6a0c7b60` | 30 | 345 | 7 | 2 | — |
| Head `efeb4ef4c4` | 34 | 502 | 1 | 2 | `13d709c5…` |

- **New failures on head:** none.
- **Fixed on head (6):** the shell-hook, hooks-CLI, cron catch-up and
  gitspawn baseline tests (fix `4532740520`). The Windows paths they put in
  bash bodies were mangled.
- **Inherited (1):** `test_local_runtime_child_env.py::test_spawn_server_keeps_the_callers_environment`
  fails identically on base. Neither it nor `processes.py` changed.
