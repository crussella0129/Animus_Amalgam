# Sprint 3 Unit Test Results (after operational confidence)

- **Tested head:** `a80294f17a` (after critique round 9).
- **Runner:** `scripts/run_tests.sh` (per-file subprocess isolation, clean
  env, `TZ=UTC`, `HERMES_TEST_FILE_RETRIES=0`) on the owner's Windows 11
  host.
- **Final formal run (V1):** started 2026-10-06T04:45:34Z, covering the six
  Sprint 3 formal files: **318 passed, 0 failed**. Runner log sha256
  `e9081c7877766d4c80ac77e7bc86a27c7ac512782276ab4ecae114791dd01b96`. The
  earlier runs at `32b8e50eaf` (318, log `0cd5001f…`), `47522c6a2d` (318,
  log `2eaec3de…`), `a730a0a39e` (291,
  log `65219407…`), `9c373121cd`, `663bac6a2a`, `4f323770ee`, `1fca1a3095`
  and `efeb4ef4c4` passed 291 (log `5816e66f…`), 238 (log `b6d63e54…`),
  223 (log `bc3e1d5f…`), 217 (log `72fefa45…`) and 171 (log `13bd883f…`). The logs are kept
  with the lab (`<lab>/formal/`) and are not published, because tracebacks
  can contain local paths. The same set passed twice in a row with file
  retries off.
