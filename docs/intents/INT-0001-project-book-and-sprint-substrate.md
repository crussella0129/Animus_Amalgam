# INT-0001 — Project Book and Sprint Loops substrate

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0001
- **State:** planned
- **Work evidence:** [T-001 and T-002 in the Sprint 0 build plan](../sprints/s0/sprint-plans/build-plan.md)
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** none

## Intent

Animus Amalgam keeps a tracked Sprint Loops Book (schema v2, substrate
contract 4) under `docs/`. It is the only writable engineering record for work
specific to this fork: why the fork exists, what it intends, what has been
done, and how each claim was verified. Someone new to the project, whether a
person or an agent, can get oriented from `docs/README.md` alone.

Boundaries:

- The Book records Amalgam's fork-specific intent and work. It does not
  document upstream Hermes Agent features. Upstream user documentation stays in
  `website/` (Docusaurus), and upstream-owned root files such as `README.md`,
  `AGENTS.md`, and `CONTRIBUTING.md` are left as upstream ships them.
- The Book adds files only under `docs/`. The one upstream-owned file it
  touches is the delimited `sprint-loops` block that convergence appends to
  `.gitignore`.
- Branch topology follows [the remote profile](../work/remote-profile.md):
  sprints commit to `dev`, and each sprint opens one `dev → main` pull request
  that a person approves.

Non-goals: rendering the Book as a website (mdBook or Docusaurus), rewriting
upstream documentation, and any constrained-decoding design content. That
content belongs to [INT-0002](INT-0002-lineage-lessons-ferric-kinesin.md) and
[INT-0003](INT-0003-animus-adaptive-constrained-decoding.md).

## Acceptance criteria

1. The installed `check-substrate.sh` reports `substrate-complete`.
   `docs/.sprint-loop-book` declares `schema-version: 2` and
   `substrate-version: 4`. `docs/work/remote-profile.md` resolves to provider
   `github`, base `main`, work `dev`, and mergePolicy `human-approve`.
2. The installed `check-book.sh` passes, every intent chapter is linked from
   `docs/SUMMARY.md`, and every relative Markdown link under `docs/` resolves
   to an existing file.
3. `docs/README.md` states four things: that the project is a fork of Hermes
   Agent; why the fork exists (applying Animus Adaptive Constrained Decoding
   lessons from Animus_Ferric and Kinesin); the Book's authority order; and
   where the Book ends and upstream documentation begins.
4. Work planned beyond the current sprint is queued in `docs/work/tasks.md` as
   `(backlog)` tasks. Each task names an intent, and that intent's Work
   evidence links the task.
5. Compared with the fork point on `main`, the sprint's diff touches only
   `docs/**` and the `sprint-loops` block in `.gitignore`.

## Rationale

The fork exists to carry lessons over from two sibling projects, and both keep
Sprint Loops Books: Animus_Ferric has 9 intent chapters and 93 sprint records,
and Kinesin has 33 intent chapters and 17 sprint records. Keeping Amalgam's
records under the same Book contract means their evidence can be cited
directly, and Amalgam's own decisions stay traceable in the same form.
Upstream Hermes Agent has no `docs/` directory at the fork point, so the Book
can live there without colliding with upstream files.

## Alternatives

- **Put the records in `website/docs/`.** Rejected. That tree is upstream's
  user documentation and is merged from upstream. Mixing fork records into it
  would maximize merge conflicts and publish engineering records on the user
  documentation site.
- **Add a root `ANIMUS.md` or edit the root `README.md`.** Rejected. Root
  files belong to upstream and change often there, so editing them would turn
  every upstream sync into a conflict.
- **Keep the Book in a separate repository.** Rejected. Intent evidence has to
  link to code and commits in this repository.

## Consequences

- The root `README.md` still presents upstream Hermes Agent, so a visitor
  landing on the repository sees nothing about Amalgam's purpose until they
  open `docs/`. This is accepted to keep upstream syncs cheap, and should be
  revisited if the fork diverges materially.
- If upstream ever adds its own `docs/` directory, syncs will need a
  path-level conflict review.
- Every `dev → main` checkpoint pull request runs the fork's inherited
  upstream CI. Convergence generated no Sprint Loops CI because
  `.github/workflows/` was already populated.
- There is no policy yet for how `NousResearch/hermes-agent` changes enter
  `main` and then `dev`. That work is queued as backlog.

## Transition history
- 2026-09-21: created as `proposed` (Sprint 0 research).
- 2026-09-21: `proposed` → `planned`. The owner approved the Sprint 0 plan, and T-001 and T-002 are scheduled.
