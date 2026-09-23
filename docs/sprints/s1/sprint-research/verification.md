# Research verification receipt

2026-09-23. Scope is the research artifacts, not runtime implementation.

- `check-substrate.sh`: substrate-complete.
- `check-book.sh`: valid v2 Book, three existing intent chapters.
- `research-budget.sh`: 20 grouped survey rows, five listed literature/
  upstream sources; the report explicitly discloses the larger cross-repo
  individual-file/source scope under Budget Override.
- Changed-document relative links: 27 resolved targets.
- Pinned predecessor citations: 25 source objects and line anchors resolved
  against the local Git object databases at the recorded full commits.
- `git diff --check`: passed.
- Independent read-only review of session evidence corrected message-ID
  labeling, early prefill rounding, and two compression-attempt timings;
  the corrections are incorporated. Privacy/causal-claim review found no
  remaining material issue in the sanitized case.
- Independent lineage review supplied exact superseded-intent links,
  corrected the roles of Kinesin's memory references and sharpened the native
  adapter comparison caveat; corrections are incorporated.
- Independent evaluation review removed an unsupported managed-growth toggle
  assumption and replaced it with the existing external-endpoint isolation.

The first broad link scan encountered empty scaffold files and intentional
negative/example links in Sprint 0; it was not a valid pass/fail result for
these changes. The corrected scan covers this change's actual documents.
The first cross-repo Git check encountered sandbox ownership checks; rerun
used per-command trust for the two user-supplied repositories, without
changing global Git configuration.

Research was committed as `1b1bfd1b97`. `check-tracked.sh` then reported a
fully committed Book and the router reported `plan`. This receipt is an
additional research record; the handoff commit includes it. Canonical plans
remain unlocked pending the invoked workflow's user approval gate.

No inference, live configuration changes, provider implementation or runtime
test suite was run. The draft proposed build/test plan is scratch, not a
finalized plan or completed sprint.
