# Sprint 1 Research Report

## Intents Reviewed

- [INT-0002](../../../intents/INT-0002-lineage-lessons-ferric-kinesin.md) —
  selected; current state: proposed. Pinned predecessor evidence must precede
  a port or new decoder.
- [INT-0003](../../../intents/INT-0003-animus-adaptive-constrained-decoding.md) —
  revised from the owner's 2026-09-23 request; current state: proposed. Added
  the 2080 Ti / 32 GB target, provider/service alternatives and long-session
  resource behavior to the research boundaries. No implementation chosen.

## 1. Sprint Goal

Determine a defensible first architecture and evaluation sequence for using
small local models in Hermes through Animus Adaptive Constrained Decoding.
Use the Ferric and Kinesin Books/source at their existing pins, the fork's
actual provider interfaces, and the owner's supplied session as evidence.
The sprint produces cited lineage chapters, a comparison/lessons register,
the sanitized failure case, a bounded experiment protocol and detailed
follow-on intent proposals. It does not implement a decoder, port an agent
loop, alter live Hermes configuration, or replay the machine-stressing run.

The supplied transcript was found in local session
`20260921_002531_5fd0cf`, model `Qwen3.8-27B-UD-Q4_K_M`. The important
question is broader than malformed calls: how to complete useful tasks while
keeping context, generation and recovery inside the host's resource envelope.

## 2. Existing Code Survey

Coordinates are pinned/source-specific in the linked artifacts. Directory
groups below are navigation summaries; the Budget Override acknowledges the
larger actual cross-repository inspection.

| File / evidence group | Relevance | Finding |
|---|---|---|
| `docs/intents/INT-0002-lineage-lessons-ferric-kinesin.md` | high | Existing analysis-only contract and immutable predecessor pins. |
| `docs/intents/INT-0003-animus-adaptive-constrained-decoding.md` | high | Coarse implementation purpose; now includes the owner's hardware and provider direction. |
| Ferric `crates/ferric-core/src/scale.rs` | high | Deterministic model/profile-to-policy mapping; core is not an inference engine. |
| Ferric `crates/ferric-loop/src/grammar.rs` | high | Ordered action schema belongs to the loop crate, with a broader dependency graph. |
| Ferric `crates/ferric-provider/src/openai.rs` | high | HTTP client sends constraints to external backend; no logits interface; enforcement capabilities need qualification. |
| Ferric `docs/history/decisions-legacy.md` | high | Narrow successes, repaired native adapter and false constraint-free recovery observation. |
| Ferric `docs/sprints/s113/sprint-tests/development-screen.md` | high | Recovery controller failed task gate; abandoned intent must remain negative evidence. |
| Ferric `docs/sprints/s115/sprint-tests/test-report.md` | high | 27B constrained smoke and 3.565 tok/s median; app trial not run. |
| Kinesin `docs/loop-and-tools.md` | high | Native actions and constrained checked answers have different request contracts; semantics are separately checked. |
| Kinesin `docs/sprints/s16/sprint-tests/diagnostics/attempt-ledger.md` | high | Valid answers and zero operations across assistance arms. |
| Kinesin `docs/sprints/s10/sprint-tests/remote-deployment.md` | high | Actual-session cache reuse without evidence that the optional flag caused it. |
| Kinesin `src/session.rs`, `src/cli/session.rs`, `src/core.rs` | high | Bounded reference memory and group-preserving compaction, not exact token budgeting. |
| Hermes `providers/base.py`, `providers/__init__.py` | high | Out-of-tree provider registration and custom-client seam already exist. |
| Hermes `agent/transports/chat_completions.py` | high | Existing messages/tools protocol; provider default hooks lack full request state. |
| Hermes `agent/turn_api_request.py`, `agent/turn_response_intake.py` | high | Request middleware and timing/usage observers avoid new core instrumentation. |
| Hermes `model_tools.py`, `agent/turn_tool_validation.py` | high | Schema sanitation, response validation and existing tool dispatch authority. |
| Hermes `agent/context_compressor.py`, `agent/turn_context_compaction.py` | high | Compression floors; managed growth runs before compression. |
| Hermes `hermes_cli/local_runtime/context_policy.py`, `growth.py`, `bootstrap.py` | high | Growth is constant-driven; separate fixed endpoint is the existing bounded experiment seam. |
| Local `logs/agent.log`, `logs/llama-server.log`, session database | high | Exact transcript match, request trajectory, compression, cache eviction, growth/restart and cold prefill. |
| Local `config.yaml`, `runtimes/llamacpp/presets.ini`, GGUF header | high | Current/historical conditions distinguished; metadata supports local model label. |

Amalgam source pin: `6223d9e2bc3280e6e21d0b0a6961eadfafe4183e`.
Current installed Hermes source: `5dd70d7cb6560c3ff8aff294ec44ec4f8d1558e5`.
Do not substitute one for the other or either for unrecorded historical
process provenance. Ferric/Kinesin pins and immutable citations are in
[lineage findings](lineage-findings.md). Local log fingerprints and exact
line coordinates are in [session evidence](local-session-evidence.md).

## 3. External Sources

Reviewed 2026-09-23; current upstream documentation is capability background,
not proof that the locally installed binary has those features.

