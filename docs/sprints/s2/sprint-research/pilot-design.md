# Sprint 2 pilot design inputs

This is research provenance for the draft plan, not an approved run manifest.
The stable authority is [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md).

## Owner choices

On 2026-09-23 the owner selected “Existing Qwen3.8-27B first” and “300
seconds” for one small request including prompt processing. The owner then
explained that some historical waits exceeded five minutes and the installed
Hermes configuration therefore used a three-hour maximum. Preserve that
configuration. Use the 300-second answer as this pilot's deadline, without
generalizing it to every useful workload.

## Proposed envelope

- Existing hashed 27B model, installed b10964 CUDA server, isolated custom
  endpoint and fresh Hermes home/process; managed local runtime disabled.
- Fixed 8,192-token context, one slot, no draft/MTP, no automatic fit or
  context growth, q8_0 K/V, flash attention explicitly enabled.
- Input ceiling 4,096 tokens including fully rendered instructions/template;
  output ceiling 128 including reasoning. Record prompt bytes/token IDs and
  prefix hash; fail admission if the real prefix cannot fit.
- Explicit batch/ubatch 256/128, six CPU threads, prompt-cache RAM disabled
  for the smoke. Exact GPU-layer placement must be frozen from tensor-size
  accounting before launch; no live auto-fit or parameter search.
- Load deadline 300 seconds; request deadline 300 seconds; at most three live
  requests (smoke, main cancellation, compression cancellation). At most three
  owned launches and 30 minutes total live gate time, including loads and
  cleanup. Cancellation tests deliberately stop within the request deadline.
- Reserve at least 4 GiB system RAM and 1 GiB dedicated VRAM before/during
  load and requests. Admit only resident-weight capacity plus explicit KV and
  scratch allowances on each device; aggregate capacity alone is insufficient.
- Sample critical headroom and process/scheduler health from an independent
  supervisor. Stale/missing critical telemetry fails closed. Explicit numeric
  paging and scheduler-lag thresholds belong in the finalized manifest.
- Stop at the first breach. No model fallback, context increase, retries of a
  rejected load/request, closing unrelated apps, or live configuration edits.

## Evidence contract

Offline deterministic fixtures first prove that the actual main and
compression requests use the isolated endpoint, stable prompt/tool bytes,
128-token budget, one physical request and bounded retries. Then prove the
supervisor can kill an owned stalled process tree, release its port and
leave an unrelated sentinel alive. Cancellation must work with a blocked
driver and telemetry collector, not depend on the model returning a token.

For live evidence, record request/slot IDs, server model/context, request
shape, rendered input count/hash, usage, prompt/decode/total time, meaningful
first token, cache observations, RAM/VRAM/paging, stop reason and idle/exit
confirmation. Use explicit `unavailable` entries for optional missing metrics.
An unavailable critical stop signal prevents launch.

A normal smoke asks for a fixed, independently checked short answer with no
tools. Main and compression cancellation use synthetic input; compression
must traverse the real helper/observer path, not just a second generic HTTP
call. A no-tool pilot demonstrates a transport/resource boundary only.

If admission fails, publish the full manifest and resource comparison as
`not-run: resource gate`, with live subchecks explicitly not run. T-201 can
finish as a gate implementation and measured rejection; INT-0004 remains
unqualified and T-202 remains queued. A rejected attempt has no completion
rate and is not evidence of bad model quality.