- **Ordering (V1, `formal_order_review`):** the operational confidence record
  was committed at 2026-10-04T01:58:33Z (`210d043a2a`). The first Sprint 3
  formal run came after it, between `cbd8f346fc` (01:58:48Z) and
  `0cd28ab8cc` (02:13:05Z). Every test below was written after the
  confidence record. Earlier runs of `run_tests.sh` were the owner-requested
  repo-root junk fix (`4532740520`, during R2). They covered the runner and
  four inherited tests, not this suite.

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_rates_use_only_qualifying_samples` | H1 | pass | Sub-batch prefill, 1-token prefill and short decode samples leave P and D unchanged. Qualifying samples move them. The floors come from calibration. |
| `test_prediction_is_monotonic_in_work` (3) | H1 | pass | The prediction never decreases as uncached or output tokens grow. |
| `test_stall_and_backstop_semantics` | H2, AC7 | pass | `step_stop` never stops a step that keeps progressing before the backstop. Past the backstop it returns `"backstop"`, a recorded failure. A silent step returns `"stall"` just past its window. Before calibration (no backstop), only the stall rule can stop a step. |
| `test_window_shapes_follow_the_floors` | H2 | pass | The pre-first-event, prefill and decode windows are k × the floor intervals; the load backstop is m × T_load / f; the calibration window is T_load. |
| `test_no_window_is_shorter_than_the_observation_floor` | H2 | pass | On a near-infinitely fast host, every window equals 4 observation periods. |
| `test_windows_scale_inversely_with_host_rate` (3) | H3 | pass | Scaling the rates by s scales the stall windows, backstop and sprint budget by 1/s (overhead terms zeroed). |
| `test_session_windows_scale_with_the_host_rates` | T1, T3 | pass | Every session window comes from `run.session_windows`. Doubling the rates halves the stall windows, request backstop, settle window, Hermes timer and backend probe timeout (`probe_window`). The gap window follows the measured CLI start-up instead. |
| `test_uncalibrated_windows_come_from_the_measured_load` | T1, T3 | pass | **Regression (round 3).** Before calibration, the windows, the backend probe timeout included, are proportional to the attempt's own load time, with no backstop. None falls below 4 observation periods (the retained cadence). During the load itself, the probe timeout is that floor. The gap window is k × the load time, a recorded plan deviation (the plan's per-session T_cli reaches the supervisor only after the session). |
| `test_stop_predicates_fire_at_boundary` | T2 | pass | Stale telemetry (3 periods), supervisor lag (2 periods), the launch cap, the request cap, the sprint budget (none during calibration), load progress and AC1 request coverage (19 against 20) each flip exactly at their boundary. |
| `test_arm_manifest_drives_server_flags` | M1 | pass | Context, checkpoints, min-step and trace verbosity come from the profile; spec is none; there is no `--predict`. |
| `test_launch_flags_reproduce_the_published_full_run_argv` | M1 | pass | `launch_flags` reproduces the published R2 manifest's flags exactly. |
| `test_changing_a_launch_flag_changes_the_manifest_identity` | M1 | pass | Changing one launch flag changes the manifest digest. |
| `test_sessions_get_fresh_state_at_the_same_paths` | M2, C3 | pass | **Regression (C3).** Consecutive sessions get identical paths, a pristine fixture and no carried-over file. The previous session is archived. |
| `test_session_env_is_private_and_repository_free` | M2 | pass | **Regressions.** `TEMP` and `TMP` are private to the session (attempt 06). A repository path on the operator's `PATH` is dropped (T-214). `SYSTEMDRIVE` passes through, and the task interpreter comes first. |
| `test_session_config_holds_timers_at_or_above_the_backstop` | M2 | pass | **Round 5.** The Hermes timer comes from `session_windows` on a calibrated host and is at or above its request backstop; every timer in the session config is too. The environment probe is off and the arm's echo is set. |
| `test_only_the_planned_session_keeps_its_slot` | C3 | pass | **Regression (attempt 04).** `run.erases_slot`, the decision `run_session` makes, erases every session after the first except the calibration and screen plans' second smoke. The full runs erase nothing, because they have one session. |
| `test_every_supervisor_wait_keeps_observing` | T1 | pass | **Regression (attempt 02).** `wait_while` calls `observe()` on every pass while it waits, and returns whether the condition cleared in time. The timeout case uses a 2 s bound. |
| `test_kernel_cache_growth_is_seen_and_routed_to_the_backend` | AC7 | pass | **Regression (attempt 02).** Cache growth is detected once, and the backend gets the lab-level `CUDA_CACHE_PATH`. |
| `test_calibration_excludes_requests_that_compiled_kernels` | C2 | pass | **Regression (attempt 02).** A compile-slowed request is not a rate sample. |
| `test_checkpoint_headroom_comes_from_the_admission_receipt` | C2 | pass | **Regression (attempt 04).** The frozen count uses the admission receipt, never the post-load sample. |
| `test_calibration_fails_closed_on_a_missing_field` | C2 | pass | With no decode sample, checkpoint or admission evidence, calibration raises, records `calibration_failed` naming the missing fields, and writes no record. |
| `test_later_plans_refuse_to_freeze_without_a_calibration_record` | C2 | pass | With no calibration record, R0 cannot be frozen. |
| `test_verify_scores_fixture_state` (3) | L2 | pass | The pristine fixture scores 0, the reference through turn 3 scores 1, and the full reference scores 4. |
| `test_contamination_flags_paths_outside_the_fixture` (7) | L4 | pass | `..`, `/c/…`, `$HOME`, `~`, `cd ..`, drive paths and doubled-backslash paths are flagged. |
| `test_contamination_spares_fixture_and_session_paths` (7) | L4 | pass | **Regressions (attempt 06).** `./.git/*`, `*/.git/*`, shell-local `$f`, `/dev/null`, inline division and a private `/tmp` are not flagged. |
| `test_contamination_spares_the_allowlist` | L4 | pass | The task interpreter and Git Bash binaries are spared. |
| `test_reference_path_is_clean`, `test_tmp_follows_the_session_temp` | L4 | pass | The reference path is clean. `/tmp` is flagged only when it maps to a shared `TEMP`. |
| `test_tool_call_validity_names_bad_arguments_and_unknown_tools` | M3 | pass | Unparseable arguments and unknown tools are named per call (`wire.tool_call_validity`, which the wire records and the driver also uses). |
| `test_screen_ranking_rule` | S2 | pass | Verified, then time per item, then decoded tokens. The all-zero case is inconclusive and ranked by machine time. The mid probe is never selected. |
| `test_contaminated_twice_is_a_failure_and_once_is_excluded` | L4, S2 | pass | One flag excludes the session (the re-run counts); two flags make the arm a failure with 0 verified items. |
| `test_stopped_request_keeps_its_cause_timing_and_predictions` | AC7, M3 | pass | **Regressions (rounds 4 and 6).** The `request_stopped` receipt carries the stop cause, elapsed time, meaningful first token, both predictions and the last `/slots` decode count as an observed lower bound. |
| `test_request_extrema_are_recorded_when_a_guard_stops_the_loop` | L1 | pass | **Regression (round 2).** When a guard raises inside the loop, the in-flight request's resource extrema are still recorded, with the running minimum and maximum. |
| `test_a_cut_short_session_is_scored_from_its_fixture` | L2 | pass | A session an attempt stop cut short is scored from its fixture: 1 verified after turn 3, with its request count, an empty L4 screen and, being under 20 requests, AC1 coverage not met (L2, round 5). |
| `test_a_cut_short_session_is_screened_from_its_last_conversation` | L4, L2 | pass | **Regression (round 3).** The stop path screens the conversation the wire last forwarded; a tool call reading `../../secret` is flagged. The screen publishes what it saw (1 message, 1 tool call), and the session records the call's validity. |
| `test_scoring_a_cut_short_session_never_raises_into_the_stop_path` | L2, AC7 | pass | **Regression (round 3).** When scoring raises, `stopped_session` returns the session with the error as its verification. `run.bounded` returns `None` past its bound and the result within it. |
| `test_a_stopped_request_stays_stopped_whatever_lands_after` (2) | AC7, M3 | pass | **Regression (round 2).** After `request_stopped`, a later `wire_failure` or `response_cancelled` keeps the stopped outcome, its cause, its own timing, both predictions and the resources. Machine time is computed. |
| `test_a_stopped_request_publishes_its_time_after_prefill` | O1, AC7 | pass | **Regression (round 7).** A stopped request whose decode went unreturned names `decoded_tokens` missing and publishes its seconds after the prompt was fully processed, from its own progress receipt, so the missing decode can be estimated. |
| `test_publish_scores_and_screens_a_cut_short_session` (2) | L2, L4 | pass | **Regression (round 3).** Publishing scores a cut-short session from its preserved fixture and screens its last request's conversation: clean when it runs the check, flagged when it reads outside the fixture. The screen's message and tool-call counts, and each call's validity, are published, with AC1 coverage for a long:all session (round 5). |
| `test_an_aborted_request_takes_its_own_sessions_stop_as_its_cause` | AC7, M3 | pass | **Regression (round 3, attempt 02).** An aborted request takes its own session's recorded stop as its cause. A failure in a session that ended without a stop stays a wire failure, and only a request in flight at the attempt stop takes the attempt's reason, timed from its receipts. |

## Regressions proven red on the pre-repair revision (V2)

Each regression ran against its repair's parent in a separate worktree. The
V2 copies made the `screen` and `verify_long` imports optional, so the
earliest bases could be collected; the committed tests are unchanged.

| Regression | Repair | Base | Red because |
|---|---|---|---|
| cancel returns promptly, recorded as a cancel | `714f5afd4f` | `e4b2b7df1b` | **Behavior:** no `response_cancelled`, and the wire could not settle (the attempt-02 freeze). |
| cancelled and stopped requests keep their timing | `efeb4ef4c4` | `0cd28ab8cc` | **Behavior:** the cancel record had no predictions. |
| slot identified from `/slots` | `efeb4ef4c4` | `0cd28ab8cc` | **Behavior:** no prediction at send, and no `id_slot` without a streamed one. |
| per-session erase | `32a1d3342b` | `f09d3863a0` | **API:** the committed test calls `run.erases_slot`, which the base lacks. The defect, every session erased because the manifest had no per-session erase field, is evidenced live by attempt 04. |
| observing waits | `714f5afd4f` | `e4b2b7df1b` | **API:** there was no module-level `wait_while`; the old inline waits skipped `observe()`. The defect is evidenced live by attempt 02's lag stop. |
| stopped outcome survives a later record | `1fca1a3095` | `efeb4ef4c4` | **Behavior:** a later `response_cancelled` relabelled the stopped request (and there was no `machine_time`). |
| failing request keeps its timing | `efeb4ef4c4` | `0cd28ab8cc` | **Behavior:** the `wire_failure` record had no `seconds`. |
| stopped-request, stopped-session and extrema seams | `1fca1a3095` | `efeb4ef4c4` | **API:** no `stopped_session`, `RequestExtrema` or `erases_slot`. |
| private `TEMP` | `1850994283` | `c9bcb37a55` | **Behavior:** `TEMP` was the owner's. |
| glob contamination case | `d33c1e4371` | `1850994283` | **Behavior:** `*/.git/*` was flagged as `/.git`. |
| sequential retry accepted | `c783199787` | `b20dff7ff5` | **Behavior:** the retry got 409. |
| in-flight ownership | `0cd28ab8cc` | `e062f5ee9d` | **Behavior:** the third request got 200, not 409. |
| session `PATH` has no repository path | `e062f5ee9d` | `4e6148c5ff` | **Behavior:** a repository path was present. |
| LF writers | `daab6f00e0` | `34f782e4cb` | **Behavior:** the receipt was written with CRLF. |
| kernel cache, compiled-sample exclusion | `714f5afd4f` | `e4b2b7df1b` | **API:** no `KernelCache`; the repair introduced it. |
| fixed live session paths | `32a1d3342b` | `f09d3863a0` | **API:** the per-index signature produced a new path per session. |
| telemetry writer survives a held file | `bead0e57aa` | `d33c1e4371` | **API:** no `publish`; the old writer raised. |
| admission headroom from the receipt | `e062f5ee9d` | `4e6148c5ff` | **API:** the old signature took the sample from the caller (the attempt-04 class). |
| aborted request takes its own session's stop | `4f323770ee` | `4a039353ac` | **Behavior:** the stall-stopped request took the attempt's later lag cause. |
| published cause matches the session's stop | `4f323770ee` | `4a039353ac` | **Behavior:** attempt 02's request 1 was published with the lag cause, not its stall. |
| cut-short session screened from its last conversation | `4f323770ee` | `4a039353ac` | **Behavior:** the screen saw no conversation, so `../../secret` was not flagged. |
| stop-path scoring never raises | `4f323770ee` | `4a039353ac` | **Behavior:** the scoring error propagated out of `stopped_session`. |
| probe timeout floored before calibration | `4f323770ee` | `4a039353ac` | **Behavior:** the probe timeout was 0 s at a zero load time, below the observation floor. |
| publish screens a cut-short session | `4f323770ee` | `4a039353ac` | **API:** the at-publish verification had no `contamination`. |
| published stopped sessions screened | `4f323770ee` | `4a039353ac` | **API:** the published receipts of attempts 05, 07, 11 and 12 had no `contamination`. |
| live in-flight stop receipt | `4f323770ee` | `4a039353ac` | **API:** the wire session had no `last_messages`; the stop receipt itself read the live `Wire.active` correctly at base. |
| delivered tool calls in the screened conversation | `4f323770ee` | `4a039353ac` | **API:** the wire session had no `last_messages`. |
| stopped request keeps its first token | `663bac6a2a` | `3396f33a8e` | **Behavior:** the `request_stopped` receipt had no meaningful first token. |
| stop during verification screens the ended session | `663bac6a2a` | `3396f33a8e` | **Behavior:** the ended session was gone, so the screen saw nothing and `requests` was `None`. |
| published requests name missing first token and tool-call count | `663bac6a2a` | `3396f33a8e` | **Behavior:** the stopped requests of attempts 02, 05, 07, 11 and 12 left both silently absent, and attempt 04's cancelled request the tool-call count (it carries its first token, 12.344 s; corrected in round 5). |
| cut-short sessions carry tool-call validity | `663bac6a2a` | `3396f33a8e` | **Behavior:** attempts 05, 07, 11 and 12 published none. |
| stall stop published with its cause | `663bac6a2a` | `3396f33a8e` | **API:** no `run.stop_active_request`. At base, `run_session` cancelled through the wire with no stop receipt. |
| stop-path screen publishes what it saw | `663bac6a2a` | `3396f33a8e` | **API:** no `screened` in the verification. |
| publish screen publishes what it saw | `663bac6a2a` | `3396f33a8e` | **API:** no `screened` in the at-publish verification. |
| published cut-short screens are non-empty | `663bac6a2a` | `3396f33a8e` | **API:** the receipts of attempts 05, 07, 11 and 12 had no `screened`. |
| every delivered tool call validated or named | `9c373121cd` | `5d62e8e2d5` | **Behavior:** attempt 10's session validated 7 of its 8 delivered calls and named nothing. |
| stop-path validity from the delivered calls | `9c373121cd` | `5d62e8e2d5` | **Behavior:** the stop path derived validity from the forwarded history, not from what the wire delivered. |
| a call cut at the output cap is recorded invalid | `9c373121cd` | `5d62e8e2d5` | **API:** `response_end` had no `tool_call_validity`. |
| tool-call output counted in the token split | `9c373121cd` | `5d62e8e2d5` | **API:** no `tool_call_tokens` at the wire, and no published `unsplit_decoded_tokens`. |
| AC1 coverage on the being-stopped path | `9c373121cd` | `5d62e8e2d5` | **API:** no `policy.ac1_request_coverage`. The cut-short long:all sessions of attempts 07, 11 and 12 had no `ac1_request_coverage`. |
| stop receipt carries a decode lower bound | `a730a0a39e` | `cf895ec191` | **Behavior:** `stopped_request` dropped the `/slots` decode count it had seen. |
| live stall stop names its decode missing | `a730a0a39e` | `cf895ec191` | **Behavior:** the published stopped request neither named `decoded_tokens` missing nor kept the observed count. |
| published requests name decoded tokens missing | `a730a0a39e` | `cf895ec191` | **Behavior:** the 6 requests that never completed (attempts 02, 04, 05, 07, 11 and 12) left `decoded_tokens` silently absent. |
| stopped request publishes its time after prefill | `47522c6a2d` | `f56cf5f195` | **API:** no `seconds_after_prefill`. |
| screen receipt reproduces the recorded winners | `47522c6a2d` | `f56cf5f195` | **API:** attempt 06's receipt had no `screen` report, only the pre-repair live verdicts. |
| concurrency refusal is receipted | `a80294f17a` | `7322017d5b` | **Behavior:** the refused request left no `wire_failure` record. |

V2 covers 46 regressions: 26 red on the behavior assertion and 20 on an
API the repair introduced. For the API reds of rounds 1 and 2, the defect
itself is evidenced live by the attempt that found it (02, 04, 07, 11 and
12); the test pins the repaired contract. The 13 API reds of rounds 3 to 7
are the new fields and seams that those rounds' behavior reds depend on. Round
5's assertions on supervisor lag, the Hermes timers against the backstop,
the request-limit receipt and the live first token pass on base: they cover
behavior that was already correct. So do round 6's markup-bearing split
test and the schema-scoped receipt checks, which hold receipts from the
repaired lab to stricter rules.

In the round-3 to round-9 worktrees, the base copy of
`test_session_env_is_private_and_repository_free` also failed. The worktree
sat inside the owner's `TEMP`, which breaks the test's premise that the
repository is outside it. The failure is an artifact of where the worktree
was, not a regression, and the test passes in the checkout. `launch_flags`, `read_sample`, `session_windows`, `probe_window`
and `step_stop` are behavior-preserving T-214 seams; their reds on older
bases are missing attributes, not defects.
