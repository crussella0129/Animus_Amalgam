# INT-0003 — Animus Adaptive Constrained Decoding in Amalgam

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0003
- **State:** active
- **Work evidence:** [Sprint 1 tasks T-104, T-105, T-107, and T-108](../sprints/s1/sprint-plans/build-plan.md#execution-sequence)
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** none

## Intent

Amalgam brings Animus Adaptive Constrained Decoding (AACD) to Hermes Agent.
This is the main reason the fork exists.

The owner's 2026-09-23 direction makes small local models on an RTX 2080 Ti
and 32 GB of system RAM the initial research target. The fork is a working
surface, not a requirement to maintain a separate full agent: an existing
Hermes custom endpoint, a provider plugin, or a Rust service informed by
Ferric are all candidates. Reusing an established constraint engine and
researching an automatically adapting decoder must be compared on evidence.
No particular integration or decoder has been selected.

Long-session viability is part of the desired outcome. The reported Qwen
session's prompt growth, request latency, cache behavior, compression failures,
and resource limits must inform the design. A syntactically valid tool call
does not by itself demonstrate task success or affordable execution.

**This chapter is deliberately coarse.** The project owner deferred writing
the detailed intents to Sprint 1. This chapter's boundaries and acceptance
criteria will be replaced after the lessons register from
[INT-0002](INT-0002-lineage-lessons-ferric-kinesin.md) exists, and the chapter
may be split into follow-on intents at that point. Sprint 1 plans that
research and intent decomposition; no implementation work may be planned
directly against these provisional criteria.

Working reading, to be confirmed or replaced by the owner: the harness, not
the model, decides which well-formed actions the model is able to emit. The
harness also adapts how tightly it constrains output to the capability of the
model and backend in use. This reading comes from Ferric's stated principles
("the harness owns decoding" and "behavior scales to the model,
deterministically"). It is not yet a decision.

Starting points recorded in the Sprint 0 survey. These are observations, not
decisions:

- Hermes Agent's main loop (`agent/conversation_loop.py`, `model_tools.py`)
  uses each provider's native tool calling. `response_format` structured output
  is used only for auxiliary requests. For those, Hermes remembers each
  (endpoint, model, type) combination that rejected a format and drops the
  field on later requests (`agent/auxiliary_structured_output.py`).
- Animus_Ferric enforces a JSON-Schema grammar owned by the harness from end
  to end, and maps each model profile to a run policy deterministically.
- Kinesin sends either tools or a constraint on a request, never both. Its
  schema constrains shape only, and a separate checker owns semantic validity.

## Acceptance criteria

These criteria are provisional and will be replaced when the detailed intents
are written:

1. Before any AACD implementation is planned, this chapter, or the follow-on
   chapters that supersede it, states observable acceptance criteria grounded
   in INT-0002's lessons register. Those criteria define which backends and
   providers are in scope and what the non-goals are.
2. This chapter records a definition of "adaptive", with its rationale and the
   alternatives that were rejected.
3. Architecture selection distinguishes policy adaptation, token-mask
   enforcement, semantic checking, and resource control; it evaluates an
   existing Hermes endpoint/provider seam before adding core surface.
4. The research identifies the supplied local session, separates observed
   events from unmeasured causes, and specifies a bounded comparison of
   ordinary local Hermes, static constraints, and adaptive constraints on
   the stated hardware. Any later implementation acceptance must include
   task correctness, latency, context growth, and memory headroom.

## Rationale

The project owner stated that the fork exists to use the lessons learned in
Animus_Ferric and Kinesin about Animus Adaptive Constrained Decoding.

## Alternatives

None have been evaluated yet. They will be recorded once INT-0002's analysis
exists.

## Consequences

- Hermes Agent supports many hosted providers whose decoding the harness
  cannot control beyond whatever structured-output modes each one offers. How
  far AACD can reach across providers is an open question that the detailed
  intents must settle.
- Both predecessors were validated mainly against local `llama-server` with
  GGUF models. Behavior on other backends has not been demonstrated.

## Transition history
- 2026-09-21: created as `proposed` (Sprint 0 research).
- 2026-09-23: revised the research boundaries from the owner's Sprint 1
  request: provider/service alternatives, the 2080 Ti / 32 GB target, and
  long-session resource behavior. State remains `proposed`; implementation
  criteria and architecture selection still require the lineage analysis.
- 2026-09-23: moved to `planned` after the owner approved the Sprint 1
  research, evaluation-protocol, and detailed-intent work. This transition
  does not authorize decoder implementation against the provisional criteria.
- 2026-09-23: moved to `active` when T-104 began the Hermes integration
  chapter. Implementation remains outside Sprint 1.
