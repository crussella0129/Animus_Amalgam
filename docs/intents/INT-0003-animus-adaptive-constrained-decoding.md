# INT-0003 — Animus Adaptive Constrained Decoding in Amalgam

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0003
- **State:** proposed
- **Work evidence:** none
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** none

## Intent

Amalgam brings Animus Adaptive Constrained Decoding (AACD) to Hermes Agent.
This is the main reason the fork exists.

**This chapter is deliberately coarse.** The project owner deferred writing
the detailed intents to Sprint 1. This chapter's boundaries and acceptance
criteria will be written after the lessons register from
[INT-0002](INT-0002-lineage-lessons-ferric-kinesin.md) exists, and the chapter
may be split into follow-on intents at that point. Until then it stays
`proposed`, and no sprint may plan implementation work against it directly.

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
