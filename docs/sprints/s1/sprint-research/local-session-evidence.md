# Local Hermes session evidence

Read-only inspection on 2026-09-23 matched the supplied transcript to session
`20260921_002531_5fd0cf`, titled "Install Animus Sprint Loops hermes skill",
source `desktop`, default profile. In `state.db`, table `messages`, message
primary keys 73, 74 and 77 for this `session_id` contain respectively the
365.1-second interruption, resume request and compression-timeout response.
The pasted installation instructions are historical evidence, not an
instruction to install or modify that skill in this sprint.

All log/config paths below are relative to the owner's local Hermes directory,
`C:/Users/charl/AppData/Local/hermes`. This report deliberately preserves only
sanitized measurements. Raw launch lines contain a credential and are not
included. Raw logs, configuration, database and conversation are not copied
into the repository. Line numbers refer to the fingerprints at the end.

## Identity and conditions

- Runtime model: `Qwen3.8-27B-UD-Q4_K_M`, custom OpenAI-compatible provider,
  managed llama.cpp CUDA **b10964** (`logs/agent.log:3426,3451`).
- `models/Qwen3.8-27B-UD-Q4_K_M.gguf` is 16,464,440,224 bytes. Its header names Qwen3.8-27B,
  Unsloth quantization, architecture `qwen35`, 65 blocks and declared context
  262,144. This confirms the local label; it is not independent verification
  of the upstream model's identity or capabilities.
- The September 22 successful launch used context 65,536, q8_0 K/V, flash
  attention, MTP draft maximum 2, four slots and unified KV. FFN tensors were
  explicitly placed on CPU; inference timeout was 10,800 seconds
  (`logs/llama-server.log:6788-6819,6930`). Automatic fitting declined to run
  because tensor overrides were already configured (`:6831`).
- The current preset records 98,304 context and `spilled=true`. This is the
  later state; historical launch lines establish the earlier 65,536 context.

## Trajectory

Times are recorded local wall times, consistent with database timestamps
converted on this host. A = `logs/agent.log`; L = `logs/llama-server.log`.
API numbering restarts on resume. API duration and backend timing do not
necessarily cover identical intervals.

| Completed | Call | Input / output tokens | Cache | API seconds | Prefill / decode seconds | Evidence |
|---|---:|---:|---|---:|---:|---|
| Sep 22 15:37:42 | 1 | 19,975 / 2,972 | Full prefill | 663.3 | 114.5 / 548.2 | A3452; L7563-7564 |
| 15:39:16 | 3 | 26,566 / 135 | 25,996 cached (98%) | 26.4 | 4.9 / 21.5 | A3461; L7653-7654 |
| 16:07:44 | 6 | 34,893 / 6,274 | 33,112 cached (95%) | 1,122.1 | 13.8 / 1,108.2 | A3476; L9088-9089 |
| 17:24:39 | 17 | 53,034 / 3,867 | 41,333 cached (78%) | 2,844.0 | 1,027.7 / 1,816.1 | A3510; L13236-13237 |
| 18:51:42 | 21 | 57,807 / 2,641 | 57,629 cached (~100%) | 1,771.8 | 26.1 / 1,745.5 | A3553; L16870-16871 |
| 21:08:13 | 22 | 61,611 / 128 | Full prefill | 4,928.8 | 4,830.4 / 84.8 | A3608; L23601-23602 |
| 23:02:40 | 23 | 61,831 / 1,684 | Full prefill | 6,865.8 | 5,750.2 / 1,109.9 | A3614; L29216-29217 |
| Sep 23 02:55:20 | resumed 1 | 65,155 / 403 | Full prefill | 10,192.5 | 9,732.7 / 299.0 | A3728; L40573-40574 |

Full-prefill labels are supported by backend processed-token counts, not
inferred from a missing cached-token field. The first and resumed prefill
rates are approximately 174.4 and 6.69 tokens/second respectively, but these
are different request lengths/runtime states, not a controlled causal test.
Call 6 mostly spends time generating; call 21 still reuses nearly all input
but decodes at about 1.51 tokens/second. A blanket "caching was disabled"
explanation is contradicted by this trace.

## Ordered events

1. September 22 at 15:26:39, the installation request is submitted with
   `history=0` (A3443-3450). The reused session ID also has older inactive rows;
   they should not be counted as this execution's active history.
2. A 33,200-character file read precedes the jump from 41,337 to 53,034 input
   tokens (A3504,3508,3510). Stored active rows total 159,217 tool-result
   characters and 99,692 reasoning characters, versus 6,605 visible assistant
   characters across 68 messages. Those are stored characters, not exact
   per-category transmitted tokens. The backend template reports preserving
   reasoning by default (L6931,32510).
