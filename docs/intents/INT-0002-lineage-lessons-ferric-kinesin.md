# INT-0002 — Lineage lessons from Animus_Ferric and Kinesin

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0002
- **State:** proposed
- **Work evidence:** none
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** none

## Intent

The Book holds a cited, commit-pinned analysis of Amalgam's two predecessor
harnesses, [Animus_Ferric](https://github.com/crussella0129/Animus_Ferric) and
[Kinesin](https://github.com/crussella0129/Kinesin). The analysis covers three
things for each:

1. documented successes;
2. documented failures and abandoned directions;
3. the architecture: how it implements constrained decoding and the control
   loop around it.

The purpose is to ground Amalgam's Animus Adaptive Constrained Decoding
intents ([INT-0003](INT-0003-animus-adaptive-constrained-decoding.md)) in
evidence rather than recollection.

Boundaries:

- This is analysis only. No code is ported under this intent.
- Every claim cites the predecessor's own Book (intent chapters, sprint
  records, failure reports, decisions) or its source, at a pinned commit.
- Both predecessors are written in Rust, while Amalgam inherits Hermes
  Agent's Python codebase. The analysis says which lessons hold regardless of
  language and runtime, and which depended on something specific to Rust or
  to the backend.

Sources pinned at the Sprint 0 survey:

| Repository | Commit | Survey-level summary |
|---|---|---|
| Animus_Ferric | `51af84e` (2026-09-08) | Rust coding harness for 1B–14B GGUF models. Its first stated principle is "the harness owns decoding": JSON-Schema grammars are enforced by the server (llguidance inside `llama-server`), so a malformed tool call cannot be produced at all rather than being repaired afterward. A pure function maps each model profile to a run policy, and tool rings widen as a model proves it can use them. 9 intents (one abandoned), 93 sprint records, and a legacy decisions log. |
| Kinesin | `a449121` (2026-09-20) | Rust agent harness with explicit authority and bounded resources. Each request carries tools or a constraint, never both. Tool calls use the grammar `llama-server` derives from the chat template. A checked prose answer is requested again with tools withdrawn and a `response_format` JSON Schema, which constrains shape only; a separate checker decides semantic validity. 33 intents (several superseded), 17 sprint records. |

## Acceptance criteria

1. The Book has a chapter for each predecessor recording its successes,
   failures, and abandoned or superseded intents. Every claim links to a
   source file in that repository at the pinned commit.
2. A comparative architecture chapter contrasts Ferric, Kinesin, and Hermes
   Agent's current decoding and tool-call path on at least these points: where
   the constraint is enforced; what it guarantees (shape versus semantics); how
   it adapts to model capability; how failures are handled; and what it
   depends on from the backend.
3. The analysis ends with a lessons register. Each lesson has a stable ID,
   evidence links, and a disposition for Amalgam: adopt, adapt, avoid, or open
   question.
4. When INT-0003's detailed acceptance criteria are written, they cite the
   lessons register.

## Rationale

The project owner has said that applying these two projects' lessons on
Animus Adaptive Constrained Decoding is a main reason this fork exists. They
asked for the documented successes, the failures, and an analysis of the
architectures themselves. Both predecessors keep Sprint Loops Books, so the
evidence already exists in a form that can be cited. Pinning commits keeps
the analysis reproducible while both repositories keep changing.

## Alternatives

- **Recall lessons informally in each future sprint's research.** Rejected.
  Failures get lost that way, and nothing can be cited or checked later.
- **Port Ferric crates or Kinesin modules directly.** Rejected for now. The
  languages differ, and choosing what to port before the analysis would repeat
  whatever the predecessors got wrong.

## Consequences

- At least one sprint of analysis comes before any constrained-decoding code.
- The pinned commits will go out of date. Every register entry has to name
  the commit it was drawn from.

## Transition history
- 2026-09-21: created as `proposed` (Sprint 0 research).
