# Kinesin lineage

This chapter evaluates Kinesin at commit
[`a4491211e605d2358e0e1daa00598920c8b213dd`](https://github.com/crussella0129/Kinesin/tree/a4491211e605d2358e0e1daa00598920c8b213dd).
It preserves the difference between a valid structure, a semantically valid
answer, and a task that was independently completed.

## Architecture

Kinesin's
[loop and tools contract](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/loop-and-tools.md)
sends either native tools or an explicit response constraint on a request,
never both. Native tool grammar comes from the selected llama.cpp chat
template. After tools are withdrawn, a checked answer uses a shape-only JSON
Schema; a separate checker owns semantic validity. That division is a Kinesin
request contract, not evidence that every backend must make the same split.

Kinesin also separates execution authority from model output. A schema limits
which response shapes can be produced, while the harness decides whether a
requested action is permitted and whether the result proves completion.

## Scoped positive observations

[Sprint 15](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s15/failure-report.md#L8)
records two correct explicit-file edits with an ordered schema when comparison
arms failed. This supports a narrow claim: supplying the concrete target and
structured action language helped that frozen case. The same sprint's
behavioral app-repair arms produced no tool calls, so it does not qualify
general autonomous repair.

A later
[actual-session cache experiment](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s10/sprint-tests/remote-deployment.md#L64)
observed 1,549 cached and 48 evaluated tokens on measured second turns. Both
flag-on and flag-omitted arms reused the cache. The result establishes reuse
in those sessions, not a causal performance benefit from specifying
`cache_prompt`.

## Failures and superseded claims

In
[Sprint 16's attempt ledger](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s16/sprint-tests/diagnostics/attempt-ledger.md#L3),
the no-assistance, authentic-filename, and full-source arms each returned two
valid answers and performed zero operations. Source-assisted prose identified
the defect and then falsely claimed a repair. The
[failure analysis](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/sprints/s16/sprint-research/failure-mechanisms.md#L9)
does not attribute this to exhausting time, context, or output budget, and no
malformed action reached an executor. Valid shape and the model's completion
review did not produce action selection or task completion.

[INT-0004](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0004-kv-cache-reuse.md#L45)
was superseded because its original benchmark did not exercise real session
construction. The corrected session observation above retains the narrower
reuse result and leaves concurrent-slot and full-history behavior open. Its
successor,
[INT-0026](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0026-session-context-continuity.md#L15),
carries actual session assembly, token-window admission, full-history
continuity, and concurrent-slot/data-boundary criteria; those broader criteria
remain proposed rather than proven by the partial observation.

[INT-0008](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0008-remote-model-over-overlay.md#L81)
was superseded because private-address plaintext and a same-host LAN
comparison did not prove cross-machine confidentiality.
[INT-0022](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0022-completed-contract-repairs.md#L24)
owns the repaired client policy, while
[INT-0027](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0027-encrypted-remote-deployment.md#L29)
preserves the broader proposed deployment outcome.

[INT-0011](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0011-production-readiness-roadmap.md#L63)
was superseded when the Sprint 10 revision added missing foundational
ownership and current evidence.
[INT-0015](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0015-threat-model-assurance.md#L66)
was superseded when its assurance revision completed taxonomy/native-FFI
coverage and recorded the MCP boundary. Their realized successor,
[INT-0021](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/docs/intents/INT-0021-harness-contract-review.md#L29),
is an evidence-linked audit and roadmap repair, explicitly not certification.

## Resource-bound lessons

The [session types](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/session.rs#L9)
cap live reference memory at 8 KiB and 16 turns. The
[CLI memory policy](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/cli/session.rs#L18)
may choose a smaller byte window and explicitly does not count model tokens.
Its [drop-oldest compaction](https://github.com/crussella0129/Kinesin/blob/a4491211e605d2358e0e1daa00598920c8b213dd/src/core.rs#L387)
preserves tool groups and checked evidence. The invariant transfers to
Amalgam; the byte limit and implementation do not.

## Transfer to Amalgam

Language-independent lessons are explicit authority, bounded resources,
group-preserving compaction, request-contract clarity, and a semantic checker
separate from grammar validity. Rust-specific mechanisms are Kinesin's types
and ownership implementation. Backend-specific mechanisms are template-
derived tool grammar, response-format coverage, cache accounting, and remote
transport guarantees.

Amalgam should keep Hermes's established tool execution and permission model,
constrain syntax at the serving boundary where qualified, and verify results
outside the model. A well-formed final answer cannot count as task completion
when the required action never occurred.
