# INT-0005 — Adaptive action policy at the Hermes provider boundary

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0005
- **State:** proposed
- **Work evidence:** [T-203 and T-204 in the backlog](../work/tasks.md)
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** [architecture comparison](../lineage/architecture-comparison.md), [lessons register](../lineage/lessons-register.md)

## Intent

Add and qualify an Animus adaptive action policy through Hermes's existing
custom endpoint/provider boundary after INT-0004 establishes the bounded
native/static control.

**Adaptive** means a deterministic, logged function maps qualified
model/backend capabilities, trusted task state, independently checked
outcomes, and remaining resource budget to the next permitted action language
and output budget. Equal inputs produce equal policy decisions. Adaptation
cannot enlarge user authority, accept the model's confidence as evidence, or
silently discard a promised constraint.

Initial scope is a local llama.cpp-compatible endpoint. A narrow Rust
policy/protocol service is the leading candidate because it can reuse Ferric's
language-independent policy ideas without importing its loop. An out-of-tree
Hermes provider plugin is added only for a demonstrated setup, capability, or
per-session metadata gap in the custom-provider path.

Non-goals:

- no new core model tool, second conversation loop, or second tool executor;
- no dynamic mutation of system text, historical messages, or the tool catalog
  inside a cached conversation;
- no semantic/task-success claim from schema validity alone;
- no hosted-provider promise beyond explicitly qualified structured-output
  capabilities;
- no new token-mask engine under this intent.

## Acceptance criteria

1. INT-0004 has a passing bounded control or an explicit result showing which
   safe smaller workload/model is usable; the adaptive experiment uses that
   same manifest and task corpus.
2. A versioned policy contract enumerates trusted inputs, decisions, state
   transitions, resource/authority monotonicity, and stable reason codes. Unit
   cases prove determinism and that model/tool content cannot enlarge authority.
3. The integration returns ordinary Hermes responses and leaves conversation,
   tool validation, authorization, execution, and completion evidence in
   Hermes. Unsupported/unsatisfiable/over-budget constraints fail explicitly.
4. Rendered system/history/tool bytes remain stable within a conversation.
   Actual prefix hashes and cached-token receipts prove whether adaptive
   metadata preserves backend reuse; otherwise adaptation occurs only at a new
   session or explicit compaction boundary.
5. Static and adaptive arms run as paired repetitions with context/resource
   policy fixed. Reports separate shape validity, tool choice, semantic
   arguments, execution, independent completion, retries, latency, context,
   cache, memory, cancellation, and host responsiveness.
6. Adaptive policy advances only if it improves on the static arm without
   weaker authority, hidden retries, cache-prefix churn, or stop-gate breaches.
   Inconclusive evidence retains the static implementation.
7. If a plugin/service holds state, real imports under temporary Hermes homes
   prove A-to-B-to-A profile isolation and session-keyed teardown. Applicable
   Python validation runs through `scripts/run_tests.sh`.

## Rationale

Lessons
[L-01 through L-06, L-10, L-11, and L-13](../lineage/lessons-register.md)
support qualified server enforcement, deterministic bounded policy, separate
semantic/authority checks, reuse of Hermes's loop/executor, rejection of the
failed recovery controller as a proven component, a stable cached prefix, and
an out-of-process first boundary. Hermes already provides the narrow
integration and execution waist.

## Alternatives

- **Static constraints only.** Retained as the control and selected result if
  adaptation provides no repeatable benefit.
- **Change tool rings or prompt instructions every turn.** Rejected within a
  conversation because it breaks Hermes's cached-prefix invariant. New-session
  or compaction-boundary changes remain possible if measured.
- **Let the model create or relax its own grammar.** Rejected as authority.
  Model-proposed constraints may be untrusted candidates only after schema,
  satisfiability, size/compile-budget, and authority checks.
- **Implement directly in Hermes core.** Rejected unless a future generic
  requirement cannot use the existing endpoint, middleware, plugin, or client
  seams.
- **Port Ferric's complete loop.** Rejected because it duplicates Hermes
  conversation and execution ownership and carries Rust-specific coupling.
  Ferric's L-11 recovery controller is also preserved as negative evidence,
  not imported as a qualified component.

## Consequences

- Policy behavior and reason codes become durable experimental artifacts.
- Cache compatibility is a backend qualification claim, not inferred from
  stable Python objects.
- A simpler static result is a successful outcome when adaptation fails its
  marginal-benefit gate.

## Transition history
- 2026-09-23: created as `proposed` from Sprint 1 lessons L-01 through L-05, L-10, and L-13.
- 2026-09-23: Sprint 1 test review made L-06's reuse of the Hermes
  loop/executor and L-11's negative recovery-controller evidence explicit;
  state remains `proposed`.
