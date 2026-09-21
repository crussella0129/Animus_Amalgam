# Project Book

This directory is the canonical Sprint Loops Book: project intent, executable
work, realization evidence, and sprint provenance live here together.

## What Animus Amalgam is

Animus Amalgam is a fork of **Hermes Agent**, the self-improving agent from Nous
Research ([NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)).
The code outside `docs/` is Hermes Agent as upstream ships it, plus whatever
this Book records as deliberately changed.

## Why the fork exists

The main reason for the fork is to bring **Animus Adaptive Constrained
Decoding** (AACD) to Hermes Agent, using lessons from the two earlier Animus
harnesses. Both are written in Rust and both keep their own Sprint Loops Book:

- [Animus_Ferric](https://github.com/crussella0129/Animus_Ferric) is a coding
  harness for small local GGUF models. Its central idea is that *the harness
  owns decoding*: server-enforced grammars make malformed tool calls
  impossible rather than repairable.
- [Kinesin](https://github.com/crussella0129/Kinesin) is an agent harness with
  explicit authority and bounded resources. Each request carries either tools
  or a constraint, never both, and its schemas constrain shape only while a
  checker owns meaning.

The lessons are the successes each project documented, its failures and
abandoned directions, and an analysis of both architectures. Two intents
cover them:

- [INT-0002 — Lineage lessons from Animus_Ferric and Kinesin](intents/INT-0002-lineage-lessons-ferric-kinesin.md)
  covers the analysis.
- [INT-0003 — Animus Adaptive Constrained Decoding in Amalgam](intents/INT-0003-animus-adaptive-constrained-decoding.md)
  covers what Amalgam will build. Its detailed intents will be written after
  that analysis.

## How the Book is organized

Authority runs in one direction. When two surfaces disagree, the higher one
wins, and the lower one is repaired or the higher one is revised explicitly:

1. **Intents** (`intents/INT-NNNN-*.md`) are the semantic authority: desired
   outcomes, boundaries, acceptance criteria, rationale, and lifecycle state.
   Start at the [intent index](intents/README.md).
2. **Work ledgers** (`work/`) are execution state: [queued tasks](work/tasks.md)
   and [completed tasks](work/completed-tasks.md), each linked to an intent.
   The [remote profile](work/remote-profile.md) declares the branch topology.
3. **Sprint records** (`sprints/sN/`) are provenance: research, locked plans,
   critiques, test evidence, and close metadata for each sprint.
4. **[SUMMARY.md](SUMMARY.md)** is navigation only and never carries state.

## Where the Book ends

The Book records only what is specific to Amalgam. Upstream material stays
upstream's, and the Book leaves it unchanged so that syncing from Hermes Agent
stays cheap:

- `website/` is upstream's user documentation (Docusaurus). Fork records do
  not go there.
- Root files such as `README.md`, `AGENTS.md`, and `CONTRIBUTING.md` are owned
  by upstream and are outside the Book.
- The Book adds files only under `docs/`. The one upstream-owned file it
  touches is the delimited `sprint-loops` block in `.gitignore`.

The reasons behind this boundary are recorded in
[INT-0001](intents/INT-0001-project-book-and-sprint-substrate.md).

## Working on this project

Work happens in Sprint Loops sprints: Research → Plan → Build → Test → Loop.
To pick up wherever the Book says the project stands, run
`/sprint-loop continue`. Sprints commit to `dev`. Each sprint ends by opening
one `dev → main` pull request, and a person approves the merge. The workflow
never creates per-sprint branches.
