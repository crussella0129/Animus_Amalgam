# Sprint 2 operational development ledger

Operational confidence criteria were met by attempt 11 (ended 16:19:33Z),
before any formal test ran. This is conditional † on owner ratification of
attempt-scoped time charging. The confidence text itself was written at about
16:28Z, after the first focused formal run began (about 16:21Z). Earlier
sections are the historical bring-up and repair record, preserved as written.

## Environment bring-up — 2026-09-24

- The approved plans passed the independent read-only critic and were locked.
- A disposable Python 3.11.16 environment was installed from the repository's
  existing `uv.lock`; the live Hermes environment remains untouched. The first
  attempt hit sandbox network restrictions; the authorized dependency install
  succeeded after escalation. This was setup, not a model request.
- Fresh Windows memory was about 9.1 GiB available; WSL held roughly 12 GiB.
  Guest inspection showed about 10 GiB of file cache. Releasing clean guest
  cache alone did not immediately provide sufficient Windows headroom.
- The owner explicitly approved stopping `CubiKan-S12-Fresh`. After stopping
  it, Windows available RAM rose to about 18.65 GiB. No user file/configuration
  was removed, and no other application was stopped.
- The existing `spawn_server` already creates suspended Windows children,
  attaches them to a kill-on-close Job Object, then resumes them. Reuse this
  existing Python runtime; no additional Rust supervisor crate is necessary.
- The GGUF reader exposed only aggregate weight size, insufficient for the
  frozen per-device allocation. Its existing header pass now also returns
  per-tensor byte sizes. The selected CPU FFN/embedding placement accounts for
  10,796,482,560 CPU and 5,656,961,024 GPU weight bytes; estimated 8K context
  allowance is 490,733,568 bytes. Explicit extra overhead and reserves remain.
- Production compression deliberately emits no user output cap. The lab wire
  guard records original and bounded backend requests separately and applies
  the experimental budget at the backend boundary. No global configuration
  cap is restored and no native-baseline claim is made.

Formatting/linting are bring-up checks. Formal tests remain deferred until
the real Hermes workflow and repair replays establish confidence.

## Actual attempts — 2026-09-24

All five attempts retain local events, outcomes and their immutable manifest.
The aggregate ledger currently records two model launches and zero inference
requests. Admission refusals consume an attempt number, not a launch.

| Attempt | Manifest prefix | Operation and observation | Repair / next step |
|---|---|---|---|
| 01 smoke | `977056c8c365` | GPU collector exited before admission: NVML initialization failed in the isolated environment. No launch. | Restoring only the OS `ProgramFiles` variable made the real GPU probe work; repair `0f8e4fe799`. Successful telemetry replay in 02. |
| 02 smoke | `3f8cb887b347` | Model loaded in 35.484 seconds, then the RAM/VRAM reserve predicate stopped it before any prompt. Last one-second sample had 6,016,237,568 RAM bytes and 3,638,558,720 VRAM bytes free; exact 250 ms breach RAM was not retained in this revision. Cleanup 1.485 seconds. | Backend warned that CPU tensor overrides with mmap should use load mode `none`. Repair `7b9fbe4455` also records exact reserve-breach RAM. |
| 03 smoke | `dfec2d620c88` | Admission refused: 14,183,669,760 RAM bytes available versus 17,238,933,504 required. CubiKan had restarted its WSL build. | Owner explicitly gave Amalgam priority and authorized stopping the restarted build. |
| 04 smoke | `dfec2d620c88` | Admission refused while Windows was still reclaiming WSL memory; no launch. | Windows later reported 20,503,040,000 RAM bytes available and no running WSL distributions. |
| 05 smoke | `dfec2d620c88` | Load mode `none` replay stopped after three page-in samples above 64 MiB/s. Samples were approximately 146.9, 116.6 and 1434.7 MiB/s. Last RAM/VRAM samples remained above reserves (8,790,188,032 and 4,245,684,224 bytes). Cleanup 1.000 seconds including receipt closure. No ready backend/CLI request. | Do not call this swap exhaustion or a successful load. Add page-out observation; resolve the load-phase policy below before another load. |

The previous raw paging observations cannot separate model-file reads from
pagefile reads. Microsoft's [counter guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/ram-virtual-memory-pagefile-management)
explains why paging activity alone does not establish a RAM shortage. The
fixed backend's [Windows file implementation](https://github.com/ggml-org/llama.cpp/blob/b29c606e28a01b1bc8c1351026a0fa6e616bf6c4/src/llama-mmap.cpp)
ignores its direct-I/O constructor option on Windows, so changing to `dio`
would not establish an unbuffered-load remedy here. These are diagnostic
limits, not permission to silently relax the approved gate.

