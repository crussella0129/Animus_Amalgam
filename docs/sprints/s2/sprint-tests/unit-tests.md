# Sprint 2 Unit Test Results (after operational confidence)

- **Tested heads:** first `4bc4f5ea89`, then the Test-phase critique-response
  commit named in the test report, which is the final head for these files.
- **Date:** 2026-09-24
- **Runner:** `scripts/run_tests.sh` (per-file subprocess isolation, clean
  env, `TZ=UTC`) on the owner's Windows 11 host, Python 3.11.16.
- **Ordering:** every test below was written after operational confidence
  (attempt 11 ended 16:19:33Z; see the E2E timeline). Each targets an
  observed defect or an envelope contract named in the locked test plan.
- **Result (final head, see test report):** `tests/evals/test_local_qualification_policy.py`
  15 passed; `tests/agent/test_minimum_context_explicit_local.py` 6 passed.

| Test (plan name) | EARS | Result | Assertion |
|---|---|---|---|
| `qualification_receipt_audit` → `tests/evals/test_local_qualification_policy.py::test_every_published_attempt_resolves_to_a_valid_frozen_manifest` | M1, P1, S1 (live half) | pass | Checks all 13 published attempts: (1) each resolves to a published manifest whose content digest equals its id and its outcome's `manifest_id`. (2) Bring-up identity fields are present with 64-hex hashes. (3) Full M1 identity (interpreter, task corpus, tokenizer and template fingerprints, seed) is present, or the attempt ran zero inference; attempts 01–05 used incomplete bring-up manifests and ran none. (4) The rendered prefix is either `not-measured` with a reason or measured with a count, never invented. (5) A stop cause is kept. (6) Cleanup took at most 5 s and the listener closed where recorded. (7) Launch and request counters never reset and never exceed that revision's limits. |
| `qualification_receipt_audit` (privacy half) → `…::test_published_evidence_excludes_private_paths_and_credentials` | P1 | pass | Every published JSON file under `qualification/` (receipts, manifests, sentinel record) is free of drive-letter or home user paths, `Bearer` values and 48-hex ephemeral tokens. |
| `manifest_identity_contract` → `…::test_changed_parameter_artifact_or_source_refuses_launch` (5 cases) | M2 | pass | The frozen continuation manifest first passes identity. Changing an execution parameter, the model hash, the backend hash, the source commit, or the `source_dirty` flag then yields the named refusal. |
| `manifest_identity_contract` → `…::test_manifest_frozen_from_a_dirty_tree_refuses_launch` | M2 | pass | A manifest re-frozen with `source_dirty: true` and a valid digest is refused by the source-revision branch, not by the digest check. |
| `manifest_identity_contract` → `…::test_uncommitted_changes_at_launch_refuse_a_valid_manifest` | M2 | pass | With a valid digest and a matching commit, uncommitted working-tree changes at launch time still refuse the launch. `run.py` now checks `git status --porcelain` at launch as well as at freeze. |
| `admission_stop_contract` → `…::test_admission_requires_measured_capacity_on_each_device` | M2, S2 | pass | Admission passes at exactly the per-device requirement. It fails one byte below on either device and with no sample, and spare VRAM cannot pay for missing RAM. |
| `admission_stop_contract` → `…::test_running_attempt_stops_one_byte_below_either_reserve` | S2 | pass | The reserve stop does not fire at the reserve, and does fire one byte below it on RAM or on VRAM. |
| `admission_stop_contract` → `…::test_ready_server_must_match_the_frozen_candidate` (3 cases) | D2 | pass | A ready server with two slots, a different context, or a different model path is refused before generation. The frozen shape passes. |
| `admission_stop_contract` → `…::test_page_in_stops_only_under_ram_pressure_while_page_out_always_counts` | S2 | pass | Regression for attempts 05 and 09. High page-in never stops the run at or above the RAM-pressure line, or inside the load allowance. Below the line, it stops on exactly the third consecutive sample, and a quiet sample resets the streak. Three high page-out samples stop the run regardless of RAM or load phase. |
| Explicit local context floor → `tests/agent/test_minimum_context_explicit_local.py::test_pinned_local_window_without_auto_compression_is_admitted` (2 cases) | D1 (Hermes defect, attempt 06) | pass | A local custom route pinned at 8192 with auto-compression off constructs a real `AIAgent` whose window is 8192, both with no reported served window and with a served window equal to the pin. The local probe is patched, so no network is touched. **Proven red on base:** with `agent/agent_init.py` from `cd2185c288` it fails. |
| `…::test_floor_still_applies_outside_the_explicit_local_pin` (4 cases) | D1 boundary | pass | Each of these still raises "below the minimum": the same pin with auto-compression on, a non-local custom URL, a configured served window above the pin (16384), and a detected served window below the pin (4096). The below-pin case is **proven red on the round-1 code**, where `max()` hid the smaller window; round 2 fixed it in `agent/agent_init.py`. **Scope:** only a window the server *reports* (Ollama `num_ctx`) is compared. llama.cpp and vLLM report none, so on this sprint's backend the pin is operator-trusted, following Hermes's "pin wins" rule. The lab's readiness `n_ctx` check (`server_identity_mismatch`) is the served-window guard. |

Existing affected coverage re-run and passing:

- `tests/agent/test_ollama_num_ctx.py` (13): the existing floor and refusal
  wording contracts are unchanged.
- `tests/hermes_cli/test_local_runtime_gguf.py` (1): the added `tensor_sizes`
  field kept the reader's contract.
- `tests/hermes_cli/test_local_runtime_processes.py` (8).

## Not unit-tested (carried by T-211)

These checks remain inline in `run.py::observe` and the launch path:

- stale or missing telemetry, and scheduler lag;
- the launch-count and aggregate-time predicates;
- stall- and deadline-triggered cleanup.

A collector exit was exercised live in attempt 01. The launch cap was reached
but not exceeded, since no tenth launch was attempted.
