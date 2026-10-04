# Default local operating policy (INT-0007 AC6, partial)

The default settings for running Hermes Agent against a local model, for
the settings Sprint 3 measured. The criterion is **throughput**: machine
time per verified item, not per-step latency (INT-0007 AC6). Every ranked
setting links to its receipts in
[`sprint-tests/qualification/`](../sprints/s3/sprint-tests/qualification/)
and to the operational ledger
([`operational-ledger.md`](../sprints/s3/sprint-tests/operational-ledger.md)).

**All results are single seeded runs** (seed 42) on one host. They select
defaults; they are not evidence of statistical superiority.

## Scope of the evidence

| Item | Value |
|---|---|
| Host | AMD Ryzen 9 5900X, 32 GiB RAM, RTX 2080 Ti (11 GiB), NVIDIA 596.49, Windows 11 |
| Model | Qwen3.8-27B UD-Q4_K_M (hybrid: 48 Gated DeltaNet, 16 attention layers), FFN weights on CPU |
| Backend | llama.cpp b10964 (CUDA 12.4), q8_0 KV cache, flash attention, `-b 256 -ub 128 -t 6` |
| Calibration | prefill 96.8 tok/s, decode 3.55 tok/s, load 14–22 s warm (45 s with a cold kernel cache) |
| Task | the long multi-file task: 8 user turns, 3 seeded defects plus 1 feature, hidden verifier |

## Ranked settings (varied in Sprint 3)

Ranked by machine time per verified item. Machine time runs from the first
request to the last response, excluding load. Under the plan's rule
(build-plan O1), failures and stops count: a run's cost includes every
attempt of that run, failed or stopped, divided by the items it verified.
The completed run's own figure is shown beside it.

| Rank | Setting | Verified | Requests | Per verified item, all attempts (O1) | Completed run only | Receipts |
|---|---|---|---|---|---|---|
| 1 | Thinking **off**, greedy (R0) | 4/4 | 18 | **205 s**, 558 tokens | 180 s, 535 tokens | attempts 07 (telemetry race), 08 |
| 2 | Thinking on, budget 256, greedy, echo off (R1) | 4/4 | 20 | **345 s**, 1,058 tokens | 346 s, 1,058 tokens | attempt 09 |
| 3 | Thinking on, budget 256, greedy, **echo on** (R2) | 4/4 | 18 | **865 s**, 2,636 tokens | 352 s, 1,151 tokens | attempts 10 (wire defect), 11 (host maintenance), 12 (owner apps), 13 |

The order is the same under both readings. R2's all-attempts cost comes
mostly from one repaired lab defect and two host resource stops, not from
echo. Its completed run was within 2% of R1.

**Sampling** (screen, turns 1–3 only, attempt 06). Greedy ranked first in
both thinking modes:

| Mode | Order (time per verified item) |
|---|---|
| Thinking off | greedy 259 s < model default (1.0 / 0.95 / 20) 319 s < vendor non-thinking (0.7 / 0.8 / 20, presence 1.5): failed, wrote helper files outside its fixture twice |
| Thinking on | greedy 515 s < vendor or model default 521 s; the mid probe (0.6 / 0.95 / 20) is not selectable |

**Reasoning echo** (O2). With thinking on and echo off, every continued
request rolls back the previous turn's generated tokens. The median was 161
uncached tokens per continued request in R1, against 56 with thinking off.
With echo on, the median fell to 60 and history stays append-only: 12 of
17 continued requests rolled back at most 1 token. The exception is every
turn whose reasoning hit the 256-token budget: all 5 large rollbacks
(412–678 tokens) followed exactly those turns, because the forced end of
thinking renders differently from what was generated. Echo removed about
60% of the prefill work, but throughput on the completed runs was unchanged
(352 s against 346 s per verified item), because decode dominates on this host.

**Checkpoint density** (O3). R3 was not run. R1's median uncached tokens per
continued request (161) never approached the 2,000 threshold. llama.cpp's
default end-of-prompt checkpoint already bounds each rollback to one turn,
so denser checkpoints (`--checkpoint-min-step 512`) have nothing to recover
on this workload.

## Recommended defaults

1. **Thinking off, greedy sampling** for agentic tool work on a
   decode-bound host. It verified the same items as bounded thinking in
   about half the machine time. Decode was 90% of R0's machine time, so
   every reasoning token costs throughput directly.
2. **If thinking is on:** greedy, a bounded budget, and
   `model.reasoning_echo: true`. It is throughput-neutral here, but it keeps
   history append-only, so prefill stops growing with each turn's
   reasoning. That matters more on longer sessions and slower-prefill
   hosts, which were not measured. Expect a one-turn rollback after each
   budget-truncated think block, until uncapped thinking (T-218) removes the
   cut.
3. **Keep the NVIDIA kernel cache persistent.** A cold driver JIT cache
   made the first prompt 30× slower (15.6 against 115 tok/s) and the load
   2.5× slower. Never run llama-server with a sandboxed or fresh `APPDATA`
   or `CUDA_CACHE_PATH`. A client machine pays the cost once per driver
   version, and host-derived deadlines must count kernel-cache growth as
   progress, not as a stall.

## Fixed choices and rationale

| Setting | Choice | Rationale |
|---|---|---|
| Context | 32,768 | Peak rendered input was 7,867 tokens. Admission fits 32K with 5 frozen checkpoints (5 × 149.6 MiB) inside the 4 GiB RAM reserve. Larger windows were not measured. |
| Environment probe | `agent.environment_probe: false` | It adds a model turn and tokens with no task value (Sprint 2, L-19). |
| Time model | m = 2.0, k = 20, f = 0.5, U = 2048 (T-215) | Every deadline derives from the host's own calibration. Over 165 requests, predicted over actual time (after the rearm) had a median of 4.3 and a p10 of 1.56. It prices the full output cap, so it is a conservative bound, not a forecast. It under-predicted once, by 9%: a full-cap decode at about 8K context, because decode slows as context grows. Enforcement uses the stall rule and a floor-priced backstop, which was never reached. |
| Toolset | `terminal` only | The task needs only shell work. Every extra tool schema is sent on every request. |
| Checkpoints | `--ctx-checkpoints` from calibration (5 here) | RAM headroom at admission divided by the measured checkpoint size, capped at 32. |

## Pending Sprint 4

- **MTP speculative decoding** (T-217): decode is the bottleneck, so this is
  the largest lever.
- **Uncapped thinking** (T-218): this also removes the budget-cut re-render
  mismatch.
- **Compression** with throughput-derived deadlines (T-219).

## Proposed live-profile changes (not applied; the owner decides)

The live profile is unchanged (P2). Its `presets.ini` currently uses a
98,304 context, the MTP draft, model-default sampling (`temp = 1`,
`top-p = 0.95`, `top-k = 20`) and a vision projector. The proposal for a
thinking-off agent profile, measured only at 32K without MTP:

```ini
# presets.ini — proposal
temp = 0
top-k = 0
top-p = 1.0
```

```yaml
# config.yaml — proposal
agent:
  environment_probe: false
model:
  reasoning_echo: true   # matters only when thinking is on
```

Keep MTP and the larger context as they are until T-217 measures them.
