# Sprint 3 Research Report

## Intents Reviewed
- [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md) — selected and revised; relevance: the sprint's primary outcome, keeping a 20–30-turn local session fast; current state: `proposed`. Research names the concrete thinking-mode cache mechanism and the existing controls for it (AC3 repair options, Rationale).
- [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) — selected; relevance: T-211 lab hardening is a stated prerequisite of T-210, and it closes Sprint 2's AC1/AC4 gaps and replays the unreplayed post-attempt-13 changes; current state: `active`.
- [INT-0005](../../../intents/INT-0005-adaptive-action-policy.md) — reviewed, not advanced; relevance: a per-step decode budget is its output-budget half. This sprint measures fixed budgets only; adaptive selection waits for that evidence; current state: `proposed`.

## 1. Sprint Goal

Operate the owner's Qwen3.8-27B through real Hermes in a session of at least
20 model requests over a multi-file task, at a larger fixed context (24–32K).
Find, repair and replay what makes long sessions slow, using existing Hermes
and llama.cpp controls only:

- reasoning mode and per-request reasoning budget;
- reasoning echo;
- next-token-prediction (MTP) speculative decoding;
- checkpoint spacing;
- deterministic pruning before any summary.

First, do the minimum of T-211 needed to make these measurements trustworthy:

- replay the post-Sprint-2 lab changes live;
- disable the environment probe;
- give each attempt a fresh home and fixture;
- record the rendered-prefix size and host condition.

No new decoder, policy service or adaptive policy is in scope.

## 2. Existing Code Survey

| File | Relevance | Notes |
|------|-----------|-------|
| `evals/local_qualification/run.py` | high | Owned backend launch, stop loop, attempt-scoped accounting. The server flags (`--ctx-size 8192`, `--predict 128`, `--spec-type none`, `--ctx-checkpoints 0`) are hardcoded and must become manifest-driven per arm. |
| `evals/local_qualification/wire.py` | high | Forces `max_tokens=128` and `enable_thinking=false` on every request. Thinking arms need both per arm. Reasoning tokens count against `max_tokens`, so 128 cannot fit thinking. |
| `evals/local_qualification/driver.py` | high | Drives `HermesCLI` with fixed prompts and `reasoning="none"`. Needs a multi-file long task, per-arm reasoning settings, and an independent checker. |
| `evals/local_qualification/policy.py` | medium | Pure admission and stop decisions. Stale, lag and time predicates are still inline in `run.py` (T-211). |
| `evals/local_qualification/prepare.py` | medium | Writes the lab config and fixtures. Fixtures are only written if absent, and the home is shared across attempts (T-211: fresh per attempt). |
| `evals/local_qualification/telemetry.py` | low | 1 s RAM/VRAM/page-in/page-out samples. Unchanged. |
| `agent/message_sanitization.py` | high | `apply_reasoning_content_policy` strips `reasoning_content` from replayed history unless the route is an echo family (DeepSeek/Kimi/MiMo) or opted in. `stale_thinking_reaches_wire` (lines 618–626) consults only the family table, ignoring the opt-in. |
| `agent/reasoning_params.py` | high | `_needs_thinking_reasoning_pad` includes `_reasoning_echo_opt_in()` (`model.reasoning_echo`), so the wire does echo when opted in. |
| `agent/context_compressor.py` | high | `_stale_thinking_on_wire` (about line 4782) uses the table-only predicate for tail walks. |
| `agent/turn_context.py` | high | `_agent_stale_thinking_on_wire` (about line 70) uses the same table-only predicate for preflight. Replayed history copies reasoning only through the echo policy (about line 1245). |
| `hermes_cli/config_defaults.py` | high | `model.reasoning_echo` opt-in (default false). Compression knobs: `threshold` 0.5, `target_ratio` 0.2, `proactive_prune_tokens` / `…_min_result_chars` / `…_min_reclaim_tokens` (deterministic tool-result pruning), `micro_compact`, `context_total_ceiling_seconds` 600. |
| `tools/env_probe.py` | high | Fail-open 10 s probe. The source of cross-session prompt variance (L-19); `agent.environment_probe: false` disables it. |
| `agent/agent_init.py` | medium | `_enforce_minimum_context` explicit-pin exception. Admits the lab's larger pinned windows unchanged. |
| `hermes_cli/local_runtime/estimator.py` | medium | `ctx_bytes` prices the Qwen3.8 context at 0.457 / 0.723 / 0.988 / 1.254 GiB for 8K / 16K / 24K / 32K. |
| `agent/transports/chat_completions.py` | medium | `extra_body` / request overrides pass through to the custom endpoint. This is the route for per-request `reasoning_budget_tokens`. |
| Qwen3.8 chat template (GGUF metadata, reported by `/props` in attempt 13) | high | See the excerpt below. It reports `supports_preserve_reasoning: true` and `supports_reasoning_effort: true`. |
| `…/hermes/runtimes/llamacpp/presets.ini` (live, read-only) | medium | The owner's live preset: 98,304 context marked "spilled", `spec-type = draft-mtp`, `spec-draft-n-max = 2`, sampling temp 1 / top-k 20 / top-p 0.95, and a vision `mmproj` projector loaded, which costs memory. |