- [llama.cpp HTTP server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) — cache and separate prompt/decode timing surfaces for a measured baseline.
- [llama.cpp llguidance support](https://github.com/ggml-org/llama.cpp/blob/master/docs/llguidance.md) — existing build-time integration for grammar enforcement.
- [llguidance](https://github.com/guidance-ai/llguidance) — existing Rust constraint engine; published mask performance is not this host's end-to-end performance.
- [JSONSchemaBench](https://arxiv.org/abs/2501.10868v3) — separate efficiency, constraint coverage and task-quality evaluation.
- [Grammar-Aligned Decoding](https://arxiv.org/abs/2405.21047v4) — distribution distortion and an adaptive sampling research direction; no demonstrated fit to this workload/hardware.

## 4. Risks, Unknowns, Dependencies

**The session has multiple slowdown mechanisms.** Requests grow from about
20K to 65K input tokens. Large file/tool output and reasoning accumulate.
Early cache reuse is substantial; long generations dominate some calls.
Later cache-capacity rejection, eviction and full prefill are observed.
On resume, 64K-to-96K growth restarts the backend; the cold 65,155-token
prefill takes 162.2 minutes. Five approximately 600-second compression
attempts do not shrink the history. Actual paging, peak RAM/VRAM, thermals
and the host's near-crash mechanism were not measured.

**A lower compression ratio is not a resource limit.** Current installed
source explains the logged 55,705/73,728 trigger values via ratio/minimum/cap
rules. Managed growth is attempted before compression and its caller does
not provide measured decode speed. Lowering the compression trigger without
separating runtime growth can move growth consideration earlier. This is a
source-backed risk; no runtime fix is asserted or implemented.

**Ferric_Core is not a serving decoder.** Reuse its policy ideas deliberately.
The action-schema generator and external HTTP client have different ownership
and coupling. Porting the whole loop would duplicate Hermes execution and
authority. Early constrained-vs-native success comparisons include an adapter
defect later repaired; they do not establish an enduring constrained advantage.

**Grammar validity is insufficient.** Ferric's recovery controller stayed
0/3, and Kinesin generated valid final answers instead of doing the work.
Independent completion checks, honest failure and bounded retries must remain
separate from action shape. Automatic/model-proposed constraints are not
trusted authority.

**Cache compatibility must be demonstrated at the backend.** Stable Hermes
messages are necessary but may not be sufficient. Tool choice, response
format, grammar metadata, templates, slots, compression and auxiliary calls
can affect rendered prefixes or residency. Measure both warm and cold paths.

**The operating envelope is unresolved.** The owner was asked whether to
favor smaller-model responsiveness or 27B quality. Pending that optional
preference, the experiment proposal starts small and retains 27B as a bounded
comparison. No latency promise or largest usable context has been established.

**Research precedes engine selection.** A new decoder is a valid research
alternative, but its necessity must come from an engine coverage/performance
gap after controlling context/offload issues. No inference was run in this
phase. Source/code claims and historical receipts must not be reported as new
experimental results.

## 5. Recommended Approach

Advance a documentation/research sprint, then choose an implementation from
the resulting evidence. The first technical hypothesis is an existing Hermes
custom endpoint backed by a narrow Rust policy/protocol service and qualified
llama.cpp enforcement. An optional provider plugin can supply concrete setup
or metadata needs. Keep conversation ownership, tools and permissions in
Hermes. Do not require a service layer if a bounded existing endpoint already
meets the task goal.

The staged evaluation is:

1. Inventory/tokenize the fixed prefix and establish a small smoke gate on a
   separately launched fixed-context server, with fresh isolated Hermes
   configuration and managed runtime disabled. Prove cancellation before a
   long run. This prevents runtime growth from invalidating the experiment.
2. Compare ordinary local Hermes, static constrained actions and adaptive
   policy at the same model, context, sampling and resource limits. Identify
   any grammar already supplied by the native tool template in the baseline.
3. Test context/compression policies separately from constraints. Record
   first meaningful token, prefill/decode, actual reuse, generation volume,
   task correctness and peak resources; stop on the predeclared cap.
4. Define adaptive policy as a deterministic mapping from capability,
   trusted state, checked outcomes and remaining budget to an allowed next
   action language/output budget. Test cache invariance for those controls.
5. Open a new-engine experiment only if a specific coverage/performance gap
   survives those controls. Treat model-generated grammars as checked
   proposals. A negative result should preserve the simpler implementation.

For this sprint's Build Phase, publish T-101/T-102 predecessor chapters,
T-104 Hermes seams, T-107 session case, T-103 comparison/lessons, T-108
evaluation protocol, then T-105 detailed intent proposals. Keep T-106's
upstream governance work as backlog: it is not necessary to answer this
research question. No full decoder implementation belongs in this plan.

Alternatives considered: a full forked harness, wholesale Ferric-loop port,
in-process inference, increased timeouts alone, and a decoder written from
scratch. The current evidence favors the smallest provider/service seam;
the alternatives remain candidates when a measured requirement justifies them.

## Artifacts

- [Local session evidence](local-session-evidence.md) — sanitized timeline,
  token/cache/timing table, compression failures and mutable-source hashes.
- [Pinned lineage findings](lineage-findings.md) — successes, failed and
  superseded claims, reusable mechanisms and draft lesson IDs.
- [Hermes integration findings](hermes-seams.md) — existing seams, installed
  source correspondence, context/growth behavior and located test coverage.
- [Candidate evaluation](evaluation-design.md) — architecture alternatives,
  manifest, resource gates, controls, metrics and advancement criteria.

## Budget Override

This request spans two predecessor repositories, a large fork, a differently
versioned installed runtime and private session/backend evidence. More than
20 individual local files were inspected to verify failure claims, request
boundaries and the threshold/growth mechanism; the table groups related
files for readability, not to claim compliance with the individual-file cap.
Pinned local lineage sources are additional external-repository evidence
beyond the five literature/upstream sources above. This cross-cutting scope
justifies both expansions. Independent read-only subagents ran in parallel;
the research is bounded to the phase's 30-minute wall-clock window. No open
ended web survey, model run or live reconfiguration was performed.
