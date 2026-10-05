# Sprint 3 Integration Test Results (after operational confidence)

- **Tested head:** `4f323770ee` (after critique round 3). These results are
  part of the final formal run recorded in [unit-tests](unit-tests.md) (223
  passed, 0 failed; runner log sha256 `bc3e1d5f…`).
- **Runner:** `scripts/run_tests.sh` on the owner's Windows 11 host.
- **Ordering:** written and first run after the confidence record
  (2026-10-04T01:58Z).

## Lab wire

The real `Wire` runs over loopback HTTP against a capture backend shaped
like the pinned b10964. It renders, tokenizes and streams a progress chunk,
reasoning and content or tool-call deltas, and a final timings chunk with
**no `id_slot`**. Its `/slots` names the working slot, as the real server
does: a slot is processing only during a request. The Sprint 2 wire tests
were ported to the Sprint 3 Wire API (T-211 changed its constructor),
keeping their invariants. Waits are event-based: the backend signals its
first chunk, and holds its final chunk until the test has seen the wire
record the working slot (`slot_seen`). Wall-clock bounds are at least 2 s.

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
| `test_receipt_fields_complete_or_named_missing` | M3, L1 | pass | The final chunk is released only after the wire has recorded `slot_seen`. The prediction is recorded at send. The response receipt carries timings, finish reason, the reasoning/visible split, first token and both predictions. The slot comes from `/slots` (`id_slot_source: "slots"`), because the stream carries none. `kernel_compiled` is present even when no cache is wired. |
| `test_cancel_returns_promptly_and_is_recorded_as_a_cancel` | C4, INT-0004 AC2 | pass | **Regression (attempt 02).** The cancel returns in under 2 s against a 6 s batch. It is recorded as `response_cancelled`, not as a wire failure, and keeps its elapsed time and prediction (AC7). |
| `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused` | M1 | pass | **Regressions (attempt 10 and T-214).** A retry sent at `[DONE]` during the previous request's accounting is accepted. A request arriving mid-stream is refused as concurrent, including after a finishing handler's cleanup. |
| `test_a_failing_request_keeps_its_timing_and_predictions` | AC7, M3 | pass | **Regression (round 1).** A malformed stream fails the request, and its `wire_failure` keeps the elapsed time and both predictions. |
| `test_an_attempt_stop_receipts_the_live_in_flight_request` | AC7, L4 | pass | **Regression (round 3).** `run.stopped_request` on the live `Wire.active` mid-stream gives the request id, the cause, an elapsed time within the observed window and both predictions. The wire session keeps the conversation it forwarded. |
| `test_the_screened_conversation_includes_tool_calls_already_delivered` | L4 | pass | **Regression (round 3).** After a delivered tool-call response, the screened conversation is the forwarded history plus that response's tool calls, which Hermes may run before another request. |

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
| `test_stopped_requests_keep_their_own_cause_and_elapsed_time` (13) | AC7 | pass | **Regression (round 3).** Each stopped request's cause equals its own session's recorded stop, or the attempt's reason when its session was still running, and it keeps its elapsed time. |
| `test_completed_calibrated_requests_carry_every_l1_field` (13) | AC7, L1 | pass | Every request completed after calibration carries every L1 field, present and not merely named. The one exception is `id_slot`, which b10964's stream does not return; those receipts predate the `/slots` correlation, so it must be named missing. |
| `test_machine_time_is_recomputable_from_the_receipt` (13) | O1 | pass | Each session's published machine time equals the span of its requests' published start and end times. |
| `test_attempt_stopped_long_sessions_are_scored` (13) | L2, L4 | pass | A long session cut short by an attempt stop has a score and an empty L4 screen: attempts 05, 07, 11 and 12. A session screened at publish ends in a stopped request, so its last forwarded conversation holds every tool call Hermes ran. |

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
| Head `1fca1a3095` | 34 | 548 | 1 | 2 | `f8b8b33e…` |
| Head `4f323770ee` | 34 | 554 | 1 | 2 | `c883ad77…` |

- **New failures on head:** none.
- **Fixed on head (6):** the shell-hook, hooks-CLI, cron catch-up and
  gitspawn baseline tests (fix `4532740520`). The Windows paths they put in
  bash bodies were mangled.
- **Inherited (1):** `test_local_runtime_child_env.py::test_spawn_server_keeps_the_callers_environment`
  fails identically on base. Neither it nor `processes.py` changed.