Bring-up corrections also add the CLI's real interrupt API before the owned
hard stop, check backend listener closure, support an operator STOP file,
preserve existing fixtures when regenerating a manifest, and remove an
unsupported `--aggressive` option from the actual compression entry point.
These corrections still need operational replay; formatting is not coverage.

## Proposed load-phase amendment — pending owner decision

The locked plan applies the 64 MiB/s page-in stop threshold even while reading
the model for the first time. A bounded diagnostic amendment would:

- Retain every historical attempt and all aggregate launch/request/time limits.
- Observe page-in and page-out throughout the run.
- During at most the first 60 seconds of model loading only, record page-in
  spikes without making page-in alone a stop cause. Stop on page-out exceeding
  64 MiB/s for three consecutive samples, or any existing RAM/VRAM, stale
  telemetry, responsiveness, ownership or deadline breach.
- After backend readiness, restore the original page-in stop rule immediately;
  carry it through all CLI startup, main and auxiliary requests. If readiness
  is not reached within 60 seconds, the exception ends and the original rule
  applies while the existing 300-second load deadline remains.

This is a reviewable proposal, not active policy. No next load is authorized
under this amendment until the owner accepts it. Operational confidence,
useful-task execution, cancellation coverage and official suites remain pending.

## Owner continuation — 2026-09-24

The owner's “continue” in direct response to the proposed amendment approves
the bounded 60-second loading adjustment above. It now supersedes only the
load-phase page-in clause; the locked plans remain preserved as historical
approval evidence. Page-out observation and its stop predicate are active.

The old timer also charged the overnight approval wait while all lab jobs were
stopped. On resumption, retain `started`, launches, requests and every receipt,
and record the idle approval interval separately. Its conservative start is
120 seconds after the previous turn's last evidence commit (`04d40088b5`,
2026-09-24T04:44:11Z); its end is this turn's first host reading (monotonic
111250.875). Thus all earlier development time plus two minutes for final
handoff stays charged. Only the stopped, overnight human wait is excluded;
the 60-minute experiment-work allowance is not renewed. Future pauses must
be recorded explicitly at the point of handoff, never inferred by a launcher.

## Attempt 06 — load succeeds, real CLI exposes the context floor

Manifest `4f4736dcaa13aca343a9c549093fe6544642307851a6eee9a70cbd328434a5f3`
loaded the actual backend in 13.985 seconds, with one 8192-token slot. The
readiness check verified its identity. After load, a sample showed
9,339,199,488 RAM and 3,681,550,336 VRAM bytes free, with zero page-out rate.
HermesCLI then refused initialization because 8192 is below its automatic
64,000-token floor. No inference was sent. All owned processes exited and the
backend listener closed in 1.422 seconds.

`agent/agent_init.py::_enforce_minimum_context` is the actual rejection.
History (`8c12fa7cf0`) establishes that an explicit LM Studio context already
overrides the floor intentionally. The focused Amalgam repair extends that
exception only to a local custom route with an explicit matching context pin
and automatic compression disabled. The lab now pins its real 8192 capacity;
it retains the independent full-prompt 4096-token admission check. This is a
fork compatibility change for the observed operation, not evidence that all
Hermes workloads fit small windows. Replay remains required.

The next replay uses separate smoke and operational CLI processes against one
owned backend (`workflow` mode), preserving each conversation's fixed toolset
and the aggregate budget. This leaves two of the six launches for main and
auxiliary cancellation after the startup repair, rather than wasting a model
reload between the smoke and useful task.

## Attempt 07 — first real answer, background-title collision

Manifest `9ecf14193525bf430368d19cec1f6a3ef292fc76dedc779c7fe394950ac4e5a7`
replayed the context repair successfully. Real Hermes produced exactly
`AMALGAM_OK`: 1169 rendered input tokens, 6 output tokens, 71.906 seconds total,
65.984 seconds to first meaningful token. Backend prompt processing was
65.962 seconds, decode 5.913 seconds. Its first 256-token prompt batch took
57.76 seconds; subsequent batches were much faster. This does not establish
continued-session latency or useful-task completion.

