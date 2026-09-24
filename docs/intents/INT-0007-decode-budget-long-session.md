# INT-0007 — Decode budget and cache-stable long local sessions

<!-- sprint-loop-intent-v2 -->
- **Intent ID:** INT-0007
- **State:** proposed
- **Work evidence:** none
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
   turns, per-turn receipts record uncached prompt tokens, decoded tokens
   (reasoning and visible separately), decode rate, wall time, independent
   completion and resource extrema.
2. Arms at the same model, context and task compare thinking off, a bounded
   reasoning budget and unbounded thinking. They report decoded tokens and
   wall time per independently checked completion, including failures.
3. With the environment probe disabled (L-19), two fresh sessions render
   byte-identical system prompts, and the second reuses the first's cached
   prefix. For the hybrid `qwen35` model, a thinking-enabled continued session shows
   whether re-rendered history stays append-only. If it does not, the
   receipt identifies the divergence point and the rollback cost, and one
   repair (Hermes history rendering or checkpoint spacing) is replayed.
4. Speculative decoding with the model's next-token layer is measured on and
   off for decode rate and output identity at temperature zero.
5. With compression enabled, deterministic pruning of old tool results runs
   before any summary request, and the session stays under its fixed context
   with no backend restart. A compression that does not reduce history
   before the cap is a failed trial.
6. The resulting default local policy is written down with its evidence. It
   is either a decode budget and settings that keep the long session within
   the owner's latency tolerance, or a documented negative result naming the
   limiting resource.

## Rationale

The owner's long session was dominated by decode-bound calls (1,108–1,816 s
each) and by cold prefill after eviction and restart. It stored about 15
reasoning characters per visible assistant character. Sprint 2 attempt 10
then showed the 27B completing a real tool task with thinking disabled. Warm
prefill took about one second per turn, and each step spent 2–19 s decoding
at 3.6 tokens/s. See L-15 to L-17, L-19 and the
[direction review](../lineage/direction-review.md).

## Alternatives

- **Run the native/static grammar comparison (T-202) first.** Deferred, not
  dropped. Grammar validity does not bound decoded tokens or prefill, and the
  measured failures were cost failures. T-202 follows with decoded tokens per
  checked completion as a first-class metric.
- **Switch immediately to a smaller or MoE model.** Kept as a comparison arm.
  Replacing the owner's selected 27B without paired evidence would discard
  the baseline.
- **Raise timeouts again.** Rejected by INT-0004: waiting longer bounds
  neither resources nor history.

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
