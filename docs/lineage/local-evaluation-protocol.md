# Bounded local-model evaluation protocol

This protocol turns the [lessons register](lessons-register.md) and
[long-session case](local-session-case-study.md) into a future experiment.
Sprint 1 defines the protocol; it does not run inference or change the owner's
live Hermes configuration.

## Questions in order

1. Can the selected local model complete useful Hermes tasks while the host
   remains responsive inside a fixed resource/context envelope? (L-07)
2. At the same model and budget, do explicit static constraints improve action
   and task outcomes over the endpoint's native tool behavior? (L-01, L-04)
3. Does deterministic adaptive policy improve on static constraints enough to
   justify its state and verification cost? (L-03, L-10)
4. Does profiling expose a constraint-coverage or mask-performance gap that
   justifies another engine or a new decoder? (L-14)

Sprint 1 proposed a smaller-model first pilot. On 2026-09-23 the owner
selected the existing Qwen3.8-27B first, with a 300-second total request
deadline for Sprint 2. Preserve the exact artifact and choice in the manifest.
The smaller local model is a later comparison, not an automatic fallback.

## Isolation and manifest

Use a fresh Hermes profile and process with `local_runtime.enabled: false`.
Launch llama.cpp separately at a distinct endpoint with fixed `--ctx-size`,
one request slot unless the experiment explicitly studies concurrency, and
explicit K/V formats and offload. Confirm the server-reported model, context,
parallelism, and empty/warm slot state before the first request. This prevents
Hermes's managed runtime from silently growing the window before compression.

Record:

- model artifact name, byte size, hash, quantization, tokenizer and chat-
  template hashes, license/source, and any draft model;
- llama.cpp commit/build features, including actual constraint engine,
  devices, GPU/CPU tensor placement, flash attention, K/V types, context,
  slots, batch/ubatch, threads, sampling, and reasoning/output limits;
- Hermes commit, isolated non-secret configuration, provider/plugin/sidecar
  commits, toolset and serialized fixed-prefix token count;
- OS, driver, CPU/RAM, GPU/VRAM, storage, other material workloads, and
  pre-run available system memory and dedicated VRAM;
- task corpus version, seed/order schedule, run identifier, and explicit
  differences between arms.

A model's declared maximum context is metadata, not a memory or latency
budget. If the measured fixed system/tool prefix does not fit the proposed
small context with completion/recovery reserve, choose a larger bounded
window or a smaller stable toolset at session start; do not truncate
instructional skills or change tools mid-conversation.

## Smoke and cancellation gate

### Development order

Following the owner's reverse-E2E clarification, bring up a disposable Hermes
environment and operate it before running official unit/integration suites.
Use only the instrumentation needed to observe and stop that environment.
Check the external stop control practically during bring-up; do not build a
large fixture matrix before touching the real application.

After the small smoke and cancellation controls work, drive a short real
workflow: inspect a fixture, edit it, execute a checker, encounter a failing
command and recover. Observe follow-up turns and bounded context pressure.
Reproduce each failure, diagnose it, repair the relevant code/configuration
and replay the same operation. Preserve all failed attempts and revision
identities. Changing a configuration between attempts creates a new manifest;
it never resets the overall run budget or permits weakening stop gates.

Operational confidence requires independently checked task completion,
successful replay of repaired paths in fresh and continued sessions, and
working main/auxiliary cancellation. Then run the affected official suites
and add focused regression coverage for failures actually found. If the host
cannot admit the model, operational confidence remains pending; green mocks
cannot replace it. Development exploration is separate from the subsequent
frozen, paired qualification experiment.

### Per-attempt limits

Start with a synthetic request of at most 4K input and 128 requested output
tokens when the measured fixed prefix permits it. The provisional limits are:

- 300 seconds total for each Sprint 2 smoke request, including prefill
  (owner-selected before execution; replaces the original provisional
  120-second value);
- at least 4 GiB available system RAM and 1 GiB dedicated VRAM headroom
  before launch and throughout the gate;
- no automatic context growth, no paging storm, no unbounded retry, and no
  second request in flight;
- one externally controlled cancellation test that stops backend work and
  leaves no orphan request;
- one auxiliary/compression cancellation test using the same ownership
  boundary.

These are conservative starting gates, not product promises. Inventory may
show that an arm cannot safely fit; record it as `not-run: resource gate`
instead of weakening the limit during execution. The operator retains a stop
mechanism outside the model's authority.