Hermes then dispatched an automatic title request (267 input tokens). The
backend completed it (13 output tokens), but the smoke CLI exited and its
background connection closed while the wire relayed the response. The wire
recorded a connection reset and stopped the whole attempt, including the new
operational CLI. Four launches and two physical requests have now been used.
Both requests remain counted; the extra title is not discarded as noise.

The existing `auxiliary.title_generation.enabled: false` setting now disables
this unrelated inference in the disposable profile. No live setting changes.
The next owned backend will replay smoke, operate the fixture, then exercise
main cancellation in fresh CLI processes, leaving the last launch for actual
auxiliary cancellation. The owner observes the driver's recorded stage rather
than inferring request purpose from prompt substrings. All budgets stay shared.

## Attempt 08 — title fix succeeds; full tool prompt is too large

Manifest `0c069dc3a608fcfe7a3d646899b19b83bca040efe7c1bf9974c5052902d61c58`
replayed `AMALGAM_OK` in 10.594 seconds (1127 input tokens; first meaningful
token at 9.203 seconds), with no automatic-title inference. These fresh-session
prompts differ, and runtime/cache warmness is uncontrolled; this is not a
paired speed comparison. The operational request then rendered to 5481 tokens
and was refused before inference. Its eight exposed schemas included file
tools plus the search/describe/call bridge introduced by process management.
The fixture remained unchanged. An independent sentinel process survived the
owned cleanup. Five launches and three physical requests are consumed.

For the final authorized launch, choose the existing `terminal` toolset alone,
with tool search disabled using its existing config setting. It can perform
the same file read/edit/check/recovery task. Preserve its complete production
instructions and schemas; this changes the selection only at a fresh session
boundary, not mid-conversation, and does not trim a prompt to evade admission.
The original 4096-token input gate remains. Attempt useful work and main
cancellation; auxiliary cancellation will remain pending if the six-launch
budget is reached. Do not silently start a seventh backend.

## Attempt 09 — valid terminal action; steady-state paging stop

Manifest `dfd0151da22a7dbcf587f9d33180724342258fb4e74f2cfff6c2d3fbb40a99fd`
again produced `AMALGAM_OK`, in 10.375 seconds. The terminal-only operation
rendered to 3799 tokens and generated the valid native call
`terminal({"command":"cat settings.json"})`. The backend processed its prompt
in 28.882 seconds (131.53 tokens/second) and generated 28 tokens in 7.554
seconds. The third consecutive high global page-in sample stopped the owner
while the tool call was finishing. The command did not execute and the fixture
remained at 2. This is action-format evidence, not completed read/edit work.

At the last sample, available RAM was 9,652,416,512 bytes, available VRAM
3,624,927,232 bytes, page-in about 199.24 MiB/s and page-out zero. Across the
entire sampled attempt, minimum RAM was 9,568,813,056 bytes and maximum
page-out about 2.58 MiB/s (well below the guard). Global counters cannot assign
these page-ins to model reads, other processes or pagefile activity. A later
read-only host snapshot showed little disk reading; it does not retroactively
attribute the earlier events. Windows Performance Recorder is available and
was not recording; no host-wide trace was started.

The owner signalled the actual Hermes interrupt API, then closed its owned
jobs. All owned roots exited and the backend listener closed in 3.219 seconds.
The separately launched sentinel survived attempts 08 and 09, then the owner
explicitly stopped that sentinel. Dedicated main cancellation still needs an
active-slot check at its planned trigger; this resource stop is not substituted
for that check. Auxiliary cancellation has not run.

The six-launch budget is exhausted: nine total attempts, six backend launches,
five inference requests (three completed smokes, one title and one interrupted
terminal action). [Sanitized receipts](qualification/attempts.json) retain all
nine attempts and immutable manifests. The fixture/check/recovery workflow,
continued-session replay, formal suites and qualification verdict remain pending.

The driver now independently checks the smoke value and fixture checker before
advancing its staged workflow, and keeps its real conversation transcript in
private evidence. Previously a CLI-rendered error could return exit zero and
advance the stage label; the owner still stopped the attempt, but the label
was not completion evidence. This repair needs replay. Limits now come from
the frozen manifest rather than duplicate hardcoded request/launch/input values.

## Next bounded continuation — proposed, not active

The following changes need the owner's decision because the current launch
allowance is exhausted and the input/paging policy is explicitly fixed:

1. Permit three additional backend launches (nine cumulative). Retain eighteen
   cumulative inference requests and sixty minutes of experiment work, including
   repairs, startup and cleanup. Do not reset any used count or charge idle time
   while all lab processes are stopped awaiting this decision.