Qwen3.8 chat template excerpt (for historical assistant turns):

```jinja
{%- if preserve_thinking is undefined or preserve_thinking is true or loop.index0 > ns.last_query_index %}
    {{- '<|im_start|>' + message.role + '\n<think>\n' + reasoning_content + '\n</think>\n\n' + content }}
{%- else %}
    {{- '<|im_start|>' + message.role + '\n' + content }}
{%- endif %}
```

**Mechanism (code-level, to be measured):**

- **Thinking off:** the model generates after an empty `<think>\n\n</think>`, and Hermes replays an empty `reasoning_content`. The two token streams match, so the prefix stays append-only, as observed in Sprint 2 attempt 10.
- **Thinking on:** the model generates real reasoning inside the think block, but Hermes strips it on replay for this custom route. The re-render then has an empty think block at the start of the last assistant turn, and the prefix diverges on every turn.
- **Why that is expensive here:** on the hybrid `qwen35` model, llama.cpp cannot truncate recurrent state. It restores the nearest context checkpoint (default 32 per slot, at least 8,192 tokens apart) or reprocesses from zero.
- **Existing repair:** `model.reasoning_echo: true`. It keeps reasoning in the context, trading context growth for a stable prefix.
- **Latent risk:** the compaction estimator ignores that opt-in, so it would undercount the tokens actually sent.

## 3. External Sources
- [llama.cpp `server-common.cpp` at the pinned backend commit](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/tools/server/server-common.cpp) — at lines 1336–1399, the per-request `chat_template_kwargs.enable_thinking` and `reasoning_effort` (where "none" disables thinking) are honored, and so is a per-request `reasoning_budget_tokens` / `thinking_budget_tokens` (with a budget message and an opt-in `reasoning_control`). A per-step decode budget therefore needs no server restart.
- [llama.cpp `server-context.cpp` at the pinned commit](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/tools/server/server-context.cpp) — covers three things: the `preserve_reasoning` template kwarg, enabled by default when supported (about lines 1480–1500); the live per-completion `reasoning_end` control that forces thinking to stop (about line 2479); and context-checkpoint creation, eviction and restore (about lines 2309–2370 and 3296–3365). Checkpoint size is logged only at trace verbosity.
- [llama.cpp `arg.cpp` at the pinned commit](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/common/arg.cpp) — covers the server-wide `--reasoning-budget` / `--reasoning-budget-message` (about line 3707), `--ctx-checkpoints` (default 32), `--checkpoint-min-step` (default 8192), and `--spec-type draft-mtp` with `--spec-draft-n-max`.

- [Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B) — the vendor's sampling guidance, which the GGUF metadata's `general.sampling` also points to.
  - Thinking mode: temperature 1.0, top-p 0.95, top-k 20, min-p 0, presence penalty 0, repetition penalty 1.0.
  - Non-thinking mode: temperature 0.7, top-p 0.8, top-k 20, min-p 0, presence penalty 1.5, repetition penalty 1.0.
  - The card does not explicitly warn against greedy decoding.