The owner's live Hermes timeout was three hours to accommodate historical
requests longer than five minutes. Do not alter that configuration. The pilot
deadline classifies a small request as completed or timed out; it does not
establish a universal product-latency requirement. No time or memory gate is
relaxed during an attempt.

After the smoke passes, increase context only in predeclared increments up to
the manifest cap. The run has a maximum request count and total wall time. Stop
at the first headroom, paging, host-responsiveness, cancellation, timeout, or
latency breach. A compression attempt must finish and demonstrably reduce
context before the cap; a timeout is a failed trial and the oversized history
is not retried repeatedly.

## Controlled arms

Within each fixed model/backend/configuration block:

- **A — native endpoint behavior:** Hermes sends its ordinary stable tools.
  Determine whether the chat template already applies a tool grammar; label
  this arm `native`, not automatically `unconstrained`.
- **B — static action constraint:** the same action language and budget are
  fixed for the task class.
- **C — adaptive policy:** a deterministic policy maps qualified capability,
  trusted task state, checked outcomes, and remaining budget to the next
  action language/output budget.
- **D — alternative/new decoder:** run only after A-C isolate an existing-
  engine coverage or performance gap. Model-proposed constraints are checked
  for schema validity, satisfiability, authority, and compile/size budget.

Hold model artifact, context, prompt/tool bytes, sampling/reasoning/output
limits, task corpus, and offload fixed for A-C. Counterbalance arm order to
reduce warm-cache and thermal bias. Run a cold and a warm condition explicitly.
Start with three paired repetitions as a pilot and publish all denominators;
that sample estimates variance and feasibility, not statistical certainty.
Expand repetitions only within the declared total time/resource budget.

Compare context management separately after A-C: fixed history, bounded tool-
result pruning, and qualified compression are different arms. Do not attribute
a context-policy change to constrained decoding.

## Tasks and independent checks

The initial corpus includes:

- read-only file lookup with a verifiable evidence target;
- one controlled edit with its real formatter/test;
- recovery after a failing command;
- a task that should require no action;
- native streaming tool calls; and
- a multistep artifact task with an external acceptance check.

Include synthetic hostile tool-return text to test that it cannot alter policy
or authorization in the fixture. Run full skill content only after small cases
pass. An external checker records whether the intended state changed; the
model's prose or checked final answer cannot certify its own completion.

## Measurements

Correlate every observation by session, turn, request, backend task/slot, and
arm/repetition identifier. Record:

- full input, uncached input, output, and reasoning tokens where available;
- queue time, time to first meaningful token, prompt prefill time/rate,
  decode time/rate, and total wall time;
- actual cached tokens, rendered-prefix hash where obtainable, context
  allocation, cache eviction, restart, and warm/cold status;
- tool-call shape validity, chosen action, semantic argument validity,
  authorization/check result, independent task completion, user correction,
  repeated/no-progress calls, and retry count;
- compression input/output size, duration, model/slot ownership, and outcome;
- process RSS/commit, system committed/available memory, paging/page-fault
  signal, dedicated/shared VRAM, GPU utilization/temperature, and host-
  responsiveness probe.

Missing metrics are recorded `unavailable` with the collection limitation.
The first streamed heartbeat is not necessarily the first meaningful token.
Keep prompt and generation timings separate.

## Advancement gates

Static constraints advance only if B improves valid execution or independently
checked completion over A without breaching the same resource envelope.

Adaptive policy advances only if C improves on B across paired runs without
weaker permissions, hidden retries, prompt-prefix churn, or worse stop/cancel
behavior. If evidence is inconclusive, retain the simpler static policy.

A provider plugin advances only for a demonstrated setup/capability/session-
metadata gap in the custom endpoint. A Rust sidecar advances only for a
demonstrated policy/protocol need. An in-process client advances only for a
measured boundary cost or unavailable capability.

Another constraint engine or a new decoder advances only when profiling and
coverage receipts identify a specific gap after context, template, offload,
and server configuration are controlled. A smaller qualified workload/model
or a negative result is an acceptable outcome.

## Evidence and privacy

Publish the non-secret manifest, task definitions, aggregated/per-run metrics,
failures, exclusions, and hashes needed to reproduce claims. Redact local
paths, credentials, unrelated conversation content, and tool outputs that may
contain private data. Preserve raw evidence locally with a hash and retention
note. Do not silently omit killed, timed-out, skipped, or externally
interrupted trials (L-12).
