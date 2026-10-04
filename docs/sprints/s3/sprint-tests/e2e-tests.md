# Sprint 3 End-to-End Results (live operation, run first)

- **Host:** the owner's Windows 11 machine (Ryzen 9 5900X, 32 GiB, RTX 2080
  Ti), running Qwen3.8-27B UD-Q4_K_M on llama.cpp b10964 (CUDA 12.4).
- **Lab:** `evals/local_qualification`. The lab root is outside the
  repository, and every attempt was frozen at a clean commit.
- **Narrative:** the full failure → diagnosis → repair → replay record is in
  [`operational-ledger.md`](operational-ledger.md). The per-request receipts
  and manifests are in [`qualification/`](qualification/).
- **Ordering:** every live result below predates the operational confidence
  record (2026-10-04T01:58Z, `210d043a2a`) and every formal test run.

| Plan test | EARS | Attempt | Result |
|---|---|---|---|
| `live_arm_replay` | C1, M1 | 01, 04 | **Pass.** A deliberate untracked file refused launch with 0 launches consumed. The calibration launch matched the frozen argv and context. |
| `live_calibration_record` | C2 | 04 | **Pass.** P 96.76 tok/s, D 3.55 tok/s (a checked 1–40 decode sample of 111 tokens), O 0.024 s, T_load 45.4 s (cold kernel cache), T_cli 3.05 s, a 149.6 MiB checkpoint and 5 frozen checkpoints. The 81,365 s budget and the owner's time-model decision were in the ledger and the manifests before the screen. The checkpoint count was recomputed from attempt 04's evidence after the admission-sample repair. |
| `live_cross_session_prefix` | C3, AC3 | 04 (miss), 05 and 06 (pass) | **Pass after repair.** Attempt 04 missed for lab reasons: per-session paths in the system prompt and a blanket slot erase. After the repair, the two smokes' rendered prompts were byte-identical and the second reused 1147 of 1151 tokens. |
| `live_main_cancel` | C4 | 04 | **Pass.** The cancel came at the first decoded token. The slot was idle in 0.84 s, owned cleanup took 0.88 s and the listener closed. |
| `task_precheck` (live) | L3 | 05–13 | **Pass.** 22 reference requests; the largest edit was 179 tokens against the 512 cap; a peak of 6,889 tokens plus a 5,632-token echo reserve fits within the 31,488 ceiling. |
| `live_sampling_screen` | S1–S3 | 06 | **Pass.** Six configurations ran turns 1–3. Greedy was selected in both modes (off 259 s, on 515 s per verified item). off-vendor failed, contaminated twice. Reported as single seeded screening runs. |
| `live_full_run_R0` | L1, L2, L4, O1 | 08 | **4/4 verified**, 18 requests (AC1 coverage not met), 182 s per verified item. |
| `live_full_run_R1` | L1, L2, L4, O1, O2 | 09 | **4/4 verified**, 20 requests (AC1 coverage met), 347 s per verified item. Every continued request rolls back the previous turn (median uncached 161). |
| `live_full_run_R2` | L1, L2, L4, O1, O2 | 13 (10–12 stopped) | **4/4 verified**, 18 requests, 354 s per verified item. Append-only (median uncached 60), except after a budget-truncated think block (all 5 large rollbacks). |
| R3 (density) | O3 | — | **Not run, by rule.** R1's median uncached count (161) does not exceed 2,000. |
| `operational_repair_replay` | O4 | ledger | **Pass.** Every in-scope failure is linked to its diagnosis, repair commit and replay (the provenance table in the ledger). |
| Prediction accuracy | O5, AC7 | all | 165 requests. Rearmed predicted/actual: median 4.34, p10 1.56, p90 11.5. One 9% under-prediction: a full-cap decode at about 8K context. Every stall and stop is listed with its cause in the ledger. |

## Not run or deferred

- **MTP (AC4), unbounded thinking (part of AC2) and compression (AC5):**
  Sprint 4 (T-217, T-218, T-219).
- **Auxiliary cancellation:** there was no auxiliary traffic in Sprint 3; it
  moves to T-219.
- **The wire's sequential-retry repair:** the live path was not re-triggered.
  Attempts 11–13 produced no cap-truncated tool call. The repair is proven
  by an offline repro and by the integration test
  `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused`.
