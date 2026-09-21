# Sprint 0 Research Report

## Intents Reviewed
- [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md): created. The Book and substrate are this sprint's only deliverable. Current state: proposed.
- [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md): created. It is not advanced this sprint; Sprint 1 carries it as backlog. Current state: proposed.
- [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md): created, deliberately coarse. The owner deferred writing the detailed intents to Sprint 1. Current state: proposed.

## 1. Sprint Goal
Set up Animus Amalgam's Project Book and the Sprint Loops infrastructure, and
nothing else. By the end of the sprint:

- the substrate is deployed and verified at bundle 0.22.0, the latest release
  (installed commit `0bdbe66` matches upstream `origin/main` after a fresh
  fetch);
- the Book's front matter explains what this fork is and why it exists;
- the fork's reason for existing is recorded as stable intent;
- Sprint 1's work (the Ferric/Kinesin lineage analysis and the detailed AACD
  intents) is queued as backlog tasks.

The owner scoped this sprint explicitly to setup because the weekly usage
limit is close. No analysis or code is in scope.

## 2. Existing Code Survey
| File | Relevance | Notes |
|------|-----------|-------|
| `README.md` | high | Upstream Hermes Agent (Nous Research) identity. It is upstream-owned, so the Book leaves it unchanged (INT-0001 Alternatives). |
| `.gitignore` | high | Convergence appended a delimited `sprint-loops` block. This is the only upstream-owned file the Book touches. |
| `.github/workflows/` | medium | 30 inherited upstream workflows. Convergence therefore generated no Sprint Loops CI, and `ci.yaml` triggers on `main`. |
| `website/` | medium | Upstream Docusaurus user docs. The Book stays out of it. |
| `docs/work/remote-profile.md` | high | `github`, `main` ← `dev`, `human-approve`. The provider was inferred from `origin`. |
| `agent/conversation_loop.py` | medium | Main agent loop. Located only; Sprint 1 will read it (T-104). |
| `model_tools.py` | medium | Tool schema and dispatch surface. Located only (T-104). |
| `agent/auxiliary_structured_output.py` | high | `response_format` capability for auxiliary requests only, plus a memo of routes that rejected a format. This is the closest existing structured-output mechanism. |
| `Animus_Ferric/README.md` | high | Rust harness for small GGUF models, pinned at `51af84e`. |
| `Animus_Ferric/docs/README.md` | high | The three convictions: the harness owns decoding, behavior scales to the model, the trajectory is the truth. |
| `Animus_Ferric/docs/introduction.md` | high | Thesis: a JSON grammar enforced by the server makes malformed tool calls impossible, which lowers the usable floor to 1B models. |
| `Animus_Ferric/docs/credits.md` | medium | llguidance is the grammar mechanism inside the server. |
| `Animus_Ferric/docs/intents/` | high | 9 intents, including INT-0001 (abandoned), which is a candidate failure lesson. |
| `Kinesin/README.md` | high | Rust harness with explicit authority and bounded resources, pinned at `a449121`. |
| `Kinesin/docs/loop-and-tools.md` | high | Tools or constraint per request, never both. A shape-only `response_format` checked answer, with a separate checker for semantics. |
| `Kinesin/docs/intents/` | high | 33 intents; several superseded (INT-0004, INT-0008, INT-0011, INT-0015). |

## 3. External Sources
- [Animus_Ferric](https://github.com/crussella0129/Animus_Ferric): predecessor harness and Book, source for INT-0002.
- [Kinesin](https://github.com/crussella0129/Kinesin): predecessor harness and Book, source for INT-0002.
- [Animus_Sprint_Loops](https://github.com/crussella0129/Animus_Sprint_Loops): the Sprint Loops bundle; its marketplace `origin/main` confirms 0.22.0 is the latest.
- [llguidance](https://github.com/guidance-ai/llguidance): Ferric's grammar-constrained decoding mechanism.
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent): the upstream project this repository forks.

## 4. Risks, Unknowns, Dependencies
- **Risk:** Upstream sync conflicts. If upstream adds a `docs/` tree, or edits `.gitignore` near the end of the file, syncs will conflict. The Book limits its footprint to `docs/` plus one delimited block (INT-0001 AC5), and backlog task T-106 defines a sync policy.
- **Risk:** The checkpoint pull request runs the full inherited upstream CI. Failures unrelated to a docs-only change, or checks aimed at upstream contributors, can show red. INT-0001 Consequences records this, and T-106 covers it.
- **Risk:** The repository is public, so Book content becomes public once the checkpoint branch is pushed. The Book contains only project-intent prose and no secrets.
- **Unknown:** What "Adaptive" means in AACD, and what AACD covers. INT-0003 records a working reading only; T-105 writes the detailed intents.
- **Unknown:** Which backends are in scope: local `llama-server` or GGUF only, or also hosted providers with structured-output modes. Deferred to T-105.
- **Dependency:** Sprint Loops bundle 0.22.0, verified as the latest.
- **Dependency:** Both predecessor repositories are active. The analysis pins commits `51af84e` and `a449121`.

## 5. Recommended Approach
Primary: Sprint 0 realizes INT-0001 only.

1. Write the Book's front matter: `docs/README.md` for project identity,
   purpose, authority order, and the boundary with upstream; an intent index in
   `docs/intents/README.md`; and navigation in `docs/SUMMARY.md`.
2. Record INT-0002 and INT-0003 as `proposed`, and queue Sprint 1's analysis
   and intent-writing work as `(backlog)` tasks linked to them.
3. Verify with `check-substrate.sh`, `check-book.sh`, a check that every
   relative link resolves, and a diff scoped against `main`.
4. Close the sprint and open the single `dev → main` checkpoint.

Alternative considered: starting the lineage analysis (INT-0002) this sprint.

Rationale: the owner explicitly limited Sprint 0 to setup because the weekly
usage limit is close. Queuing the analysis as backlog with pinned sources keeps
Sprint 1 cheap to start without spending this sprint's budget on it.

## Artifacts
- (none saved; the reference pins are recorded in INT-0002's Sources table)
