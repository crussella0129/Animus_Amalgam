# Amalgam lessons register

Each lesson has a stable ID, evidence, transfer boundary, and disposition.
Dispositions describe the current direction: **adopt**, **adapt**, **avoid**,
or **open question**.

| ID | Disposition | Lesson | Transfer boundary | Evidence |
|---|---|---|---|---|
| L-01 | adopt | Make the allowed action shape an executable server constraint when the endpoint is qualified. | Principle is language-independent; schema/token masking is backend-dependent. | [Ferric architecture](animus-ferric.md#architecture) |
| L-02 | adopt | Verify the outbound request and actual enforcement; unsupported constraints must be explicit failures. | HTTP inspection is general; format support varies by provider/build. | [Ferric failed direction](animus-ferric.md#failed-and-abandoned-directions) |
| L-03 | adapt | Map qualified capability to a bounded action/output policy deterministically. | Policy contract is general; Ferric tier/ring types are Rust-specific. | [Ferric architecture](animus-ferric.md#architecture) |
| L-04 | adopt | Measure structural validity, action selection, semantic arguments, execution, and independent task completion separately. | Language- and runtime-independent. | [Kinesin failures](kinesin.md#failures-and-superseded-claims), [Ferric recovery result](animus-ferric.md#failed-and-abandoned-directions) |
| L-05 | adopt | Keep authorization and evidence checking outside model-generated constraints or confidence. | Language-independent; reuse Hermes guards and approvals. | [Kinesin architecture](kinesin.md#architecture), [Hermes tool path](hermes-decoding-seams.md#existing-tool-call-path) |
| L-06 | avoid | Do not import a predecessor's full agent loop or duplicate Hermes tool execution. | Ferric/Kinesin crate graphs are implementation-specific. | [Ferric transfer](animus-ferric.md#transfer-to-amalgam), [Hermes endpoint seam](hermes-decoding-seams.md#smallest-existing-attachment-point) |
| L-07 | adopt | Bound context, output, retries, wall time, RAM/VRAM headroom, and recovery independently of grammar. | Resource contract is general; counters/limits are runtime-specific. | [Local session](local-session-case-study.md), [Kinesin resource bounds](kinesin.md#resource-bound-lessons) |
| L-08 | adapt | Preserve tool/result groups and checked evidence when compacting, using tokenizer-aware budgets. | Group invariant is general; Kinesin's 8 KiB/16-turn limits are not. | [Kinesin resource bounds](kinesin.md#resource-bound-lessons) |
| L-09 | adopt | Measure actual cache reuse on faithful sessions and report warm/cold paths separately. | General measurement rule; slots/templates/counters are backend-specific. | [Kinesin cache correction](kinesin.md#scoped-positive-observations), [local trajectory](local-session-case-study.md#measured-trajectory) |
| L-10 | adapt | Keep a conversation's rendered prefix and tool vocabulary stable; change policy metadata only after proving cache compatibility. | Hermes cache invariant is runtime-specific; measurement rule is general. | [Hermes cache invariants](hermes-decoding-seams.md#cache-and-session-invariants) |
| L-11 | avoid | Do not treat Ferric's evidence-bound recovery controller as a proven component. | Specific controller failed; honest negative evidence is general. | [Ferric abandoned intent](animus-ferric.md#failed-and-abandoned-directions) |
| L-12 | adopt | Preserve failed, skipped, and externally interrupted qualifications with their denominators and limits. | Language-independent. | [Ferric reported limits](animus-ferric.md#reported-successes-and-their-limits), [Kinesin diagnostics](kinesin.md#failures-and-superseded-claims) |
| L-13 | adapt | Prefer a cancellable out-of-process serving boundary for the first experiment. | Process boundary is runtime-specific; cancellation requirement is general. | [Ferric ADR-027](animus-ferric.md#failed-and-abandoned-directions), [Hermes decision boundary](hermes-decoding-seams.md#decision-boundary) |
| L-14 | open question | Build a new decoder only if controlled profiling finds an enforcement-coverage or mask-performance gap in existing engines. | Algorithm and tokenizer integration are engine-specific. | [Architecture recommendation](architecture-comparison.md#recommended-first-architecture) |

## Consequence for detailed intents

The first implementation intents must cite L-01 through L-14 as applicable,
state which backend-specific assumptions they qualify, and make L-04/L-07
metrics observable. The bounded evaluation protocol decides whether L-03's
adaptive policy improves on static constraints and whether L-14 advances.
