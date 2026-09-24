# Sprint 2 Integration Test Results (after operational confidence)

- **Tested head:** `4bc4f5ea89`; tracked code is identical to the Build head,
  and the only uncommitted changes were Book documents.
- **Date:** 2026-09-24
- **Runner:** `HERMES_TEST_WORKERS=16 scripts/run_tests.sh tests/agent/ tests/hermes_cli/test_local_*.py tests/evals/test_local_qualification_policy.py tests/evals/test_local_qualification_wire.py`
  on the owner's Windows 11 host.

| Test (plan name) | EARS | Result | Assertion |
|---|---|---|---|
| `test_hermes_wire_and_isolation_contract` → `tests/evals/test_local_qualification_wire.py::test_admitted_request_is_bounded_once_and_original_is_preserved` | D1 | pass | The real `Wire` guard, over loopback HTTP against a capture backend, forwards exactly one generation request. It applies the 128-token cap and disables thinking, preserves the caller's original `max_tokens` in the receipt and consumes one budget unit. |
| `…::test_oversized_or_misrouted_request_never_reaches_generation` (2 cases) | D2 | pass | Rendered input one token over the ceiling, or a wrong model name, returns 422. The backend receives zero generation requests, no budget is consumed, and the wire failure is set so the owner stops the attempt. |
| `owned_job_cleanup_windows_live` → `tests/hermes_cli/test_local_runtime_processes.py::test_owner_exit_kills_router_tree_not_external` (existing, `windows_only`, parametrized) | S1 | pass | A real Windows owner → router → grandchild chain dies when the owner exits or is killed. An external control process survives. This is reused, not duplicated, as the plan requires. |

## Affected-suite regression check

- **Head run:** 947 files, 9,386 passed, 114 failed and 81 skipped in
  2,253.7 s. Thirteen further files hit the per-file timeout under load, and
  one file was flaky (passed on retry).
- **Regression proof:** all 65 failing or timed-out files were rerun on the
  Sprint 2 head and on a detached worktree of the pre-sprint commit
  `cd2185c288`. The two runs were concurrent, with identical settings (8
  workers, 1,500 s per-file timeout), and each tree imported its own code.
  - Both runs: 2,149 passed, 120 failed and 7 skipped.
  - The failing test IDs are identical: nothing fails only on head and
    nothing fails only on base.
  - `tests/agent/test_prompt_builder.py` timed out before collection on
    both.

  Sprint 2 therefore introduced **no regressions**. The 120 failures predate
  it and are Windows-host failures in inherited upstream tests.
- New Sprint 2 tests in this run: all passed.
  `tests/evals/test_local_qualification_policy.py` (7),
  `tests/evals/test_local_qualification_wire.py` (3) and
  `tests/agent/test_minimum_context_explicit_local.py` (2).
- **Hygiene note:** the runner's clean env omits `SYSTEMDRIVE` on Windows, and
  two `test_shell_hooks.py` tests write mangled files into the repo root.
  Both were removed after each run, and an out-of-scope fix task was
  proposed.

## Deferred with rationale

- **Profile A→B→A for the lab wire.** Each attempt runs one fresh
  disposable `HERMES_HOME`, and no profile multiplexing occurs on this path.
  The live receipts show every main and compression request reaching the
  pinned endpoint and model with no external-provider fallback (attempts
  06–13). A multiplexed-profile regression belongs with a change that
  touches profile scope.
- **Stalled-collector cleanup.** The collector runs as its own owned process.
  Its exit stopped attempt 01 live, but a deterministic stalled-collector
  test was not added. Carried to T-210.
