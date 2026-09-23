# Sprint 1 Unit Test Results

- **Tested build head:** `1e3c15a9606fb23e6af35ca92b4dbb86ebd21f4f`
- **Date:** 2026-09-23
- **Scope:** evidence and document-contract checks for the locked Sprint 1
  EARS clauses. No inference, model benchmark, live configuration change, or
  source-runtime test was performed.

## Results

| Test | EARS coverage | Result | Assertion and evidence |
|---|---|---|---|
| `ferric_evidence_audit` | T-101 clauses 1-2 | pass | The full `51af84e933c0f6ff4a42f1508cb9aefad00847c5` commit exists locally. All nine cited source objects and nine line anchors resolve at that commit. Content inspection distinguishes `ferric-core` policy, `ferric-loop` schema construction, external token masking, the unenforced regex declaration, the corrected native adapter, reported benchmark limits, and the abandoned 0/3 recovery result. |
| `kinesin_evidence_audit` | T-102 clauses 1-2 | pass | The full `a4491211e605d2358e0e1daa00598920c8b213dd` commit exists locally. All 16 cited source objects and 15 line anchors resolve. The chapter covers the tools/constraint split, Sprint 15/16 evidence, INT-0004/0008/0011/0015 with their INT-0026/0022/0027/0021 successors and qualification limits, bytes versus model tokens, and observed cache reuse versus a causal `cache_prompt` claim. |
| `hermes_path_audit` | T-104 clauses 1-2 | pass | Thirty cited source/test objects and their maximum cited lines resolve at Amalgam commit `6223d9e2bc3280e6e21d0b0a6961eadfafe4183e` or installed checkout commit `5dd70d7cb6560c3ff8aff294ec44ec4f8d1558e5`, as labeled. The chapter traces custom provider, request assembly, transport, validation, guarded dispatch, cache invariants, managed growth before compression, and later implementation coverage. |
| `session_receipt_audit` | T-107 clauses 1-2 | pass | The current private `agent.log`, `llama-server.log`, `config.yaml`, and `presets.ini` still match all four recorded byte counts and SHA-256 fingerprints. The sampled API rows, backend timing coordinates, cache-limit rejection, eviction, 64K-to-96K restart, and five compression ceilings reconcile with those sources. The committed case labels RSS/VRAM/paging/thermal/crash causality as unmeasured and contains fingerprints and coordinates rather than raw artifacts, configuration, transcript, or credentials. |
| `comparison_coverage` | T-103 clauses 1-2 | pass | The comparison covers action vocabulary, enforcement location, guarantee, adaptation, failure handling, backend dependency, and cache/context cost for Ferric, Kinesin, and Hermes. Its transfer section separately labels language-independent, Rust-specific, runtime-specific, and backend-specific mechanisms. |
| `lessons_integrity` | T-103 clause 3 | pass | The register contains exactly 14 unique sequential IDs, `L-01` through `L-14`. Every row has one allowed disposition, a non-empty transfer boundary, and at least one resolvable evidence link. |
| `experiment_gate_review` | T-108 clauses 1-2 | pass | The protocol fixes external context and request ownership, defines a <=4K/128-token smoke, 120-second request cap, 4 GiB RAM and 1 GiB VRAM headroom gates, external and auxiliary cancellation, stop conditions, three paired pilot repetitions, missing-data labels, independent completion checks, and separate context-policy trials. It does not assume a managed-growth toggle. |
| `intent_traceability` | T-105 clauses 1-2 | pass | INT-0004, INT-0005, and INT-0006 contain observable criteria, rationale, alternatives, consequences, state history, lesson citations, non-goals, and explicit future gates. INT-0005 defines deterministic adaptation and rejects authority growth; INT-0006 gates any decoder work on a reproduced engine gap. Seven Sprint 1 task commits resolve, and T-201 through T-205 queue the follow-on work and owner decisions without claiming implementation. |
| `scope_and_content_review` | T-105 clause 2; T-104 clause 2; T-107 clause 1 | pass | The complete sprint diff from the pre-sprint Amalgam head contains only Markdown under `docs/`. A credential-pattern screen found no API key, bearer token, or common secret prefix. No runtime configuration, inference code, provider implementation, raw log, database, transcript, or unrelated local change is committed. |

## Reproducible confirmations

- Pinned-citation object audit: `2` commits, `25` blob objects, and `24`
  explicit line anchors resolved; the Ferric/Kinesin split is recorded above.
- Hermes coordinate audit: `30` source/test objects resolved at the two
  chapter-labeled commits and every cited maximum line was in range.
- Private receipt audit: `4/4` files matched their recorded sizes and hashes.
- Content-contract audit: predecessor boundaries, seven comparison
  dimensions, 14 lessons, protocol gates, three detailed intents, ten named
  tests, completed-task commits, docs-only scope, and secret screen passed.
- `git diff --check`: clean.

The checks read Git objects and the fingerprinted local evidence. They did not
write to the predecessor repositories or the owner's Hermes state.
