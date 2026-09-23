# Animus_Ferric lineage

This chapter evaluates Animus_Ferric at commit
[`51af84e933c0f6ff4a42f1508cb9aefad00847c5`](https://github.com/crussella0129/Animus_Ferric/tree/51af84e933c0f6ff4a42f1508cb9aefad00847c5).
It separates source-backed architecture from historical benchmark reports.
Those reports were not rerun for Amalgam.

## Architecture

`ferric-core` is a small domain and policy crate, not an inference engine or
token decoder. Its public surface exports types and deterministic run-policy
logic, while the
[profile selection function](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-core/src/scale.rs#L329)
chooses an explicit override, measured level, or parameter prior and derives
budgets. The
[tool registry](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-tools/src/registry.rs#L249)
bounds offered actions by tier and ring. This is deterministic policy
adaptation; it does not inspect logits or learn online.

The [action-schema generator](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-loop/src/grammar.rs#L61)
lives in `ferric-loop`, not `ferric-core`. It constructs an ordered JSON
Schema with one branch per permitted action and requires `thought`, `tool`,
and `args`. Pulling that crate into another harness would also pull loop,
provider, tool, guard, trace, and VCS responsibilities.

The [OpenAI-compatible provider](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/crates/ferric-provider/src/openai.rs#L149)
is a downstream HTTP client. It sends `response_format` or grammar metadata;
the external server performs token masking. Native tools use a separate
request branch, and the provider declares that it does not expose logits.
Its capability declaration is broader than its behavior: the regex variant
does not transmit an enforced constraint. Amalgam must qualify each concrete
endpoint and fail visibly when enforcement is unavailable.

## Reported successes and their limits

The [legacy decision record](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/history/decisions-legacy.md#L80)
reports 25/25 constrained single-tool results versus 0/25 native for an early
Qwen2.5-Coder-7B setup, followed by 50/50 single-call calibration for several
model sizes. That is evidence for shape reliability in those configurations,
not general autonomous task completion. The same record says the 1B profile
failed every multiturn ladder level. ADR-025 later reports native 7B/8B
improving from 0% to 100% after a content-tool-call fallback repair while 1B
native remained 22%, making the early comparison adapter-dependent. Some old
linked receipts no longer exist, so these remain historical reported results.

[Sprint 115](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/sprints/s115/sprint-tests/test-report.md#L19)
reports a Qwen3.8-27B UD-Q4_K_M constrained smoke on CUDA b10516 at 32,768
context, 24 of 66 GPU layers, flash attention, and Q8 KV. Three scored samples
had median decode throughput of 3.565 tokens/second. The frozen application
trial did not start after the external server ended. A separate successful
counter-app field report was explicitly excluded from autonomous application
qualification.

## Failed and abandoned directions

Ferric's
[evidence-bound recovery intent](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/intents/INT-0001-evidence-bound-autonomous-recovery.md#L89)
is abandoned. Its
[frozen development screen](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/sprints/s113/sprint-tests/development-screen.md#L3)
records all three controller versions at 0/3 task completion. Enforcement and
tracing made failure more legible but did not produce recovery; repetition and
oscillation remained, and confirmation/held trials were not run.

[ADR-027](https://github.com/crussella0129/Animus_Ferric/blob/51af84e933c0f6ff4a42f1508cb9aefad00847c5/docs/history/decisions-legacy.md#L102)
corrects an apparent in-process mistral.rs recovery: the adapter had stripped
the constraint, so the experiment never tested enforcement. Restoring even a
trivial constraint then hung historically. That result argues for inspecting
the actual outbound request, enforcing cancellation, and keeping the first
Amalgam experiment out of process. It does not establish a current upstream
mistral.rs defect.

## Transfer to Amalgam

Language-independent lessons are the deterministic mapping from measured
capability to bounded policy, server-enforced action shape, explicit failure,
and separate semantic/task checks. Rust-specific assets are Ferric's crate
graph and types. Backend-dependent assets are JSON-Schema/grammar coverage,
chat-template behavior, cancellation, and actual token-mask enforcement.

Amalgam should reuse the policy and ordered-action principles through Hermes's
existing provider boundary. It should not import Ferric's complete loop,
describe `ferric-core` as a decoder, or treat syntactic validity as task
success. A new decoder remains an experiment contingent on a measured gap in
existing engines.