2. Increase the rendered-input ceiling from 4096 to 6144 tokens, within the same
   already-allocated 8192-token context and unchanged 128-token output ceiling.
   The minimal real prompt consumes 3799 tokens, leaving only 297 for results
   and continued work under the old ceiling. No instructions are trimmed.
3. After loading, make the existing three-sample page-in stop conditional on
   available RAM being below 8 GiB. Continue recording every page-in sample.
   The independent 4 GiB RAM, 1 GiB VRAM, three-sample 64 MiB/s page-out,
   2-second owner-lag, stale-probe and 300-second request/load stops all remain.
   This is a provisional experimental policy, not a claim that high page-ins
   are harmless; the global counter did not demonstrate memory exhaustion.

Use the first continuation launch for the useful workflow and main cancellation,
the second for real auxiliary cancellation, with the third reserved for a
diagnosed repair replay. Operational confidence still requires the actual
success evidence; approving these changes is not approving a test verdict.

## Owner continuation 2 — 2026-09-24 (agent handoff to Claude Opus 5.5)

The owner answered the proposal above with “continue” and asked for the
project direction to be checked and improved. The three proposed changes are
now active: nine cumulative launches, a 6144-token rendered-input ceiling, and
a post-load page-in stop that applies only below 8 GiB available RAM (page-in
is still recorded on every sample). All other stops are unchanged.

One accounting correction is made by the new agent and flagged to the owner:
the 60-minute allowance now charges each attempt from its start to the end of
cleanup, instead of wall time since the first launch. The allowance bounds
host exposure; diagnosis and repair with no owned lab process running carry
no host risk. Previously charged time (2836.9 seconds, including all earlier
repair time) stays charged, so about 763 seconds of attempt time remain. No
count is reset.

Direction check before the next launch: the GGUF header shows `qwen35` is a
hybrid model — 48 Gated DeltaNet recurrent layers and 16 full-attention layers
(`full_attention_interval` 4) plus one next-token-prediction layer. llama.cpp
cannot truncate recurrent state. A prompt that diverges from the cached tokens
must restore a context checkpoint at or before the divergence, or reprocess
from zero. The lab runs with `--ctx-checkpoints 0`. Continued-session turns in
the next workflow therefore show whether Hermes's re-rendered history stays
token-identical. That matters more to snowballing than any grammar setting.

## Attempt 10 — useful task, continued session and main cancellation succeed

Manifest `df1d80e16c394a1777ee19827001fe0f116999554e857aebe2dca412db9dcdb5`
(source `c42152ca0b`) used one owned backend for three fresh Hermes CLI
processes: smoke, the operational task and main cancellation.

- **Smoke:** exact `AMALGAM_OK`; 1169 input tokens, 12.0 seconds.
- **Useful task:** in one continued conversation, the real terminal toolset
  read `settings.json` and reported 2. It changed the value to 3 with a Python
  JSON rewrite and re-read the file. It then ran the real checker (`CHECK_OK`),
  ran the deliberately missing script, observed exit code 2 and recovered by
  rerunning the checker. It reported both the failure and the recovery
  truthfully. The owner's independent checker then returned exit code 0 and
  `CHECK_OK`, and the file held `{"retry_limit": 3}`. The task used eight
  inference requests and five tool executions. Rendered input grew
  from 3803 to 4543 tokens and stayed under the 6144 ceiling.
- **Cache behavior (hybrid model, zero checkpoints):** after the first cold
  3803-token prefill (29.8 s at 127.8 tokens/s), every continued request
  processed only its new suffix. Uncached prompt tokens were 40, 70, 47, 37,
  93, 124 and 37, each in about one second. Hermes's re-rendered history
  therefore stayed token-identical with thinking disabled. The rollback risk
  recorded above did not occur in this configuration. Thinking-enabled
  history is untested.
- **Where time went:** decode ran at 3.59–3.69 tokens/s. After the cold
  prefill, each agent step spent 1 s on prefill and 2–19 s on decode (7–69
  tokens). The steady-state bottleneck on this host is decode speed.
- **Main cancellation:** the trigger fired with the slot actively processing
  request 15. The graceful interrupt, owned-job close and listener closure
  completed in 2.625 s (limit 5 s). All three owned roots exited 0.
