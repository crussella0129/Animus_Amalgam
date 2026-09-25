# INT-0007 — Decode budget and cache-stable long local sessions

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0007
- **State:** active
- **Work evidence:** [Sprint 3 build plan](../sprints/s3/sprint-plans/build-plan.md); [T-210 to T-216, T-221 and T-222 in the Sprint 3 plan, and T-217 to T-219 in the backlog](../work/tasks.md)
- **Completion evidence:** none
- **Code evidence:** none
- **Test evidence:** none
- **Documentation evidence:** [direction review](../lineage/direction-review.md), [lessons L-15 to L-19](../lineage/lessons-register.md)

## Intent

Keep a 20–30-turn local Hermes session on the owner's RTX 2080 Ti / 32 GiB
host responsive. Control the two measured costs: tokens decoded per step, and
prefill lost when a session's cache cannot be reused. This is the snowballing
failure that started Amalgam, measured where it occurs.

The first mechanisms are existing backend and Hermes controls, not new
architecture: per-request reasoning mode and budget, the output cap,
speculative decoding with the model's own next-token layer, a fixed context
with no mid-session growth, tool-result bounds, context-checkpoint spacing,
and deterministic pruning before any model-written summary. A step-dependent
decode budget is the output-budget half of
[INT-0005](INT-0005-adaptive-action-policy.md)'s adaptive policy. This intent
qualifies whether that half pays off before any action-language work.

Boundaries and non-goals:

- Reuse the Sprint 2 lab, stop rules and owned-process boundary; never touch
  the owner's live profile.
- Do not change a conversation's system text, tool catalog or earlier
  messages mid-session. A decode-budget change must be proven not to alter
  cached prefix tokens, or it applies at a session boundary.
- No new decoder, provider plugin or policy service. Those remain gated by
  INT-0005/INT-0006 and L-14.
- No automatic model download. A different model, such as a
  mixture-of-experts checkpoint, is an owner-selected comparison arm.

## Acceptance criteria

1. On a multi-file task that accumulates real tool results over at least 20
   turns (a turn is one model request), per-turn receipts record uncached prompt tokens, decoded tokens
   (reasoning and visible separately), decode rate, wall time, independent
   completion and resource extrema.
2. Arms at the same model, context and task compare thinking off, a bounded
   reasoning budget and unbounded thinking. Each arm runs at the sampling
   configuration that screens best for its thinking mode, chosen among
   greedy decoding and the model's and vendor's recommended settings. Arms
   report decoded tokens and wall time per independently checked
   completion, including failures.
3. With the environment probe disabled (L-19), two fresh sessions render
   byte-identical system prompts, and the second reuses the first's cached
   prefix. For the hybrid `qwen35` model, a thinking-enabled continued session shows
   whether re-rendered history stays append-only. If it does not, the
   receipt identifies the divergence point and the rollback cost, and one
   repair is replayed: the existing `model.reasoning_echo` opt-in, Hermes
   history rendering, or checkpoint spacing.
4. Speculative decoding with the model's next-token layer is measured on and
   off for decode rate and output identity at temperature zero.
5. With compression enabled, deterministic pruning of old tool results runs
   before any summary request, and the session stays under its fixed context
   with no backend restart. A compression that does not reduce history
   before the cap is a failed trial.
6. The resulting default local policy is written down with its evidence. It
   is either a decode budget and settings that maximize verified throughput
   (machine time per independently verified completion, which the owner
   prefers over per-step latency), or a documented negative result naming
   the limiting resource.
7. Local-route request, load and compression deadlines derive from the
   throughput measured on the host that is running, times the work about to
   be done, with a margin. Stall windows and backstops derive from the same
   measured throughput. There are no fixed time constants, so one policy
   serves hosts of any speed. Enforcement is a stall rule (no progress within
   a window scaled to the host's measured rates) plus a worst-case backstop
   (the most work a step can contain, at this host's floor rates, times the
   margin). A slow step that keeps making progress is never stopped by time
   before that backstop. A backstop stop is a recorded failure. Receipts record predicted and actual time
   for every request. A step stopped by a stall, a host-derived backstop or
   a resource guard is a recorded failure, never a silent retry.

## Rationale

The owner's long session was dominated by decode-bound calls (1,108–1,816 s
each) and by cold prefill after eviction and restart. It stored about 15
reasoning characters per visible assistant character. Sprint 2 attempt 10
then showed the 27B completing a real tool task with thinking disabled. Warm
prefill took about one second per turn, and each step spent 2–19 s decoding
at 3.6 tokens/s. See L-15 to L-17, L-19 and the
[direction review](../lineage/direction-review.md).

