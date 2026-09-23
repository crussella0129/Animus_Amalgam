# Pinned lineage findings

Ferric: `51af84e933c0f6ff4a42f1508cb9aefad00847c5`.
Kinesin: `a4491211e605d2358e0e1daa00598920c8b213dd`.
Their local committed trees match these pins despite different pre-merge dev
HEADs. An unrelated uncommitted Ferric test edit was excluded. No predecessor
code, configuration or running model was changed. These notes support the
future T-101/T-102 chapters; historical reported tests were not rerun.

## Ferric: reusable policy, external enforcement

[`ferric-core`](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-core/src/lib.rs#L1)
provides types and policy. Its
[`scale.rs`](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-core/src/scale.rs#L329)
selects a tier from explicit override, measured level, then parameter prior;
the resulting policy sets budgets. The
[tool registry](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-tools/src/registry.rs#L249)
bounds offered tools by tier and ring. This is concrete configured/measured
adaptation; it is not an inference engine, an online learner or a decoder
that inspects logits.

The [action-schema generator](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-loop/src/grammar.rs#L61)
is in `ferric-loop`, with a branch for each allowed action and required
`thought`, `tool`, `args`. Importing that crate brings tools, guards, trace,
VCS and provider dependencies; importing `ferric-core` alone does not supply
the action generator.

The [OpenAI provider](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-provider/src/openai.rs#L149)
is a downstream HTTP client. It sends a schema/grammar for enforcement by the
server; native tools use a separate branch. It advertises `exposes_logits:
false`. Its unconditional constraint capability and unenforced `Regex`
variant are reasons to qualify a backend rather than copy the declaration.
There is no ready-made Ferric_Core serving endpoint established by this source.

## Positive results have bounded meaning

The [historical decisions](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/history/decisions-legacy.md#L80)
report 25/25 constrained single-tool outcomes versus 0/25 native for one
early Qwen2.5-Coder-7B configuration, and later 50/50 single-call calibration
for several model sizes. The same history reports the 1B failing every
multiturn ladder level. ADR-025 records native 7B/8B improving from 0% to 100%
after a content-tool-call fallback fix, while 1B native remained 22%. This
weakens any sweeping interpretation of the early native comparison. Some historical linked
receipts are missing; retain the label "documented historical result".

[Sprint 115](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/sprints/s115/sprint-tests/test-report.md#L19)
reports Qwen3.8-27B UD-Q4_K_M on CUDA b10516, 32,768 context, 24/66 GPU
layers, flash attention and Q8 KV. A constrained smoke passed; three scored
samples yielded median 3.565 decoded tokens/second. The frozen application
trial never began after external server termination. A separate successful
counter-app field report is expressly excluded from autonomous qualification.
This is a useful comparison condition, not evidence that 27B long sessions
are qualified on the owner's current Hermes configuration.

## Failed directions are part of the result

Ferric's [INT-0001](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/intents/INT-0001-evidence-bound-autonomous-recovery.md#L89)
was abandoned. Its [frozen development screen](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/sprints/s113/sprint-tests/development-screen.md#L3)
records three controller versions each at 0/3 task completion. Verified
blocking and traces did not yield the intended recovery; repetition and
oscillation remained. Confirmation/held trials were skipped. Do not carry
this forward as a successful controller awaiting a port.

[ADR-027's correction](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/history/decisions-legacy.md#L102)
records historical in-process mistral.rs hangs even with a trivial restored
constraint. Apparent earlier recovery was invalid because the adapter had
removed the constraint. Verify the actual request and enforcement, and keep
cancellation bounded. This historical result does not establish a defect in
current upstream mistral.rs.

## Kinesin: shape, meaning and resources are different checks

The [loop/tool contract](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/loop-and-tools.md)
separates native tools from a checked answer request: each request carries
tools or an explicit constraint. The server derives native tool grammar from
the chat template; checked answers use a shape-only response schema and
separate semantic checking. This is Kinesin's contract, not a universal
limitation of every backend API.

[Sprint 15](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s15/failure-report.md#L8)
records two correct explicit-file edits with an ordered schema, while
behavioral app-repair arms made zero tool calls.
[Sprint 16's diagnostic ledger](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s16/sprint-tests/diagnostics/attempt-ledger.md#L3)
reports no assistance, authentic filenames and full-source arms: each made
two valid answers and zero operations. Source-assisted prose identified a
bug and falsely claimed repair. The
[failure analysis](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s16/sprint-research/failure-mechanisms.md#L9)
does not identify exhaustion of the time/context/output budgets, or malformed
actions reaching execution. Syntax and the model's own completion review did
not establish useful action selection.

The old [cache intent](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0004-kv-cache-reuse.md#L45)
was superseded because its benchmark did not exercise actual session
construction. A later [faithful session experiment](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s10/sprint-tests/remote-deployment.md#L64)
observed 1,549 cached plus 48 evaluated tokens on measured second turns.
Both flag-on and flag-omitted arms reused cache. It demonstrated reuse,
not a causal benefit from setting `cache_prompt`.

Kinesin's [session types](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/session.rs#L9)
cap live reference memory at 8 KiB/16 turns; its
[memory policy](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/cli/session.rs#L18)
may choose a smaller byte window and explicitly does not count model tokens.
[Compaction](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/core.rs#L387)
preserves tool groups and checked evidence. Adapt those invariants, not the
specific byte limit, to Hermes's tokenizer and cached history.

Kinesin's [INT-0008](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0008-remote-model-over-overlay.md#L81)
became superseded because private-address plaintext and a same-host LAN
comparison did not prove cross-machine confidentiality.
[INT-0022](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0022-completed-contract-repairs.md#L24)
owns the repaired client policy;
[INT-0027](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0027-encrypted-remote-deployment.md#L29)
preserves the broader deployment outcome. Sprint 10 supplied a scoped
two-host observation, but INT-0027 remains proposed.

[INT-0011](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0011-production-readiness-roadmap.md#L63)
became superseded when the Sprint 10 roadmap revision added missing
foundational ownership and current evidence.
[INT-0015](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0015-threat-model-assurance.md#L66)
became superseded when the assurance revision completed taxonomy/native-FFI
coverage and recorded the MCP boundary. Their successor,
[INT-0021](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0021-harness-contract-review.md#L29),
is realized as an evidence-linked audit/roadmap revision, explicitly distinct
from certification. Historical records and proposed outcomes retain their limits.

## Preliminary lessons for comparison

| ID | Disposition | Lesson and evidence above |
|---|---|---|
| L-01 | adopt | Treat a grammar as an executable shape contract; qualify enforcement on the actual endpoint. Ferric provider/ADR-027. |
| L-02 | adapt | Deterministic capability-to-policy mapping is reusable; Ferric core and rings are not a new decoder. |
| L-03 | adopt | Keep syntax, action choice, semantic validity and independent task completion as separate measurements. Ferric s113; Kinesin s15/s16. |
| L-04 | avoid | Do not revive evidence-controller complexity as a proven success after its objective gate failed. Ferric abandoned INT-0001. |
| L-05 | adapt | Bound context/output/resources independently of grammar; retain evidence and tool groups at compaction. Kinesin session limits and local session trace. |
| L-06 | adopt | Measure backend cache reuse on real session construction; a flag or absent counter is insufficient. Kinesin corrected cache evidence. |
| L-07 | avoid | Do not rewrite Hermes's prompt/tool catalog each turn to copy dynamic tool rings. Preserve its conversation cache contract. |
| L-08 | open question | A new self-constraining decoder needs an identified engine/policy gap and a controlled win over existing engines. No such win is established by these sources. |
| L-09 | adopt | Preserve negative trials, skipped qualifications and missing receipts as limitations. Ferric s115; Kinesin superseded claims. |

This table is a research draft. T-103 will publish the stable comparative
chapter and lessons register; T-105 will cite that register in detailed
implementation intents.