- **Resources:** minimum sampled available RAM was 5.73 GiB, minimum free VRAM
  3.02 GiB and maximum page-out 0.2 MiB/s. Twelve samples exceeded 64 MiB/s
  page-in, but no three consecutive post-load samples did, so the guard did
  not stop the attempt. The GPU peaked at 61 °C. RAM sat below the 8 GiB
  page-in-pressure line for 196 of 206 samples, so the conditional stop was
  armed for most of the run and was not merely inactive.

## Attempt 11 — auxiliary (compression) cancellation succeeds

The real `compress_now` path sent one 1875-token summary request. Production
compression sent no output cap; the wire applied the lab's 128-token limit.
The trigger fired with the slot actively processing. Hermes's own interrupt
closed the connection at 0.61 s. All owned roots exited 0 by 1.22 s and the
listener closed at 1.78 s.

## Operational confidence — criteria met by attempt 11, before formal suites

**Conditional:** this record depends on owner ratification of attempt-scoped
time charging (see the time-accounting correction below). If the owner
declines, confidence returns to pending.

**Scope of the round-2 context-floor fix:** only a served window that the
server *reports* (Ollama `num_ctx`) is compared with the pin. On llama.cpp,
the pin is operator-trusted, and the lab's readiness `n_ctx` check guards the
served window. llama-server's `/props` reported
`default_generation_settings.params.n_predict = -1` despite `--predict 128`
(attempt 13 private `server_props`), so only the per-request cap bounds output.

The plan's criteria are met by receipts that predate every official test run
in this sprint:

1. Independently checked useful-task completion (attempt 10 independent
   checker).
2. Repaired paths replayed in fresh sessions and in a continued session. The
   replays cover the explicit-context admission (06), disabled title
   inference (07) and terminal-only toolset (08). The conditional page-in
   policy (continuation 2) is an owner-approved envelope amendment, not a
   repair. Attempt 10 used three fresh CLI processes, and its
   operation was a three-turn continued conversation.
3. Main and auxiliary cancellation worked within 5 s while the backend was
   active.
4. No unresolved blocking defect. One non-blocking harness defect remains:
   the child environment omits `SYSTEMDRIVE`, so a tool created a literal
   `%SystemDrive%` directory in the fixture. It did not affect results.

Aggregate after attempt 11: eleven attempts, eight launches, sixteen inference
requests and 3125.8 charged seconds. Official unit/integration verification
begins now.

## Attempts 12–13 — live replay of the refactored harness

For the formal contract tests, `run.py`'s inline identity, admission and
paging decisions were extracted, unchanged, into `policy.py` (T-206). The
refactor was then replayed live from its own clean revision (manifest
`e1be868bc6ea4d283d38da2987d7b8dd4192e6e42ac4eff17e6422ac9d366166`).

- **Attempt 12:** identity verification and ten seconds of live baseline
  sampling ran through the extracted guard. Admission then refused the launch
  correctly: 17,090,760,704 RAM bytes were available against 17,238,933,504
  required, after Windows memory compression grew during the test run. No
  launch or request was used, and there was no automatic retry.
- **Attempt 13:** the owner closed desktop applications to free memory. The
  deliberate re-attempt loaded the backend and returned exact `AMALGAM_OK`
  (1127 input tokens, 10.5 s). Minimum sampled RAM was 8.25 GiB and page-out
  0. Owned cleanup took 1.08 s and the listener closed.

Final aggregate: thirteen attempts, nine of nine launches, seventeen of
eighteen requests and 3,209 charged seconds. The launch allowance is
exhausted, so any further live work belongs to the next sprint's envelope.

## Time-accounting correction (test critique C-020)

The second idle interval (monotonic 112853.2 → 117644.2, 4791.0 s) is labeled
in the private ledger as an owner-approval wait. It actually spans the
previous agent's handoff, an unknown owner-response delay, and the new agent's
direction review and harness edits, with no lab process running. Totals at the
end of each attempt:

| Accounting | 10 | 11 | 12 | 13 |
|---|---|---|---|---|
| Wall clock, interval 2 excluded | 3,104 s | 3,208 s | 5,359 s | 5,570 s |
| Wall clock, interval 2 charged (repairs count) | 7,895 s | 7,999 s | 10,150 s | 10,361 s |
| Attempt-scoped (introduced here, **unratified**) | — | — | — | 3,209 s total |

Under the originally approved rule ("including repairs"), all of attempts
10–13 exceed the 60-minute allowance. Only attempt-scoped charging keeps them
inside it, and the owner has not ratified that change. The checkpoint asks for
ratification. Until then, attempts 10–13 are recorded as outside the
originally approved time budget, though inside every resource and safety stop.
