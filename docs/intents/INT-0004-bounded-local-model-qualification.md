# INT-0004 — Bounded local-model qualification

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0004
- **State:** active
- **Work evidence:** [Sprint 2 build plan](../sprints/s2/sprint-plans/build-plan.md); [operational repair ledger](../sprints/s2/sprint-tests/operational-ledger.md); [T-201 to T-209 completions](../work/completed-tasks.md); [T-202 and T-211](../work/tasks.md)
- **Completion evidence:** none
- **Code evidence:** [operational lab](../../evals/local_qualification/README.md); [explicit local context admission](../../agent/agent_init.py)
- **Test evidence:** [Sprint 2 live E2E results](../sprints/s2/sprint-tests/e2e-tests.md); [Sprint 2 unit results](../sprints/s2/sprint-tests/unit-tests.md); [Sprint 2 integration results](../sprints/s2/sprint-tests/integration-tests.md)
- **Documentation evidence:** [evaluation protocol](../lineage/local-evaluation-protocol.md); [operational ledger](../sprints/s2/sprint-tests/operational-ledger.md); [direction review](../lineage/direction-review.md)

## Intent

Qualify a useful local Hermes baseline on the owner's RTX 2080 Ti and 32 GiB
system-RAM host before implementing adaptive policy. The first run uses a
separately launched, fixed-context llama.cpp server through Hermes's existing
custom provider and an isolated profile. It compares the endpoint's native
tool behavior with a static constrained action protocol at the same model and
resource settings.

The owner selected the existing Qwen3.8-27B artifact as the first pilot and
300 seconds as its total request deadline on 2026-09-23. The owner also
explained that the live Hermes configuration allowed three hours because
some historical requests exceeded five minutes. The pilot deadline bounds
this small experiment; it is not a claim about all acceptable product latency
and does not change that live configuration. The smaller local 7B artifact
remains a possible later comparison, not an automatic fallback.

Development follows the owner's reverse-E2E workflow: operate actual Hermes
in a disposable environment, reproduce failures while doing useful work,
make focused repairs, and replay the failed operation. Official unit and
integration suites follow demonstrated operational confidence. A growing
fixture suite or a synthetic response alone cannot substitute for operating
the system. Basic build checks and a practical stop-control check are part
of bringing up the environment, not a suite-first development gate.

Boundaries and non-goals:

- Do not modify or replay against the owner's default/live Hermes profile.
- Do not allow managed context growth, weaken a stop gate during a run, or
  treat a longer timeout as increased capacity.
- Do not label native tool behavior unconstrained until the template's actual
  grammar is established.
- Do not claim AACD, general model quality, or a decoder improvement from this
  baseline. This intent qualifies the operating envelope and static control.

## Acceptance criteria

1. A non-secret manifest records the exact model/tokenizer/template hashes,
   backend/build features, context/slot/cache/offload settings, Hermes commit,
   stable toolset/prefix size, sampling/output limits, host condition, task
   corpus, and the owner's model-priority/latency choice.
2. A fixed-context smoke gate proves server identity/context, one-request
   ownership, external cancellation, auxiliary/compression cancellation, and
   the protocol's provisional time/RAM/VRAM headroom gates before any longer
   trial. A model that cannot fit is recorded `not-run: resource gate`.
3. Native and static-constraint arms run as paired cold/warm trials with model,
   rendered prompt/tool bytes, sampling, offload, context, tasks, and budgets
   held fixed. At least three pilot repetitions publish all denominators,
   failures, exclusions, and uncertainty; three trials are not represented as
   statistical qualification.
4. Receipts correlate request/slot identity with input/uncached/output tokens,
   meaningful-first-token, prompt/decode/total timing, actual cache reuse,
   action/argument validity, independent completion, retries, RAM/VRAM/paging,
   host responsiveness, and stop/cancel behavior. Missing metrics are explicit.
5. Context/pruning/compression trials are a separate axis. They preserve
   tool/result groups and checked evidence under a tokenizer-aware budget.
   Compression must complete and reduce history before the cap; a timeout is a
   failed trial and does not trigger repeated retries of the oversized history.
6. Static constraints advance only if they improve valid execution or
   independently checked completion without exceeding the same resource and
   authority envelope. A negative or smaller-workload result is acceptable.
7. Development evidence records the actual operation, observed failure,
   diagnosis, repair revision and replay outcome. Formal unit/integration
   testing follows successful operation and repair replay in the isolated
   environment; regression coverage targets observed failures and essential
   contracts. Resource-blocked operation remains unproven, not replaced by
   passing mocks or declared operational confidence.

## Rationale

The local case shows high-cache long generation and separate cold-prefill
cliffs after cache pressure, context growth, and restart. Grammar constraints
cannot diagnose those costs. Lessons
[L-04, L-07 through L-09, L-12, and L-13](../lineage/lessons-register.md)
require independent correctness/resource measures, group-preserving
token-aware compaction, faithful cache evidence, honest failures, and a
cancellable process boundary.

## Alternatives

- **Begin with the 27B model at the largest declared context.** Rejected:
  the supplied run lost host responsiveness and did not establish a safe
  envelope. The owner's selected 27B-first pilot instead uses a small fixed
  context and the same memory/cancellation gates.
- **Use Hermes's managed local runtime and lower compression settings.**
  Rejected for qualification because managed growth occurs before compression
  and would change the tested allocation.
- **Increase timeouts and repeat the original session.** Rejected: the run
  already shows that waiting longer neither bounds resources nor makes failed
  compression reduce history.

## Consequences

- No adaptive-policy implementation starts until this baseline supplies a
  reproducible static control and safe operating envelope.
- The selected first model may be smaller than the best-quality candidate.
- Fixed-context isolation gives up managed-runtime convenience in exchange for
  a stable experiment boundary.
- Focused repairs to reproduced Hermes integration defects are in scope;
  architecture expansion still requires its own evidence and intent. Keep
  exploratory repair runs separate from the frozen comparative trials.

## Transition history
- 2026-09-23: created as `proposed` from Sprint 1 lessons L-04, L-07, L-09, L-12, and L-13.
- 2026-09-23: Sprint 1 test review made L-08's group-preserving,
  tokenizer-aware compaction boundary explicit in acceptance criterion 5 and
  the rationale; state remains `proposed`.
- 2026-09-23: owner selected existing Qwen3.8-27B first and a 300-second
  pilot request deadline, with historical three-hour live timeouts retained
  as context. Updated priority and latency boundaries; state remains
  `proposed` pending the Sprint 2 plan gate.
- 2026-09-23: owner clarified reverse-E2E development order: operate an
  isolated system, encounter and repair failures, replay, then run official
  unit/integration suites. Added AC7; state remains `proposed`. This changes
  the draft workflow, not the authority to start inference before plan approval.
- 2026-09-24: owner approved the revised reverse-E2E Sprint 2 plan with
  “ok now continue”; moved `proposed` → `planned`, linked work evidence.
- 2026-09-24: clean independent plan review and canonical lock completed;
  moved `planned` → `active` as the isolated-environment build began.