Sprint 3 research located the thinking-mode cache mechanism in code.

- **Template:** the Qwen3.8 chat template re-renders every past assistant
  turn with a `<think>{reasoning_content}</think>` block by default
  (`preserve_thinking`).
- **Hermes:** Hermes strips `reasoning_content` from replayed history for
  custom routes unless `model.reasoning_echo` is set. With thinking on, the
  cached prefix therefore diverges every turn.
- **Backend:** the pinned llama.cpp build honors a per-request
  `reasoning_budget_tokens`, so step budgets need no server restart.
- **Suspected defect:** Hermes's compaction estimator ignores the echo
  opt-in. See the
  [Sprint 3 research report](../sprints/s3/sprint-research/research-report.md).

## Alternatives

- **Run the native/static grammar comparison (T-202) first.** Deferred, not
  dropped. Grammar validity does not bound decoded tokens or prefill, and the
  measured failures were cost failures. T-202 follows with decoded tokens per
  checked completion as a first-class metric.
- **Switch immediately to a smaller or MoE model.** Kept as a comparison arm.
  Replacing the owner's selected 27B without paired evidence would discard
  the baseline.
- **Raise timeouts again.** Rejected by INT-0004: waiting longer bounds
  neither resources nor history. AC7 is different. It replaces fixed ceilings
  with work-derived deadlines plus stall detection. A slow step that is making
  progress gets enough time, and a wedged one is still stopped. The original
  session's five compressions died at a fixed 600 s ceiling while still
  progressing.

## Consequences

- The next sprint measures long-session behavior directly instead of adding
  qualification ceremony.
- Some arms may be negative, for example if bounded reasoning lowers task
  completion. Those results are kept.
- A larger fixed context must be re-priced by the lab estimator before
  launch. Admission remains the gate.

## Transition history
- 2026-09-24: created as `proposed` from the Sprint 2 direction review
  requested by the owner (L-15 to L-19).
- 2026-09-24: Sprint 3 research named the thinking-mode cache mechanism and
  the existing controls (reasoning echo, per-request budget) in the Rationale
  and AC3; state remains `proposed` pending the Sprint 3 plan gate.
- 2026-09-24: during Sprint 3 planning, the owner asked for time budgets
  derived from measured throughput and the work about to be done, plus a
  safety margin, instead of fixed caps. Added AC7 and the alternatives note.
  The owner approved the Sprint 3 plan; moved `proposed` → `planned` with
  the build plan and T-210 to T-214 as Work evidence.
- 2026-09-24: after the plan critique, the owner decided four things.
  - Backstops and stall windows are host-derived, because the software must
    run on other machines of unknown speed. AC7 was reworded to remove every
    fixed time constant.
  - Sampling is an experiment axis: a screening round, then full runs of
    the winners (AC2).
  - Throughput over per-step latency is the AC6 criterion.
  - Sprint 3 takes the core (lab, deadline module, sampling and thinking
    screen, winners' full runs, echo). MTP (AC4), uncapped thinking (part of
    AC2) and the compression trial (AC5) move to Sprint 4.

  State remains `planned`.
- 2026-09-24: the plan re-review clarified two semantics without changing
  the outcome. A turn in AC1 is one model request. AC7 enforcement is a stall
  rule plus a host-derived worst-case backstop, and a backstop stop is a
  recorded failure. State remains `planned`.
- 2026-09-24: Sprint 3 plans locked after four critique rounds (final:
  proceed-with-caveats). Moved `planned` → `active` as Build began with T-215.