## 4. Risks, Unknowns, Dependencies
- **Risk — host headroom:** RAM admission needs 16.06 GiB, and 16.07 GiB was available at research time, with no margin. A 32K context and MTP draft state add VRAM (about 0.8 GiB of margin at 32K before MTP). Admission may refuse; do not stop the owner's applications without asking.
- **Risk — thinking latency:** at about 3.6 tokens/s, 500 reasoning tokens take about 140 s. An unbounded-thinking arm will hit the 300 s request cap. That is a valid negative datum, not a harness failure. Reasoning tokens also count against `max_tokens`, so thinking arms need a larger per-arm output cap.
- **Risk — latent estimator mismatch:** with `reasoning_echo` on, preflight and tail walks both undercount the wire prompt, which risks late compaction or overflow. Expect to find it by operating, and repair it at its source (`stale_thinking_reaches_wire` must honor the opt-in).
- **Risk — sampling:** the owner's live sampling (temperature 1) matches the vendor's thinking-mode guidance. Greedy decoding is common for comparability, but it may behave differently in thinking mode. Planning resolved this as a seeded screen over greedy and the vendor settings (see the revisions below).
- **Unknown:** whether the template's `reasoning_content|trim` re-render is byte-identical to the generated think block. Newline handling decides whether echo fully restores append-only prefixes.
- **Unknown:** recurrent-state checkpoint size (it drives RAM cost as spacing gets denser). Measure it at trace verbosity.
- **Unknown:** MTP acceptance rate and output identity at temperature 0 on this build.
- **Dependency:** a fresh lab home per attempt, and `agent.environment_probe: false`, or cross-session comparisons stay invalid (L-19).
- **Dependency:** owner approval of the sprint envelope (launches, requests, charged time), and ratification of attempt-scoped charging, which Sprint 2 left conditional.
- **Dependency (optional arm):** any mixture-of-experts comparison model requires an owner download decision. It is not assumed.

## 5. Recommended Approach
Primary: reverse-E2E on the Sprint 2 lab, extended minimally.

1. **Make the settings manifest-driven.** Context, output cap, thinking mode,
   reasoning budget, reasoning echo, speculative type and checkpoint spacing
   are frozen per arm in the manifest. Each attempt uses a fresh home and
   fixture, the environment probe is off, and the rendered prefix and host
   condition are recorded.
2. **Replay first.** On the first launch, replay Sprint 2's post-attempt-13
   changes and prove byte-identical smoke prompts across two fresh sessions.
3. **Run a long task.** Build a multi-file fixture (a small package with
   several defects and a test runner) that needs at least 20 model requests
   in one conversation. An independent checker judges completion.
4. **Operate the arms**, repairing and replaying failures between attempts:
   - thinking off at 24–32K (baseline);
   - thinking on without echo (expect a rollback every turn; measure the
     uncached tokens);
   - thinking on with `model.reasoning_echo: true` (expect append-only; watch
     the estimator);
   - a bounded per-request `reasoning_budget_tokens`;
   - MTP on for the best arm;
   - compression enabled with `proactive_prune_tokens`, so the long session
     crosses its threshold.
5. **Formal tests last.** Run official tests only after operational
   confidence, targeting the defects found.

Alternative considered: implement INT-0005's adaptive per-step policy now.
Deferred. Choosing an adaptive budget needs the fixed-arm evidence first, and
the footprint ladder prefers existing configuration and request fields over
new surface.

Rationale: the evidence locates the cost in decoded tokens and cache loss.
Existing controls (`reasoning_echo`, per-request reasoning budgets, MTP,
checkpoint spacing, proactive pruning) can each be exercised without new
architecture. The one suspected defect has a precise source location.

## Revisions after planning (2026-09-24)

The owner's planning decisions changed three recommendations:

- MTP, uncapped thinking and the compression trial move to Sprint 4 (backlog T-217 to T-219).
- Sampling becomes a seeded screen rather than fixed temperature 0.
- Every time limit derives from measured host throughput, with no fixed seconds.

Pinned-source note (`server-context.cpp`): the `prompt_progress` start event (about lines 3416–3420) and the per-batch events (about lines 3805–3809) are sent only when both `stream` and `return_progress` are true. The lab therefore forces streaming upstream.

## Artifacts
None saved separately. The evidence is linked inline: the pinned llama.cpp
sources, the template excerpt taken from the attempt-13 `server_props` record
(private receipt fingerprinted in Sprint 2 `attempts.json`), and the Hermes
source locations in the survey.
