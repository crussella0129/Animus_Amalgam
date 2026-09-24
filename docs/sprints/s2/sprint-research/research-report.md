# Sprint 2 Research Report

## Intents Reviewed

- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) —
  selected and revised; state: proposed. Owner selected existing 27B first and
  300 seconds per pilot request. This sprint advances T-201 only: inventory,
  manifest, fixed-context smoke, resource admission and cancellation. Paired
  native/static qualification and context-policy trials remain T-202.

## 1. Sprint Goal

Build and exercise a bounded qualification gate for the existing local
Qwen3.8-27B artifact using the accepted Hermes custom-provider path and a
separately owned llama.cpp process. Publish a reproducible manifest and all
outcomes, including `not-run: resource gate`. The first question is whether
this host can safely admit a small request and stop it predictably. It is not
yet whether adaptive constrained decoding improves an agent.

PR #2 was merged before this sprint. The declared `dev` work branch was
fast-forwarded to accepted `main` at
`cd2185c288398b19941b968e4352bf38bbcafbda`. Current source includes
accepted runtime and output-limit changes that invalidate assumptions based
only on Sprint 1's source pin. No model was loaded during this research.

## 2. Existing Code Survey

Paths below refer to that source pin; local artifacts are fingerprinted in
the inventory. Existing tests were read, not executed during research.

| File / evidence | Relevance | Finding |
|---|---|---|
| `docs/intents/INT-0004-bounded-local-model-qualification.md` | high | Requires artifact identity, owner choice, isolated cancellation and resource gates before qualification. |
| `docs/lineage/local-evaluation-protocol.md` | high | Fixed context, single slot, explicit limits, complete failures and separate context-policy axis. |
| `docs/lineage/local-session-case-study.md` | high | Long generation and cold prefill are separate costs; the 10,800-second timeout is historical evidence. |
| `agent/AGENTS.md` | high | Stable prompt, tool authority and physical auxiliary-attempt contracts. |
| `hermes_cli/AGENTS.md` | medium | Area guidance consulted for runtime resolution; full area guidance must be read before implementation there. |
| `hermes_cli/local_runtime/bootstrap.py` | high | Disabled managed runtime returns without acquiring a supervisor in the ordinary path. |
| `hermes_cli/local_runtime/gguf.py` | high | Existing header parser supplies metadata and tensor bytes without loading weights. |
| `hermes_cli/local_runtime/hardware.py` | high | Existing live RAM/VRAM probes; capacity is distinct from available memory. |
| `hermes_cli/local_runtime/context_policy.py` | high | Managed context fit/growth must stay outside the fixed pilot. |
| `hermes_platform/host/facts.py` | medium | Canonical host facts avoid adding another platform-resolution implementation to core. |
| `evals/output_caps_local_capture.py` | high | Existing local wire-capture pattern; fixtures are not inference evidence. |
| `tests/gateway/test_output_caps_removed.py` | high | User configuration caps are deliberately ignored; explicit internal wire budgets remain supported. |
| `agent/agent_init.py` | high | Direct agent construction retains an explicit internal `max_tokens`; defaults are uncapped. |
| `agent/chat_completion_helpers.py` | high | Internal and ephemeral budgets reach the chat transport; inspect actual serialized requests. |
| `agent/auxiliary_client.py` | high | Compression configuration is not a reliable output cap; physical attempt and explicit budget need verification. |
| `agent/context_compressor.py` | high | Small-context threshold floors can defeat assumed compression timing. |
| `agent/model_metadata.py` | high | Context metadata floors are not proof of the external server allocation. |
| `agent/auxiliary_hooks.py` | high | Existing observers can identify physical auxiliary attempts without modifying core. |
| Local GGUF artifacts and llama.cpp version/help/manifest | high | 27B and 7B exist locally; pinned b10964 supports fixed context, slots, explicit offload and cache limits. |

## 3. External Sources

