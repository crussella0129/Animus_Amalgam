# Sprint 2 Integration Test Results (after operational confidence)

- **Tested heads:**
  - The affected-suite run and the base comparison used `4bc4f5ea89`, whose
    tracked code equals the Build head; only Book documents were
    uncommitted.
  - The critique-response test changes were run at the Test-phase commit that
    records this file (see the test report).
- **Runner:** `scripts/run_tests.sh` on the owner's Windows 11 host.
- **Ruff:** `ruff format` and `ruff check` reported "All checks passed" for
  `evals/local_qualification/` and every new or changed test file at each
  commit boundary.

| Test (plan name) | EARS | Result | Assertion |
|---|---|---|---|
| Lab-wire integration → `tests/evals/test_local_qualification_wire.py::test_admitted_request_is_bounded_once_and_original_is_preserved` | D1 | pass | The real `Wire` over loopback HTTP against a capture backend forwards exactly one generation request. It applies the 128-token cap and disables thinking, and records the caller's original `max_tokens`. The rendered input count includes the tool-schema text (15 = 10 message + 5 tool words), and one budget unit is consumed. |
| `…::test_oversized_or_misrouted_request_never_reaches_generation` (3 cases) | D2 | pass | Messages over the ceiling, tool schemas alone pushing the input over the ceiling, and a wrong model name each return 422. The backend receives zero generation requests, no budget is consumed, and the wire failure is set, which stops the owner. |
| `…::test_exhausted_request_budget_refuses_before_generation` | S2 | pass | With the aggregate request budget spent, the wire returns 422 before forwarding. No generation is sent and the failure names the exhausted budget. |
| `owned_job_cleanup_windows_live` → `tests/hermes_cli/test_local_runtime_processes.py::test_owner_exit_kills_router_tree_not_external` (existing, `windows_only`) | S1 | pass | A real Windows owner → router → grandchild chain dies when the owner exits or is killed, and an external control process survives. This test's wait allows 10 s, so the 5 s budget is enforced on the live receipts instead (unit-level `test_every_published_attempt_resolves_to_a_valid_frozen_manifest`: every published attempt cleaned up within 5 s and closed its listener). |

The wire test exercises a lab component, not Hermes. The Hermes side of D1/D2
is evidenced live: main requests (attempts 06–13) and the real compression
request (attempt 11) reached the wire with the pinned model name.

Isolation evidence for "no external-provider fallback":

- The child environment is built from an allowlist that passes no provider
  credentials.
- The lab config sets `fallback_models: []`, and the custom provider has no
  hosted route.

A request that bypassed the wire would not appear in wire receipts. What rules
out a successful one is the missing credentials, not the wire.

## Planned test `test_hermes_wire_and_isolation_contract` — disposition

| Planned element | Disposition |
|---|---|
| Actual Hermes main/compression imports | Live only (attempts 06–13 main requests; attempt 11 real `compress_now`). There is no offline real-import capture test. |
| Bounded physical attempts, 128-token cap | Request-level: every forwarded request carried `max_tokens: 128`, proven by the wire test and all live `backend_body` receipts. At the server level, llama-server reported `default_generation_settings.params.n_predict = -1` despite `--predict 128`. The server default is therefore unbounded, and the request cap is the only bound. Backend truncation at 128 was not observed (largest decode 69). D2's output-limit capability clause is **partial**; T-211 carries the decision and the truncation observation. |
| Stable equivalent request bytes | **Fails across sessions** (environment probe, L-19); stable within a session. |
| Temporary homes A→B→A | Not done (rationale above); carried by T-211. |
| Mismatched server/context/rendered-input blocks generation | Unit: `test_ready_server_must_match_the_frozen_candidate` (3 cases). Integration: oversize, tools-overflow, misroute and exhausted-budget wire cases. |

## Affected-suite regression check

- **Head run:** `HERMES_TEST_WORKERS=16 scripts/run_tests.sh tests/agent/ tests/hermes_cli/test_local_*.py`
  plus the Sprint 2 eval tests. Result: 947 files; 9,386 passed, 114 failed,
  81 skipped in 2,253.7 s.
  - Thirteen files hit the per-file timeout under load.
  - One file was flaky, passing on retry:
    `tests/agent/test_tool_activity_heartbeat.py`, which is unrelated to
    Sprint 2.
- **Regression proof:** every failing or timed-out file (65) was rerun on
  the Sprint 2 head and on a detached worktree of the pre-sprint commit
  `cd2185c288`. The runs were concurrent with identical settings (8 workers,
  1,500 s per-file timeout), and each tree was verified to import its own
  `agent/agent_init.py`.
  - Both runs: 2,149 passed, 120 failed and 7 skipped.
  - The sets of failing test IDs are identical, so there are **no
    regressions**.
- `tests/agent/test_prompt_builder.py` was rerun alone on both trees with a
  2,400 s timeout. It fails at collection on both with
  `AttributeError: module 'os' has no attribute 'geteuid'`, a POSIX-only call
  at import. It is a pre-existing Windows platform gap and gives no coverage
  on this host. Sprint 2 did not change prompt building. The cross-session
  prompt finding in the [E2E results](e2e-tests.md#d1-prompt-stability--within-a-session-only)
  comes from live receipts.
- **Hygiene:**
  - The runner's clean environment omits `SYSTEMDRIVE` on Windows, and two
    `test_shell_hooks.py` tests write mangled files into the repo root. Both
    were removed after each run, and an out-of-scope fix task was proposed.
  - The inherited Windows failures (120) predate Sprint 2 and are not
    Amalgam scope.

## Post-replay lab changes (not replayed live)

After attempt 13 exhausted the launch allowance, the critique responses
changed three things:

- extracted the server-identity check into `policy.server_identity_mismatch`
  and read the context from the manifest instead of a literal 8192;
- made the wire's backend timeout injectable, with the same 2 s default;
- tightened tests.

A second critique round then added more changes:

- a launch-time uncommitted-change refusal (`identity_mismatch(..., source_dirty_now)`,
  with `run.py` running `git status --porcelain` at launch);
- in production Hermes, a served window (`num_ctx`) that differs from the pin
  now disqualifies the explicit-pin exception.

The Hermes change is unit-tested and proven red on the prior code. The lab
changes are behavior-preserving and unit-tested, and T-211's first launch
replays them.

## Deferred with rationale (carried by T-211)

- **Profile A→B→A for the lab wire.** One disposable home was reused across
  attempts, and no profile multiplexing occurs on this path. Shared home and
  fixture state is acknowledged: fixtures are only written when absent, and
  the operate fixture now holds 3. A multiplexed-profile regression belongs
  with a change that touches profile scope.
- **Not exercised:**
  - backend output-cap truncation (the largest decode was 69 of 128 tokens);
  - stall- and deadline-triggered cleanup;
  - a stalled collector;
  - stale-telemetry and scheduler-lag stops;
  - launch and time budget predicates;
  - rendered-prefix size in the manifest.