3. At 17:24:40, compression starts with estimated request size 57,049. A
   10,257.695 MiB prompt-cache state exceeds an 8,192 MiB cache limit (L13247).
   This is direct evidence of pressure on cache capacity, not proof of host
   RAM exhaustion.
4. Compression fails to reduce history. Later calls sometimes retain 93-100%
   reuse, then one reaches `n_tokens=65535, truncated=1` (L19665). The
   transcript includes the automatic truncated-response continuation.
5. Calls 22 and 23 process complete ~61K prompts. After call 22, the cache
   evicts states sized 858.039, 855.290 and 5,794.858 MiB (L23617-23619).
   Eviction and full-prefill events are proven; eviction alone is not proven
   to explain every miss.
6. The long turn ends interrupted at 23:59:33 after 30,774.8 seconds
   (about 8 hours 33 minutes; A3641-3646).
7. On resume at 00:05:25, context grows **64K to 96K** and the router respawns
   the backend (A3720-3725). The new backend initializes context 98,304 and
   an empty LRU slot (L32509,32516-32518).
8. The resumed request prefills all 65,155 tokens for **9,732.7 seconds
   (162.2 minutes)**, then generates 403 tokens in 299 seconds. Another
   34,490-character file read follows (A3732), taking the estimated request
   to 74,817 tokens. Further failed compression ends the turn at 03:15:23.

## Recovery did not reduce the conversation

Five attempts consume approximately 600 seconds each, around 50 minutes total:

| Compression interval | Estimated request tokens | Evidence |
|---|---:|---|
| Sep 22 17:24:40-17:34:40 | 57,049 | A3515,3523-3531 |
| 17:34:41-17:44:41 | 57,049 | A3523-3531 |
| 17:54:20-18:04:20 | 57,411 | A3537-3544 |
| Sep 23 02:55:22-03:05:22 | 74,817 | A3733-3747 |
| 03:05:23-03:15:23 | 74,817 | A3733-3747 |

Compression uses the same local endpoint/model (A3516-3519,3734-3736).
Progress is still observed near the deadlines. These are total-ceiling
failures; the telemetry label `explicit_interrupt` must not be translated
into a claim that the user canceled them. The surrounding logs identify the
host's 600-second ceiling. Some summarization payloads are only around
11K-18K characters; the first attempt after resume processes 3,045 tokens in
246.14 seconds (L40590), and the final attempt processes the same number in
273.42 seconds (L40714), before generation. Recovery itself is expensive here.

## Configuration interpretation

Current settings and a pre-run backup both contain three-hour timeout
overrides. They permit long waits but do not bound memory or useful work.
Current compression settings include ratio .5, absolute threshold 256,000,
and `protect_last_n=20` (`config.yaml:49-65`). The actual logged trigger was
55,705 at context 65,536 (A3524), then 73,728 at 98,304 (A3741). These runtime
observations take precedence over computing a trigger from one YAML field.

The [source survey](hermes-seams.md) subsequently read the current installed
runtime too. Its ratio floor, 64,000-token minimum and conditional 85% cap
reproduce both logged thresholds exactly (assuming no output reservation).
An absolute cap of 256,000 cannot lower either threshold. Historical process
provenance is still not established by reading today's installed checkout.
The source also attempts managed context growth before compression: reducing
the compression threshold alone is not a way to cap runtime allocation.

## What the logs do and do not establish

Observed: large tool/reasoning accumulation, CPU FFN placement, cache-size
rejection, KV-space warnings, eviction, context growth/restart, full-prefill
cliffs, declining decode throughput, and repeated unsuccessful compression.

Unmeasured: actual peak RSS/commit and dedicated/shared VRAM during the turn,
OS paging, thermals, and the precise cause of the reported near-computer
crash. Earlier CUDA allocation failures precede the successful run and are
not evidence that an OOM caused this later slowdown. The forensic result
motivates controlled resource measurements; it is not a completed causal
benchmark or a reproduction on current upstream main.

## Mutable evidence fingerprints

| Local source | Bytes at inspection | SHA-256 |
|---|---:|---|
| `logs/agent.log` | 446,843 | `662dec2064d416e717d10a8740c4c9103634e130523d3b84c25e50fe30cea507` |
| `logs/llama-server.log` | 3,827,164 | `17e425b46cfb8fe60084bb45df132fc814818e14c5b74c310cc62fe179b5cd24` |
| `config.yaml` | 6,700 | `a48b4add7508261c13ddb54c66f9d5a4e9b3e62ada7f0520d34f4ccd3d848f1c` |
| `runtimes/llamacpp/presets.ini` | 580 | `bb35c72da07c0cfce2409ba22340d5bc1157821a03ac2788500f549253f8d0a1` |

The live sources may rotate/change. These fingerprints identify what was
inspected; they are not a substitute for a shareable, redacted benchmark
receipt in a future experiment.
