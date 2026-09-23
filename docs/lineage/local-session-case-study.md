# Local Hermes long-session case study

This sanitized case preserves the owner's supplied failure example without
committing the private transcript, raw logs, live configuration, or launch
credentials. Read-only inspection on 2026-09-23 matched it to session
`20260921_002531_5fd0cf`, title “Install Animus Sprint Loops hermes skill,”
source `desktop`, default profile. In the private `state.db` `messages` table,
primary keys 73, 74, and 77 contain respectively the reported 365.1-second
interruption, resume request, and compression-timeout response.

All `A` and `L` coordinates below refer to the fingerprinted private files
`logs/agent.log` and `logs/llama-server.log` listed at the end. They are
evidence coordinates, not repository paths.

## Runtime conditions

The runtime identifies `Qwen3.8-27B-UD-Q4_K_M` through a custom
OpenAI-compatible endpoint and managed llama.cpp CUDA b10964 (A3426,3451).
The local GGUF header names Qwen3.8-27B, Unsloth quantization, `qwen35`, 65
blocks, and a declared 262,144-token context. That confirms the local label,
not upstream provenance or capability.

The successful September 22 launch used a 65,536-token context, q8_0 K/V,
flash attention, MTP draft maximum 2, four slots, unified KV, and explicit CPU
placement for FFN tensors (L6788-6819,6930). Its 10,800-second timeout allowed
long work; it did not bound memory, prompt growth, or useful completion.

## Measured trajectory

Times are local wall times. “Full prefill” is backed by server processed-token
counts rather than inferred from a missing cache field.

| Completed | Call | Input / output tokens | Cache | API seconds | Prefill / decode seconds | Evidence |
|---|---:|---:|---|---:|---:|---|
| Sep 22 15:37:42 | 1 | 19,975 / 2,972 | Full prefill | 663.3 | 114.5 / 548.2 | A3452; L7563-7564 |
| 15:39:16 | 3 | 26,566 / 135 | 25,996 (98%) | 26.4 | 4.9 / 21.5 | A3461; L7653-7654 |
| 16:07:44 | 6 | 34,893 / 6,274 | 33,112 (95%) | 1,122.1 | 13.8 / 1,108.2 | A3476; L9088-9089 |
| 17:24:39 | 17 | 53,034 / 3,867 | 41,333 (78%) | 2,844.0 | 1,027.7 / 1,816.1 | A3510; L13236-13237 |
| 18:51:42 | 21 | 57,807 / 2,641 | 57,629 (~100%) | 1,771.8 | 26.1 / 1,745.5 | A3553; L16870-16871 |
| 21:08:13 | 22 | 61,611 / 128 | Full prefill | 4,928.8 | 4,830.4 / 84.8 | A3608; L23601-23602 |
| 23:02:40 | 23 | 61,831 / 1,684 | Full prefill | 6,865.8 | 5,750.2 / 1,109.9 | A3614; L29216-29217 |
| Sep 23 02:55:20 | resumed 1 | 65,155 / 403 | Full prefill | 10,192.5 | 9,732.7 / 299.0 | A3728; L40573-40574 |

The trace does not support one cache-loss explanation. Early requests reuse
95-98% of their prefixes; call 21 reuses almost everything yet spends about
29 minutes decoding at roughly 1.51 tokens/second. Call 6 also spends almost
all its time generating. Later calls show separate cold-prefill cliffs.

## Accumulation, cache pressure, and restart

Stored active rows contain 159,217 tool-result characters and 99,692 reasoning
characters versus 6,605 visible assistant characters across 68 messages.
These character totals are not exact transmitted-token attribution. A
33,200-character file read precedes the 41,337-to-53,034 input-token jump
(A3504,3508,3510); another 34,490-character read occurs after resume (A3732).

At the first compression trigger, llama.cpp rejects a 10,257.695 MiB prompt-
cache state because its configured limit is 8,192 MiB (L13247). Later the
context reaches `n_tokens=65535, truncated=1` (L19665). After call 22, cache
states of 858.039, 855.290, and 5,794.858 MiB are evicted (L23617-23619).
These events establish cache-capacity pressure and eviction, not their share
of every delay.

The long turn ends interrupted after 30,774.8 seconds, about 8 hours 33
minutes (A3641-3646). On resume, managed context grows from 64K to 96K and
respawns the backend (A3720-3725). The new server has an empty slot and
98,304-token context (L32509,32516-32518). Its next request processes all
65,155 prompt tokens in 9,732.7 seconds—162.2 minutes—then generates 403
tokens in 299 seconds. The restart/cold-prefill sequence is the clearest
measured snowballing event.

## Recovery failure

Five compression attempts consume approximately 600 seconds each, roughly 50
minutes total. Three occur around 57K estimated request tokens; two occur at
74,817 after resume (A3515-3544,3733-3747). They use the same local model and
endpoint. Progress appears near the deadlines, so these are total-ceiling
failures, not proven dead streams or user cancellations. The telemetry label
`explicit_interrupt` must be interpreted with the adjacent 600-second host
ceiling.

Even recovery is slow: the two resumed attempts process 3,045-token prompts
in 246.14 and 273.42 seconds before generation (L40590,40714). None reduces
the conversation.

## Supported and unsupported conclusions

Observed facts include large tool/reasoning accumulation, CPU FFN placement,
cache-size rejection, KV-space warnings, eviction, context growth and backend
restart, cold-prefill cost, slower decoding, and failed compression.

The logs do not measure peak process RSS/commit, dedicated/shared VRAM during
the turn, OS paging, thermals, or the precise near-crash mechanism. Earlier
CUDA allocation failures precede this successful run and are not evidence
that a later OOM caused it. Constraints could reduce malformed calls or retry
accumulation; they cannot by themselves remove prompt prefill or KV memory.

This case therefore requires separate experiment axes for task/action quality
and context/resource control. Longer timeouts are not a remedy for work that
does not fit or for compression that fails to reduce history.

## Private evidence fingerprints

| Source at inspection | Bytes | SHA-256 |
|---|---:|---|
| `logs/agent.log` | 446,843 | `662dec2064d416e717d10a8740c4c9103634e130523d3b84c25e50fe30cea507` |
| `logs/llama-server.log` | 3,827,164 | `17e425b46cfb8fe60084bb45df132fc814818e14c5b74c310cc62fe179b5cd24` |
| `config.yaml` | 6,700 | `a48b4add7508261c13ddb54c66f9d5a4e9b3e62ada7f0520d34f4ccd3d848f1c` |
| `runtimes/llamacpp/presets.ini` | 580 | `bb35c72da07c0cfce2409ba22340d5bc1157821a03ac2788500f549253f8d0a1` |

Those mutable local files may rotate. The fingerprints identify the inspected
snapshot; future benchmarks need shareable, redacted receipts of their own.
