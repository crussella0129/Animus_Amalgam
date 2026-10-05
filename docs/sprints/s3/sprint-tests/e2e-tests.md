# Sprint 3 End-to-End Results (live operation, run first)

- **Host:** the owner's Windows 11 machine (Ryzen 9 5900X, 32 GiB, RTX 2080
  Ti), running Qwen3.8-27B UD-Q4_K_M on llama.cpp b10964 (CUDA 12.4).
- **Lab:** `evals/local_qualification`. The lab root is outside the
  repository, and every attempt was frozen at a clean commit (the manifest
  `source_commit`).
- **Narrative:** the failure → diagnosis → repair → replay record is in
  [`operational-ledger.md`](operational-ledger.md). Per-request receipts and
  sanitized manifests for all 13 attempts are in
  [`qualification/`](qualification/).
- **Ordering:** every live result below predates the operational confidence
  record (2026-10-04T01:58Z, `210d043a2a`). The one exception is the T5
  bring-up replay, which is model-free and was re-run after critique rounds
  1 and 2. Round 3 changed nothing the bring-up runs.
- **Machine time:** first request to last response, excluding load (the
  screen's locked definition), published per session in each receipt
  (`machine_time`). The O1 figures divide the machine time of every attempt
  of a run by the items those attempts verified. Sessions cut short by an
  attempt stop are scored from their preserved fixture (L2) and screened
  (L4) from the conversation their last request forwarded. None was
  flagged.

| Plan test | EARS | Attempt | Result |
|---|---|---|---|
| `bringup_stop_control_check` | T5 | `9086be2dae`; replays at `efeb4ef4c4` and `1fca1a3095` | **Pass.** No model is loaded, and the stall rule watches each child's output. The latest replay (2026-10-05T20:37Z): the chatty child survived 3 windows (6.0 s); the silent child was stopped at 2.015 s against a 2.0 s window; its 5-process owned tree was gone in 0.047 s; the sentinel survived. |
| `live_arm_replay` | C1, M1 | 01, 04 | **Pass.** A deliberate untracked file refused launch with 0 launches consumed (attempt 01, published). The calibration launch matched the frozen argv: `--slot-save-path` present, no `--predict`, context 32768. The ready server's `/props` model and context matched the manifest (`server_props` event). Hermes's explicit-pin served-window check admitted the 32K pin: every session's CLI started against the pinned 32768 window, with no context-floor refusal. |
| `live_calibration_record` | C2 | 04 | **Pass.** P 96.76 tok/s; D 3.55 tok/s (a checked 1–40 decode sample of 111 tokens); O 0.024 s; T_load 45.4 s (cold kernel cache); T_cli 3.05 s; a 149.6 MiB checkpoint; 5 frozen checkpoints. The 81,365 s budget and the owner's time-model decision were in the ledger and the manifests before the screen. The fail-closed path is covered by `test_calibration_fails_closed_on_a_missing_field`. |
| `live_cross_session_prefix` | C3, AC3 | 04 (miss), 05 and 06 (pass) | **Pass after repair.** Attempt 04 missed for lab reasons: per-session paths and a blanket slot erase. After the repair, the rendered prompts were byte-identical and the second smoke reused 1147 of 1151 tokens. |
| `live_main_cancel` | C4 | 04 | **Pass.** The cancel came at the first decoded token. The slot was idle in 0.84 s, owned cleanup took 0.88 s and the listener closed. |
| `task_precheck` (live) | L3 | 05–13 | **Pass.** 22 reference requests; the largest edit was 179 tokens against the 512 cap; a peak of 6,889 tokens plus a 5,632-token echo reserve fits within the 31,488 ceiling. |
| `live_sampling_screen` | S1–S3 | 06 | **Pass.** Six configurations ran turns 1–3. Greedy was selected in both modes (off 259 s, on 515 s per verified item). off-vendor failed, contaminated twice. Reported as single seeded screening runs. |
| `live_full_run_R0` | L1, L2, L4, O1 | 07 (stopped), 08 | **4/4 verified**, 18 requests (AC1 coverage not met). Per verified item: 205.3 s across all attempts (attempt 07 cut short at 3 requests, 0 verified from its preserved fixture), 180.2 s on the completed run. |
| `live_full_run_R1` | L1, L2, L4, O1, O2 | 09 | **4/4 verified**, 20 requests (AC1 coverage met), 345.4 s per verified item. Every continued request rolls back the previous turn (median uncached 161). |
| `live_full_run_R2` | L1, L2, L4, O1, O2 | 10–12 (stopped), 13 | **4/4 verified**, 18 requests. Per verified item: 384.3 s across all attempts (attempts 10, 11 and 12 verified 3, 0 and 2; attempt 12's two were screened clean at publish), 352.6 s on the completed run. Excluding attempt 12's two items gives 494.0 s; dividing by one run's 4 items gives 864.6 s. Append-only (median uncached 60), except after a budget-truncated think block (all 5 large rollbacks). |
| R3 (density) | O3 | — | **Not run, by rule.** R1's median uncached count (161) does not exceed 2,000. |
| `operational_repair_replay` | O4 | ledger | **Pass.** Every in-scope failure is linked to its diagnosis, repair commit and replay (the provenance table in the ledger). |
| `policy_evidence_review` | P1 | policy | **Pass**, reviewed 2026-10-05T21:38Z at `663bac6a2a`. [`local-operating-policy.md`](../../../lineage/local-operating-policy.md) ranks thinking mode and echo by machine time per verified item under every O1 reading. It ranks sampling from the screen and explains checkpoint density (R3 not triggered). Each figure names its attempts, published in `qualification/`. Context, environment probe, time model, toolset and checkpoints carry their rationale. MTP, uncapped thinking and compression are marked pending Sprint 4, and every result is labelled a single seeded run. The echo-on recommendation for thinking-on use now states that it sits outside the time ranking, where echo ranks third, and is chosen for INT-0007 AC3. |
| `live_profile_untouched` | P2 | live profile | **Pass** at 2026-10-05T21:38:24Z, head `663bac6a2a`. The live `config.yaml` is 6,700 bytes, `a48b4add7508261c13ddb54c66f9d5a4e9b3e62ada7f0520d34f4ccd3d848f1c`, and `runtimes/llamacpp/presets.ini` is 580 bytes, `bb35c72da07c0cfce2409ba22340d5bc1157821a03ac2788500f549253f8d0a1`; both equal the plan baseline. It is re-checked at sprint close. |
| Prediction accuracy | O5, AC7 | all | 169 post-calibration requests. On the 165 completed requests, rearmed predicted/actual had a median of 4.34 (p10 1.56, p90 11.5), with one 9% under-prediction (a full-cap decode at about 8K context). The 4 attempt-stopped requests keep their stop cause and elapsed time; the pre-repair wire never recorded their predictions. Every stall and stop is listed in the ledger. |

## Not run or deferred

- **MTP (AC4), unbounded thinking (part of AC2) and compression (AC5):**
  Sprint 4 (T-217, T-218, T-219).
- **Auxiliary cancellation:** there was no auxiliary traffic in Sprint 3; it
  moves to T-219.
- **The live sequential-retry path:** not re-triggered, because attempts
  11–13 produced no cap-truncated tool call. It is covered by the
  integration test.
- **A backstop stop:** never reached live. The decision is covered by
  `test_stall_and_backstop_semantics` on `throughput.step_stop`, which the
  lab uses for requests and the load.
