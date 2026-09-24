# Direction review after Sprint 2

Written 2026-09-24 at the owner's request to confirm that Amalgam was taken in
a good direction, or to improve it. Evidence: the
[long-session case study](local-session-case-study.md), the
[Sprint 2 operational ledger](../sprints/s2/sprint-tests/operational-ledger.md)
and its [sanitized receipts](../sprints/s2/sprint-tests/qualification/attempts.json).

## Verdict

- **Strategy: sound, keep it.** Keep Hermes's custom endpoint in front of a
  fixed llama.cpp server. Add a narrow policy service only for a measured gap,
  and add no new decoder without a profiled engine gap (L-14). Nothing
  measured in Sprint 2 argues for a decoder.
- **Sprint 2 execution: overbuilt, now corrected.** Nine attempts produced one
  unexecuted tool call. The main causes were a miscalibrated paging stop and
  per-attempt owner approvals. After the fixes, two launches produced the
  useful task, a continued session and both cancellations.
- **Next priority: change it.** The measured costs are decoded tokens and
  cache-loss events, not malformed actions. The next sprint should attack the
  decode budget and long-session cache stability before the native/static
  grammar comparison.

## What held up

- Sprint 1's diagnosis named context growth, cache pressure, eviction,
  restart cold prefill and failed compression, and held that timeouts are not
  capacity. Attempt 10 corroborates it. With a fixed context, one slot, no
  host prompt cache and no growth, the same 27B completed a three-turn tool
  task. Each continued turn prefilled only its 37–124 new tokens, in about one
  second.
- The safety envelope addresses the near-crash mechanism at no measurable
  cost: owned Job Objects, RAM/VRAM reserves, one slot, `--cache-ram 0` and a
  fixed context.
- Operating the real system found real defects that a mock matrix would not:
  the 64K context floor, a background title request, and a tool surface too
  large for the window.

## What went wrong, and the corrections

| Problem | Evidence | Correction |
|---|---|---|
| The global page-in counter stopped healthy runs. It also counts file and executable-image reads. | Attempts 05 and 09 stopped with RAM ≥ 8.7 GiB available and page-out ≈ 0. | Page-in stops only below 8 GiB available RAM. Page-out, reserves, staleness and deadlines stay unconditional. This is tested in `tests/evals/test_local_qualification_policy.py`. |
| The experiment clock charged repair time, and every limit change waited on the owner. | Three owner stops, including an overnight wait, across eleven attempts. | Each attempt is charged from start to end of cleanup. Repairs with no model loaded carry no host risk. |
| The 4096-token input ceiling left 297 tokens beyond the fixed prompt. | The terminal-only prompt is 3799 tokens. | The ceiling is now 6144 inside the same 8192 context. The task peaked at 4543. |

## Where the time actually goes

| Source | Observation |
|---|---|
| Original session, decode | Calls 6, 17 and 21 spent 1,108, 1,816 and 1,745 s decoding. Call 21 decoded at 1.51 tokens/s. Stored reasoning was 99,692 characters against 6,605 visible assistant characters, about 15:1. |
| Original session, cache loss | Three cold prefills took 4,830, 5,750 and 9,733 s, after eviction and the 64K→96K restart. |
| Original session, compression | Five attempts of about 600 s each; none reduced history. |
| Attempt 10 (thinking off, 8K) | Cold prefill ran at 127.8 tokens/s. Warm prefill took about 1 s per turn. Decode ran at 3.6 tokens/s, so a step took 2–19 s. Model time for the whole three-turn task was 136 s, excluding tool execution. |

Implications, in priority order:

1. **Decoded tokens are the steady-state cost.** On this host, a dense 27B with
   CPU-resident FFN weights costs about 0.28 s per generated token. Routine
   tool steps completed correctly with thinking disabled. A per-step decode
   budget is the cheapest large win: no reasoning for routine tool steps,
   bounded reasoning for planning. This is the output-budget half of
   [INT-0005](../intents/INT-0005-adaptive-action-policy.md)'s definition
   of adaptive policy. It needs neither a decoder nor the native/static
   comparison first.
2. **Constrained decoding pays off in fewer tokens, not only valid ones.** A
   step that may only emit a call from a small grammar has no room to
   deliberate first. Report decoded tokens per checked completion next to
   validity in every constraint trial.
3. **Hybrid-model cache stability is untested with thinking enabled.**
   `qwen35` has 48 Gated DeltaNet recurrent layers and 16 attention layers.
   llama.cpp cannot roll recurrent state back. It restores a checkpoint
   instead, and build b10964 defaults to 32 checkpoints spaced at least 8,192
   tokens apart. Thinking-off history stayed token-identical in attempt 10.
   If thinking-on history re-renders earlier turns differently, for example
   by dropping old reasoning, each user turn could roll back up to about 8K
   tokens and re-prefill them. Call 17 (78% reuse, 1,028 s prefill) is
   consistent with that but does not prove it. Test it directly.
4. **Make the system prompt byte-identical across sessions.** The same smoke
   rendered to 1169 or 1127 tokens depending on whether Hermes's fail-open
   environment probe beat its 10 s deadline on a busy host. That varies a line
   near the start of the prompt, so a new session re-prefills about 3.8K tokens
   (about 30 s) instead of reusing the previous session's prefix. Set
   `agent.environment_probe: false` for local profiles (L-19).
5. **Never grow the context or restart the slot mid-session.** Bound tool
   results where they enter the conversation. Prune deterministically before
   summarizing: a local summarizer decoding at 1.5–5 tokens/s cannot write a
   long summary within a deadline.
6. **Model and runtime choice can outweigh policy.** Two one-flag experiments
   on the same harness could multiply decode speed. One is multi-token
   speculative decoding: this 27B ships one next-token prediction layer, and
   the live configuration used it. The other is a mixture-of-experts model
   with few active parameters and its experts in system RAM (`--n-cpu-moe`).
   The owner chooses any new model download.

## Recommended next sprint

The goal is to keep a 20–30-turn local session fast, on the same harness and
stop rules:

- a longer multi-file task that accumulates real tool results;
- a larger fixed context, priced by the lab estimator before launch (it prices
  8K at about 0.47 GiB);
- arms: thinking off, thinking bounded and thinking on; speculative decoding
  on and off; default and denser checkpoint spacing;
- per turn: uncached prompt tokens, decoded tokens, decode rate, wall time,
  independent completion and resource extrema;
- compression enabled with deterministic pruning first, judged by whether it
  reduces history before the cap.

Then run T-202 (native vs static constraints), with decoded tokens per checked
completion as a first-class metric. Process change: approve the envelope once
and let the lab iterate inside it. Only a new resource class, such as a larger
model, more memory or a new download, returns to the owner.
