# INT-0006 — Conditional constraint-engine and decoder research

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0006
- **State:** proposed
- **Work evidence:** [T-205 in the backlog](../work/tasks.md)
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** [lesson L-14](../lineage/lessons-register.md#consequence-for-detailed-intents)

## Intent

Determine whether Amalgam needs a different constraint engine or a new
self-constraining decoder. This intent activates only after INT-0004/INT-0005
produce a reproducible existing-engine coverage or token-mask performance gap.
It does not authorize implementation of a decoder from scratch.

Scope includes existing llama.cpp/llguidance behavior, other engines that can
preserve the provider/service boundary, grammar-aligned decoding research, and
checked model-proposed constraints. It excludes agent-loop redesign, authority
delegation to generated grammars, and claims that an engine change fixes
context/prefill/resource problems outside token masking.

## Acceptance criteria

1. An activation receipt names the exact failed schema/task, model/tokenizer,
   engine/build, request, expected behavior, actual enforcement/coverage or
   mask-overhead result, and proves the gap remains after template, context,
   offload, cache, and server configuration are controlled.
2. A bounded comparison measures schema/grammar coverage, compile/startup
   cost, per-token mask overhead, end-to-end latency, output quality,
   cancellation, memory, and task outcomes on the same corpus. Existing
   engines are included before a new implementation is recommended.
3. Any model-proposed constraint path treats proposals as untrusted: trusted
   code checks syntax, satisfiability, tokenizer compatibility, size/compile
   budget, authority, and fallback behavior before enforcement.
4. The decision records one of: keep the existing engine; adopt an existing
   alternative; run a bounded algorithm prototype; or create a separate
   implementation intent for a new decoder. It preserves negative results and
   does not infer general quality from grammatical output.
5. A new-decoder implementation can be planned only in a new intent with a
   defined algorithm, integration boundary, threat model, benchmark/control,
   resource envelope, and removal/fallback story.

## Rationale

[L-14](../lineage/lessons-register.md) leaves a new decoder open because the
current evidence diagnoses context growth, cache eviction, prefill, generation,
and failed recovery but does not isolate a token-mask engine limitation.
Grammar-Aligned Decoding motivates measuring distribution/quality effects; it
does not establish a win on this model, hardware, or task corpus.

## Alternatives

- **Build a decoder immediately.** Rejected: existing llama.cpp/llguidance
  already exposes relevant enforcement, and no controlled gap is established.
- **Assume one JSON-valid smoke qualifies the engine.** Rejected: enforcement,
  coverage, semantic quality, cancellation, and resource cost are separate.
- **Use only a microbenchmark.** Rejected as the sole gate; end-to-end task and
  resource receipts are also required.
- **Never research another engine.** Rejected because a reproducible coverage
  or mask-performance gap may justify a different implementation.

## Consequences

- T-205 remains conditional and may close without a decoder project if no gap
  survives the controls.
- A model-generated grammar can narrow representation but can never create
  permission or certify task success.
- Any future decoder work is separately reviewable rather than hidden inside
  the provider integration.

## Transition history
- 2026-09-23: created as `proposed`; activation is gated by a reproducible L-14 engine gap.
