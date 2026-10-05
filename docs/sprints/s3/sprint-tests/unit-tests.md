# Sprint 3 Unit Test Results (after operational confidence)

- **Tested head:** `1fca1a3095` (after critique round 2).
- **Runner:** `scripts/run_tests.sh` (per-file subprocess isolation, clean
  env, `TZ=UTC`, `HERMES_TEST_FILE_RETRIES=0`) on the owner's Windows 11
  host.
- **Final formal run (V1):** started 2026-10-05T20:35:10Z, covering the six
  Sprint 3 formal files: **217 passed, 0 failed**. Runner log sha256
  `72fefa4574746c93c5cb57ed10779342fd33e32854ee726cc9d55d9eb4061a34`. The
  earlier run at `efeb4ef4c4` passed 171 (log `13bd883f…`). The logs are kept
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
| `test_uncalibrated_windows_come_from_the_measured_load` | T1, T3 | pass | Before calibration, the windows are proportional to the attempt's own load time, with no backstop. They never fall below 4 observation periods (the retained cadence). |
| `test_stop_predicates_fire_at_boundary` | T2 | pass | Stale telemetry (3 periods), supervisor lag (2 periods), the launch cap, the request cap, the sprint budget (none during calibration) and load progress each flip exactly at their boundary. |
| `test_arm_manifest_drives_server_flags` | M1 | pass | Context, checkpoints, min-step and trace verbosity come from the profile; spec is none; there is no `--predict`. |
| `test_launch_flags_reproduce_the_published_full_run_argv` | M1 | pass | `launch_flags` reproduces the published R2 manifest's flags exactly. |
| `test_changing_a_launch_flag_changes_the_manifest_identity` | M1 | pass | Changing one launch flag changes the manifest digest. |
| `test_sessions_get_fresh_state_at_the_same_paths` | M2, C3 | pass | **Regression (C3).** Consecutive sessions get identical paths, a pristine fixture and no carried-over file. The previous session is archived. |
| `test_session_env_is_private_and_repository_free` | M2 | pass | **Regressions.** `TEMP` and `TMP` are private to the session (attempt 06). A repository path on the operator's `PATH` is dropped (T-214). `SYSTEMDRIVE` passes through, and the task interpreter comes first. |
| `test_session_config_holds_timers_at_or_above_the_backstop` | M2 | pass | The environment probe is off, the arm's echo is set, and every Hermes timer is at or above the backstop. |
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
| `test_tool_call_validity_names_bad_arguments_and_unknown_tools` | M3 | pass | Unparseable arguments and unknown tools are named per call. |
| `test_screen_ranking_rule` | S2 | pass | Verified, then time per item, then decoded tokens. The all-zero case is inconclusive and ranked by machine time. The mid probe is never selected. |
| `test_contaminated_twice_is_a_failure_and_once_is_excluded` | L4, S2 | pass | One flag excludes the session (the re-run counts); two flags make the arm a failure with 0 verified items. |
| `test_stopped_request_keeps_its_cause_timing_and_predictions` | AC7, M3 | pass | The `request_stopped` receipt carries the stop cause, elapsed time and both predictions. |
| `test_request_extrema_are_recorded_when_a_guard_stops_the_loop` | L1 | pass | **Regression (round 2).** When a guard raises inside the loop, the in-flight request's resource extrema are still recorded, with the running minimum and maximum. |
| `test_a_cut_short_session_is_scored_from_its_fixture` | L2 | pass | A session an attempt stop cut short is scored from its fixture: 1 verified after turn 3, with its request count. |
| `test_a_stopped_request_stays_stopped_whatever_lands_after` (2) | AC7, M3 | pass | **Regression (round 2).** After `request_stopped`, a later `wire_failure` or `response_cancelled` keeps the stopped outcome, its cause, its own timing, both predictions and the resources. Machine time is computed. |
| `test_publish_scores_a_cut_short_session_from_its_fixture` | L2 | pass | Publishing scores a cut-short session from its preserved fixture. |

## Regressions proven red on the pre-repair revision (V2)

Each regression ran against its repair's parent in a separate worktree. The
V2 copies made the `screen` and `verify_long` imports optional, so the
earliest bases could be collected; the committed tests are unchanged.

| Regression | Repair | Base | Red because |
|---|---|---|---|
| cancel returns promptly, recorded as a cancel | `714f5afd4f` | `e4b2b7df1b` | **Behavior:** no `response_cancelled`, and the wire could not settle (the attempt-02 freeze). |
| cancelled and stopped requests keep their timing | `efeb4ef4c4` | `0cd28ab8cc` | **Behavior:** the cancel record had no predictions. |
| slot identified from `/slots` | `efeb4ef4c4` | `0cd28ab8cc` | **Behavior:** no prediction at send, and no `id_slot` without a streamed one. |
| per-session erase | `32a1d3342b` | `f09d3863a0` | **Schema:** the manifest had no per-session erase field (`KeyError: 'erase_slot'`), so every session was erased. Now asserted through `run.erases_slot`, the decision `run_session` makes. |
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

For the API and schema reds, the defect itself is evidenced live by the
attempt that found it (02, 04, 07, 11 and 12). The test pins the repaired
contract. `launch_flags`, `read_sample`, `session_windows`, `probe_window`
and `step_stop` are behavior-preserving T-214 seams; their reds on older
bases are missing attributes, not defects.
