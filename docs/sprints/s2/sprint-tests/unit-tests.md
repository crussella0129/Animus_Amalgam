# Sprint 2 Unit Test Results (after operational confidence)

- **Tested head:** `4bc4f5ea89` (all tested code is unchanged from `e5965195a8`)
- **Date:** 2026-09-24
- **Runner:** `scripts/run_tests.sh` (per-file subprocess isolation, clean
  env, `TZ=UTC`) on the owner's Windows 11 host, Python 3.11.16. Focused runs
  used 48 workers; the affected-suite run used 16.
- **Ordering:** each test below was written after operational confidence
  (attempt 11). Each targets an observed defect or an essential envelope
  contract named in the locked test plan.

| Test (plan name) | EARS | Result | Assertion |
|---|---|---|---|
| `manifest_identity_contract` → `tests/evals/test_local_qualification_policy.py::test_published_manifest_identity_resolves_to_its_digest` | M1 | pass | The published continuation manifest's content digest equals its `id`, and it passes identity against its own commit and artifact hashes. |
| `manifest_identity_contract` → `…::test_changed_parameter_artifact_or_source_refuses_launch` (4 cases) | M2 | pass | Changing an execution parameter (`input_tokens`), the model hash, the backend hash or the source commit each yields a named refusal (digest / model artifact / backend artifact / source revision). |
| `admission_stop_contract` → `…::test_admission_requires_measured_capacity_on_each_device` | M2, S2 | pass | Admission passes at exactly the per-device requirement and fails one byte below on either device or with no sample. Spare VRAM cannot pay for missing RAM. |
| `admission_stop_contract` → `…::test_page_in_stops_only_under_ram_pressure_while_page_out_always_counts` | S2 | pass | Regression for attempts 05 and 09. High page-in never stops the attempt at or above the RAM-pressure line, or inside the load allowance. Below the line, it stops on exactly the third consecutive sample, and a quiet sample resets the streak. Three high page-out samples stop regardless of RAM or load phase. |
| Explicit local context floor → `tests/agent/test_minimum_context_explicit_local.py` (2) | D1 (reproduced Hermes defect, attempt 06) | pass | A local custom route pinned at 8192 with auto-compression off constructs a real `AIAgent`. The same pin with compression on still raises "below the minimum". **Proven red on base:** with `agent/agent_init.py` from `cd2185c288`, the admission test fails (1 failed, 1 passed). |

Existing affected coverage re-run: `tests/agent/test_ollama_num_ctx.py` (13
passed; existing floor/refusal wording contracts unchanged) and
`tests/hermes_cli/test_local_runtime_gguf.py` (1 passed; the added
`tensor_sizes` did not change the header reader's existing contract).

## Not unit-tested (explicit)

- Stale or missing telemetry and scheduler-lag stops remain inline,
  time-based checks in `run.py::observe`. They were exercised live (attempt
  01: a collector exit stopped the attempt before admission) but have no
  deterministic unit test. This is carried to T-210, where the harness is
  extended anyway.
