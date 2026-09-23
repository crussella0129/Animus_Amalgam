# Ferric, Kinesin, and Hermes architecture comparison

This comparison synthesizes the pinned predecessor chapters and Amalgam's
current Hermes source. It separates policy adaptation from token enforcement,
semantic checking, execution authority, and context/resource control.

## Control boundaries

| Dimension | Animus_Ferric | Kinesin | Hermes / Amalgam implication |
|---|---|---|---|
| Action vocabulary | `ferric-loop` builds one ordered action-schema branch per allowed tool; core/tool policy selects a tier and ring. | A request carries native tools or a response constraint, never both. | Existing tool definitions remain canonical; an adapter derives constraints without creating another executor. |
| Enforcement | External server receives JSON Schema or grammar metadata. | llama.cpp derives native tool grammar from the chat template; checked answers use response format. | The serving backend owns token masks. Qualify the actual endpoint/build/template rather than trusting a capability declaration. |
| Guarantee | Representable action shape only. | Native call or checked-answer shape only. | Hermes validation/guards/permissions remain authoritative; grammar cannot establish correct tool choice, arguments, or completion. |
| Adaptation | Deterministic model profile maps to budgets and action ring. No logits or online learner in `ferric-core`. | Explicit authority/resource policy and separate request modes; no evidence that shape alone changes premature-answer behavior. | Candidate AACD policy maps qualified capability, trusted task state, checked outcomes, and remaining budget to a permitted next action language. |
| Failure handling | Guards/traces preserve evidence; abandoned recovery controller still scored 0/3. Provider regex constraint can be silently unenforced. | Checker owns semantics; Sprint 16 valid answers did no work. | Unsupported enforcement and failed checking become explicit results. Bounded retries cannot erase a negative trial. |
| Backend dependency | JSON-Schema/grammar coverage, tokenizer/template, server cancellation, and HTTP response protocol. | Template tool grammar, response-format coverage, cache accounting, and transport. | Begin with a fixed external llama.cpp endpoint. Measure rendered prefix, enforcement, cancellation, cache, and timings. |
| Cache/context cost | Compaction uses the model; reported constrained successes do not qualify long context. | Bounded reference bytes/turns and group-preserving compaction, but bytes are not model tokens. | Preserve Hermes's cached prefix. Test resource policy independently of constraints; managed growth currently precedes compression. |

Evidence: [Ferric lineage](animus-ferric.md), [Kinesin lineage](kinesin.md),
[Hermes seams](hermes-decoding-seams.md), and the
[local-session case](local-session-case-study.md).

## Shape, meaning, and authority

All three architectures need four distinct decisions:

1. **Policy:** which actions and output budget are permitted for this trusted
   state and qualified model/backend.
2. **Enforcement:** which tokens can express that permitted language.
3. **Meaning:** whether the chosen action and arguments can satisfy the task.
4. **Authority and evidence:** whether execution is allowed and whether the
   observed result proves completion.

Ferric is strongest on deterministic action-shape construction, but its
abandoned controller shows that more evidence/guards need not create recovery.
Kinesin makes the shape/meaning distinction explicit, but its diagnostic runs
show that a valid final answer can replace the required action. Hermes already
owns authority, tool execution, validation, and conversation state. Amalgam
should add policy/enforcement at its provider boundary and preserve those
existing responsibilities.

## Adaptation and cache safety

The candidate definition of adaptive is a deterministic and logged function:

`qualified capability + trusted task state + checked outcomes + remaining budget → next permitted action language and output budget`

The same inputs must yield the same decision; model confidence cannot enlarge
authority. Model-proposed constraints are untrusted data and require syntax,
satisfiability, size/compile-budget, and authority checks.

Ferric's dynamic ring idea transfers as policy, but changing Hermes's tool
catalog or system prompt within a conversation would violate its cache
contract. The preferred experiment keeps rendered system/history/tool bytes
fixed and changes only backend metadata proven not to alter prompt tokens or
cache residency. If the backend cannot demonstrate that invariant, adaptation
occurs at a new session or compaction boundary.

## Resource control is orthogonal

The local case records both long generation with high cache reuse and later
cold-prefill cliffs after cache pressure and a managed restart. Constrained
decoding may improve action validity and reduce some retries, but it does not
remove KV memory, prompt prefill, large tool results, preserved reasoning, or
failed compression. The evaluation therefore holds context policy fixed while
comparing native/static/adaptive action policy, then tests context/compaction
as a separate axis.

## Transferability

Language/runtime-independent mechanisms:

- deterministic capability-to-policy mapping;
- server-enforced structural constraints;
- separate semantic and independent completion checks;
- bounded retries, context, output, and resource use;
- group-preserving compaction and durable negative evidence;
- cache verification on real session construction.

Rust-specific mechanisms include Ferric/Kinesin crate layouts, ownership
types, and their concrete policy/checker implementations. Runtime-specific
mechanisms include in-process inference APIs and cancellation. Backend-
specific mechanisms include schema coverage, tokenizer/template behavior,
tool-call syntax, cache slots, and timing/resource fields. Amalgam should
reimplement the language-independent contracts through Hermes interfaces and
qualify backend-dependent behavior with real requests.

## Recommended first architecture

Use Hermes's existing custom OpenAI-compatible endpoint as the control. Add a
narrow Rust policy/protocol service only if it supplies a measured missing
capability: it accepts the stable Hermes request/tools, derives a checked
constraint and resource policy, calls a qualified llama.cpp server, and
returns ordinary Hermes responses. An out-of-tree provider plugin may own
setup/capability metadata when static custom-provider configuration is
insufficient.

An in-process client or new token-mask engine remains conditional on a
profiled engine/coverage gap. Neither predecessor evidence nor the local
snowballing trace demonstrates that writing a new decoder is the first fix.
