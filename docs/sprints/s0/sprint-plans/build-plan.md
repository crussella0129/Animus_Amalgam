# Sprint 0 Build Plan

## Intents
- [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md): state planned.
  - AC3 and AC4 are covered by T-001 and T-002.
  - AC1 (substrate) was met at init by `deploy-substrate.sh` in commit `84a5005b2c`. It has no build task and the Test phase verifies it.
  - AC2 (validator, SUMMARY reachability, link resolution) and AC5 (diff scope) constrain every task. The Test phase verifies both.
- [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) and [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) are not advanced; both stay `proposed`. T-002 only adds backlog links to their Work evidence, so this sprint makes no change to what they mean.

## Schema Tree
- Sprint Goal: stand up the Project Book and Sprint Loops substrate, and queue Sprint 1
  - Book front matter
    - T-001: `docs/README.md` covers project identity, purpose, authority order and the upstream boundary; `docs/intents/README.md` becomes the intent index
  - Carry-forward work
    - T-002: queue backlog tasks T-101 to T-106 and link each from its intent's Work evidence

## Execution Sequence

### T-001: Write the Book front matter (project identity, purpose, authority order, upstream boundary, intent index)
- **Intent:** [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)
- **Touches:** `docs/README.md`, `docs/intents/README.md`, `docs/intents/INT-0001-project-book-and-sprint-substrate.md` (the `planned` → `active` transition at Build start)
- **Depends on:** (none)
- **Acceptance criterion:** INT-0001 AC3: `docs/README.md` states four things. The project is a fork of Hermes Agent. The fork exists to apply AACD lessons from Animus_Ferric and Kinesin. The Book has an authority order. The Book ends where upstream documentation begins.
- **Success criterion (EARS):**
  - **WHEN** `docs/README.md` is read, **THEN** it **SHALL** name "Hermes Agent" and contain a link to `https://github.com/NousResearch/hermes-agent`.
  - **WHEN** `docs/README.md` is read, **THEN** it **SHALL** contain "Adaptive Constrained Decoding", "Animus_Ferric" and "Kinesin", and **SHALL** link `intents/INT-0002-…` and `intents/INT-0003-…`.
  - **WHEN** `docs/README.md` is read, **THEN** it **SHALL** state the authority order with intents first, then work ledgers, then sprint records, then `SUMMARY.md` as navigation only.
  - **WHEN** `docs/README.md` is read, **THEN** its `## Where the Book ends` section **SHALL** name `website/` and the upstream-owned root files (`README.md`, `AGENTS.md`) as outside the Book.
  - **WHEN** `docs/intents/README.md` is read, **THEN** it **SHALL** link every `docs/intents/INT-*.md` file, and **SHALL NOT** link an intent path that does not exist.
- **Notes:**
  - The index lists each chapter's ID and title only. It states that lifecycle state lives in each chapter, so the index cannot drift from the chapters.
  - Keep the substrate's opening sentence about the canonical Book.

### T-002: Queue the Sprint 1 backlog (T-101 to T-106) and link each task from its intent's Work evidence
- **Intent:** [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)
- **Touches:**
  - `docs/work/tasks.md`
  - `docs/intents/INT-0001-project-book-and-sprint-substrate.md`
  - `docs/intents/INT-0002-lineage-lessons-ferric-kinesin.md`
  - `docs/intents/INT-0003-animus-adaptive-constrained-decoding.md`
- **Depends on:** (none). The paths and intents are disjoint from T-001, and both tasks run in plan order.
- **Acceptance criterion:** INT-0001 AC4: work planned beyond this sprint is queued as `(backlog)` tasks. Each task names an intent, and that intent's Work evidence links it.
- **Success criterion (EARS):**
  - **WHEN** `docs/work/tasks.md` is parsed, **THEN** every backlog line **SHALL** match `^- \[ \] T-[0-9]+ \(backlog\) \[intent: INT-[0-9]{4}(, INT-[0-9]{4})*\]: .+ — touches: .+$`, and the backlog **SHALL** contain exactly T-101, T-102, T-103, T-104, T-105 and T-106.
  - **WHEN** a backlog task names an intent `INT-X`, **THEN** INT-X's `Work evidence` field **SHALL** contain a Markdown link whose label contains that task ID.
  - **WHEN** Build completes, **THEN** `docs/work/tasks.md` **SHALL** contain no `(sprint 0)` entry.
- **Notes:** The backlog descriptions are:
  - T-101: Ferric analysis at `51af84e`, written to `docs/lineage/animus-ferric.md`.
  - T-102: Kinesin analysis at `a449121`, written to `docs/lineage/kinesin.md`.
  - T-103: the comparative architecture chapter and lessons register.
  - T-104: a survey of Hermes' decoding and tool-call integration points.
  - T-105: the detailed AACD intents, written with the owner.
  - T-106: an upstream sync policy and CI expectations for checkpoints.

  No backlog description may contain the literal `(sprint 0)`. Linking a
  `proposed` intent's Work evidence to backlog tasks does not change its state.