- [Pinned llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/tools/server/README.md) — endpoint and slot inspection contracts; cancellation and cache reuse still require local evidence.
- [Pinned llama.cpp function calling documentation](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/docs/function-calling.md) — native templates may already constrain tools; native is not automatically unconstrained.
- [Qwen2.5-Coder 7B GGUF model card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) — publisher family reference for the available comparison; does not establish the provenance of either local artifact.

## 4. Risks, Unknowns, Dependencies

- **Memory:** the selected artifact has 15.32 GiB of tensor data. The later
  research snapshot has 7.26 GiB available system RAM and 8.96 GiB free VRAM.
  After reserving 4 GiB RAM and 1 GiB VRAM, their optimistic combined capacity
  is only 11.22 GiB, before KV, scratch, driver and host overhead. This is a
  conservative no-paging admission failure, not proof that mmap cannot load
  the file. Recheck before launch; never create page pressure to discover fit.
- **Latency:** 300 seconds is the owner's chosen small-request deadline.
  The live three-hour setting is neither changed nor treated as evidence of
  capacity. Report prefill, decode and total separately where observable.
- **Limits:** current Hermes intentionally omits legacy user output caps.
  Verify an explicit 128-token internal budget on both main and auxiliary
  wire paths before live inference. A YAML field or server default is not proof.
- **Context:** 8,192 tokens is a proposed fixed ceiling, not the model's
  advertised maximum. Tokenize the complete rendered prefix and request;
  reject a request over 4,096 input tokens rather than silently truncating it.
- **Cancellation:** client disconnection alone does not prove backend idle.
  An independent process owner must stop its entire owned job, even if a
  request or telemetry collector stalls. Do not terminate unrelated processes.
- **Measurements:** shared VRAM and hard-paging evidence may be unavailable
  through the installed tools. A safety-critical missing probe blocks a live
  attempt; optional missing quality metrics remain explicit nulls.
- **Environment:** current source and the installed Hermes virtual environment
  are different identities. Freeze a compatible evaluation environment before
  tests; do not update the live environment to make the experiment run.
- **Scope:** a tiny no-tool smoke is not useful-agent qualification. INT-0004
  remains unfinished until T-202's paired task and context trials are tested.

## 5. Recommended Approach

Use a small standalone Rust evaluation supervisor for process ownership,
deadlines and resource gates, with thin Python glue exercising actual Hermes
main and compression paths. Rust is viable for Windows process ownership;
Python is justified for the existing Python agent API, not a replacement
agent loop. Keep it under `evals/`, with no provider plugin, service, new core
tool, live-config change or automatic model fallback.

First prove the gate against local deterministic fixtures, including a stalled
backend and resource breach. Then freeze a manifest and run a fresh resource
admission check. Only an admitted 27B candidate can load. Use one slot, fixed
8K context, at most 4K input and 128 output, bounded CPU/GPU placement,
explicit cache settings, and independent cancellation. A resource rejection
is a complete recorded outcome for T-201, while live qualification stays
unproven. Do not advance T-202 automatically.

Alternatives considered: Python-only supervision would reduce initial code,
but an independent Rust owner follows the project's language preference and
keeps stop authority outside the driver. Reusing managed Hermes serving would
change context allocation. Starting with the available 7B would improve the
likely memory margin but conflicts with the owner's selected priority.

## Artifacts

- [Read-only inventory](inventory.md) — exact local fingerprints, host
  snapshot, measurement methods and unresolved provenance.
- [Pilot design inputs](pilot-design.md) — owner choices, admission policy,
  proposed limits and receipt contract for the Plan phase.

## Budget Override

Resume-state verification, merged-main synchronization and cross-cutting
runtime revalidation exceeded the initial wall-clock research window and
included supporting Book/helper files beyond the table's 19 evidence rows.
This was necessary to avoid applying Sprint 1 assumptions to the newly
accepted output-cap and runtime code. External research stayed at three
primary sources; stop exploratory research here and carry unresolved runtime
questions into explicit build/test gates.
