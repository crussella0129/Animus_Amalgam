# Sprint 3 Unit Test Results (after operational confidence)

- **Tested head:** `0cd28ab8cc` (tests and the race fix they found).
- **Runner:** `scripts/run_tests.sh` (per-file subprocess isolation, clean
  env, `TZ=UTC`) on the owner's Windows 11 host.
- **Ordering:** every test below was written and first run after the
  operational confidence record (2026-10-04T01:58Z, `210d043a2a`).
- **Result:** `tests/hermes_cli/test_local_runtime_throughput.py` and
  `tests/evals/test_local_qualification_lab.py` all pass. The full
  formal-test summary is in the [test report](test-report.md).

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_rates_use_only_qualifying_samples` | H1 | pass | Sub-batch prefill, 1-token prefill and short decode samples leave P and D unchanged. Qualifying samples move them. The floors come from calibration. |
| `test_prediction_is_monotonic_in_work` (3) | H1 | pass | The prediction never decreases as uncached or output tokens grow. |
| `test_stall_and_backstop_semantics` | H2 | pass | Events inside the window keep a step alive until the backstop. A silent step stalls just past its window. |
| `test_window_shapes_follow_the_floors` | H2 | pass | The pre-first-event, prefill and decode windows are k × the floor intervals; the load backstop is m × T_load / f; the calibration window is T_load. |
| `test_no_window_is_shorter_than_the_observation_floor` | H2 | pass | On a near-infinitely fast host, every window equals 4 observation periods. |
| `test_windows_scale_inversely_with_host_rate` (3) | H3 | pass | Scaling the rates by s scales the stall windows, backstop and sprint budget by 1/s (overhead terms zeroed). |
| `test_arm_manifest_drives_server_flags` | M1 | pass | Context, checkpoints, min-step and trace verbosity come from the profile; spec is none; there is no `--predict`. The extracted `launch_flags` reproduces the frozen R2 argv exactly. |
| `test_sessions_get_fresh_state_at_the_same_paths` | M2, C3 | pass | **Regression (C3).** Consecutive sessions get identical paths, a pristine fixture and no carried-over file. The previous session is archived. |
| `test_session_env_is_private_and_repository_free` | M2 | pass | **Regressions.** `TEMP` and `TMP` are private to the session (attempt 06), and no repository path survives from the operator's `PATH` (found in T-214). `SYSTEMDRIVE` passes through, and the task interpreter is first on `PATH`. |
| `test_session_config_holds_timers_at_or_above_the_backstop` | M2 | pass | The environment probe is off, the arm's echo is set, and every Hermes timer is at or above the backstop. |
| `test_kernel_cache_growth_is_seen_and_routed_to_the_backend` | AC7 | pass | **Regression (attempt 02).** Cache growth is detected once, and the backend gets the lab-level `CUDA_CACHE_PATH`. |
| `test_calibration_excludes_requests_that_compiled_kernels` | C2 | pass | **Regression (attempt 02).** A compile-slowed request is not a rate sample. |
| `test_checkpoint_headroom_comes_from_the_admission_receipt` | C2 | pass | **Regression (attempt 04).** The frozen count uses the admission receipt, never the post-load sample. |
| `test_verify_scores_fixture_state` (3) | L2 | pass | The pristine fixture scores 0, the reference through turn 3 scores 1, and the full reference scores 4. |
| `test_contamination_flags_paths_outside_the_fixture` (7) | L4 | pass | `..`, `/c/…`, `$HOME`, `~`, `cd ..`, drive paths and doubled-backslash paths are flagged. |
| `test_contamination_spares_fixture_and_session_paths` (7) | L4 | pass | **Regressions (attempt 06).** `./.git/*`, `*/.git/*`, shell-local `$f`, `/dev/null`, inline division and a private `/tmp` are not flagged. |
| `test_reference_path_is_clean`, `test_tmp_follows_the_session_temp` | L4 | pass | The reference path is clean. `/tmp` is flagged only when it maps to a shared `TEMP`. |
| `test_screen_ranking_rule` | S2 | pass | Verified, then time per item, then decoded tokens. The all-zero case is inconclusive and ranked by machine time. The mid probe is never selected. |
| `test_contaminated_twice_is_a_failure_and_once_is_excluded` | L4, S2 | pass | One flag excludes the session (the re-run counts); two flags make the arm a failure with 0 verified items. |

## Regressions proven red on the pre-repair revision (V2)

Each regression was run against its repair's parent in a separate worktree.
The V2 copies made the `screen` and `verify_long` imports optional, so the
earliest bases could be collected; the committed tests are unchanged.

| Regression | Repair | Base | Red because |
|---|---|---|---|
| cancel returns promptly, recorded as a cancel | `714f5afd4f` | `e4b2b7df1b` | No `response_cancelled`, and the wire could not settle (the attempt-02 freeze). |
| kernel cache, compiled-sample exclusion | `714f5afd4f` | `e4b2b7df1b` | No `KernelCache` (the repair is the class). |
| fixed live session paths | `32a1d3342b` | `f09d3863a0` | The per-index signature: paths differed per session. |
| private `TEMP` | `1850994283` | `c9bcb37a55` | `TEMP` was the owner's (an assertion). |
| contamination spares fixture paths | `1850994283`, `d33c1e4371` | `c9bcb37a55`, `1850994283` | The scan had no session `TEMP` parameter; at `1850994283`, `*/.git/*` was flagged as `/.git` (an assertion). |
| telemetry writer survives a held file | `bead0e57aa` | `d33c1e4371` | No `publish`: the writer raised. |
| sequential retry accepted | `c783199787` | `b20dff7ff5` | The retry got 409 (an assertion). |
| in-flight ownership | `0cd28ab8cc` | `e062f5ee9d` | The third request got 200, not 409 (an assertion). |
| session `PATH` has no repository path | `e062f5ee9d` | `4e6148c5ff` | A repository path was present (an assertion). |
| admission headroom from the receipt | `e062f5ee9d` | `4e6148c5ff` | The old signature took a sample from the caller. |
| LF writers | `daab6f00e0` | `34f782e4cb` | The receipt was written with CRLF (an assertion). |

`launch_flags` and `read_sample` are behavior-preserving T-214 seams. Their
reds at `4e6148c5ff` are missing attributes, not defects.
