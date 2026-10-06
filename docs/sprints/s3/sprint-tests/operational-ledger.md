# Sprint 3 operational development ledger

The reverse-E2E record for Sprint 3. Each entry runs failure → diagnosis →
repair → replay, in the order it happened. The lab runs on the rebuilt
environment from the 2026-10-03 reset (`docs/sprints/s3/sprint-meta.md`). Its
lab root is outside the repository, and it records private evidence there.

## Attempt 01 — C1 replay: a dirty tree refuses launch (2026-10-03)

Manifest `calibration-9564a7815796` was frozen at clean `e4b2b7df1b`. A
deliberate untracked file was then added. The run refused with "source
revision differs from frozen candidate". It consumed 0 launches and charged
8.9 s. The probe file was removed, and the tree was clean again before
attempt 02.

## Attempt 02 — first live calibration: a 30× prefill collapse and a blocked supervisor

**Failure.** The backend loaded in 47.0 s. The first smoke request (1167
input tokens) received one progress event (`processed 0`) and then nothing.
The rule stopped it as "stall in prefill (window 47.0s)". Session 2 then
stopped the attempt with "supervisor scheduler lag exceeded two telemetry
periods", with a maximum lag of 14.9 s. Totals: 1 launch, 1 request, 163.6 s
charged, cleanup 2.9 s, listener closed.

**Diagnosis 1 — prefill speed.** The backend logged the first 256-token batch
at 59.97 s, which is 4.27 tok/s. Sprint 2 measured about 120 tok/s on this
host and binary. GPU utilization stayed at the desktop's idle 17–23%.

Five candidate causes were ruled out by measurement:

- **The host:** PCIe ran Gen3 ×16, and the driver was 596.49 in both
  sprints.
- **The model and binary:** their hashes match Sprint 2.
- **RAM pressure:** a diagnostic run hit the same 6.2 GiB available RAM and
  stayed fast.
- **The launch flags:** an owned diagnostic launch with Sprint 2's flags
  prefilled at 111 tok/s. One with Sprint 3's exact flags (32K context, 4
  checkpoints, `-lv 4`) prefilled at 115 tok/s, at 13–15 GB/s PCIe and 99% GPU
  utilization.
- **The request body:** it was ordinary greedy sampling.

The real difference was the backend's environment. The lab spawned
llama-server with the attempt's fresh `APPDATA`, so the NVIDIA driver started
from an empty kernel JIT cache. That attempt's fake home held a new 98 MB
`NVIDIA/ComputeCache`.

Reproduced: with a cold `CUDA_CACHE_PATH`, load took 48.6 s (against 18.2 s
warm), prefill ran at 15.6 tok/s (against 115) and decode at 1.09 tok/s
(against 3.6). The cache grew continuously during load and through the first
request, to 103 MB, with the backend at about one CPU core and the GPU idle.
The cause was Sprint 3's fresh-state-per-attempt rule (T-211) treating
driver state as agent state. Sprint 2 reused its state.

**Diagnosis 2 — supervisor lag.** After the stall stop, `Wire.cancel_active()`
called `HTTPConnection.close()`. That closes the response's buffered reader,
which waits for the reader lock held by the handler thread blocked in
`readline()`. The supervisor therefore froze until the backend finished its
60 s batch. Two waits also skipped `observe()`: the grace wait and the
post-cancel settle loop. Synchronous `/slots` probes have the same effect,
because llama.cpp answers them only between batches. The attempt was stopped
by its own supervisor, not by the host.

**Repair** (lab only):

- **Kernel cache:** the backend uses a lab-level kernel cache
  (`CUDA_CACHE_PATH=<lab>/kernel-cache`, `CUDA_CACHE_MAXSIZE` 4 GiB), so the
  compile cost is paid once per lab and driver, not once per attempt.
- **Growth as progress:** kernel-cache growth counts as progress for the
  load-stall and request-stall rules. Compiling is the backend working with no
  stream or slot signal.
- **Clean rate samples:** a request that grew the cache is marked
  `kernel_compiled`, and both the calibration and the rate tracker exclude it.
  Compile time is not throughput.
- **Non-blocking cancel:** cancel shuts the upstream socket down instead of
  closing it. A lab cancel is recorded as `response_cancelled`, never as a
  wire failure.
- **Observing waits:** every supervisor wait runs through one helper that
  keeps `observe()` going. The next session's slot erase waits, while
  observing, until the slot settles. The cancel record uses the poller's last
  `/slots` snapshot instead of a blocking probe.

**Product finding (for T-213/T-219, not repaired here).** A client machine
pays this compile cost on its first launch and after every driver update: a
30× slower first prompt and a 2.5× slower load. Host-derived deadlines must
not treat that first launch as the host's steady state. Kernel-cache growth
is the observable that separates the two.

**Diagnostic launches.** The bisection used 4 owned diagnostic launches
outside the lab: a scratch script with the same binary and model, a Job
Object, an admission check and a 4 GiB RAM kill-guard. One of the 4 ran with
an unintended warm cache because of a quoting slip. They count against the
approved envelope's 12 launches, so 5 of 12 are used (attempt 02 plus 4
diagnostics). Each diagnostic sent 1 request (4 of 400).

## Attempt 03 — calibration replay refused at admission (2026-10-03)

Manifest `calibration-b722f9301e22` was frozen at repair `714f5afd4f`.
Admission measured 14.76 GiB available RAM against the 16.06 GiB needed;
VRAM was sufficient (8.80 GiB free, 8.52 needed). The owner's applications
had reopened since the 16.75 GiB reading. The attempt made no launch and was
charged 26.7 s. The owner was asked to free memory. No owner process was
touched.

## Attempt 04 — calibration replay succeeds; C3 misses for lab reasons

Manifest `calibration-f8e1dc85710a` was frozen at `f09d3863a0` and admitted
at 16.84 GiB available RAM. The lab kernel cache started empty, so this
attempt also tested the attempt-02 repair against a cold cache.

- **Load:** 45.4 s. The driver compiled 46.8 MB of kernels during load. Cache
  growth counted as progress, and the load-stall rule did not fire.
- **Smoke 1:** exact `AMALGAM_OK` in 74.8 s. It compiled another 60.9 MB of
  kernels and was marked `kernel_compiled`, so it was excluded from rate
  samples. The stall rule did not fire.
- **Smoke 2 (warm):** exact. 1167 tokens at 96.7 tok/s prefill and 3.48 tok/s
  decode; 13.6 s.
- **Decode sample:** exact 1–40. 111 tokens at 3.52 tok/s.
- **Main-cancel (C4):** the lab cancelled at the first decoded token, which
  recorded `response_cancelled`, not a wire failure. The slot was idle 0.84 s
  later; owned cleanup took 0.88 s and the listener was closed. The maximum
  supervisor lag was 0.38 s, against 14.9 s in attempt 02.

**C2 — calibration record** (`<lab>/calibration.json`):

| Field | Value |
|---|---|
| `P` (prefill) | 96.76 tok/s |
| `D` (decode) | 3.55 tok/s |
| `O` (first progress event) | 0.024 s |
| `T_load` | 45.4 s, cold kernel cache (a warm load measured 18–22 s) |
| `T_cli` | 3.05 s |
| `hash` | 8.9 s |
| Checkpoint size | 149.6 MiB (156,894,232 bytes) |
| Frozen checkpoints | 5 |
| Sprint budget | **81,365 s** |

The sprint budget is the locked T-215 formula: margin × the planned
attempts. It is cap-bound, because each planned request is priced at its
full 768-token output cap at `D`. That makes it a worst-case
stop-and-report backstop, not a forecast. Sprint 2's real agent steps
decoded 7–69 tokens each.

**Calibration defect, repaired without a launch.** `write_calibration` was
called with the last post-load sample instead of the admission sample. RAM
headroom therefore read negative, and 0 checkpoints were frozen. The repair
(`32a1d3342b`) recomputed the record from attempt 04's own recorded evidence
at `a5413bc376`. The headroom was 0.789 GiB, so 5 checkpoints were frozen.
No measurement changed. The original record is kept as
`calibration-attempt04-postload-sample.json`.

**C3 — missed, for lab reasons.** The two smokes' rendered system prompts
had equal length (1167 tokens) but were not byte-identical. They differed
only in the lab's per-session paths (home, working directory and the
scratch directory Hermes names). The slot was also erased before smoke 2, so
`cache_n` was 0. Neither cause is Hermes behavior. Repair (`32a1d3342b`):

- Every session runs at fixed `<attempt>/live` paths, then closes its
  process tree and is archived.
- Slot erase is a per-session plan field. The calibration plan's second
  smoke keeps the slot.

The replay is the first two sessions of the screen attempt (a smoke, then a
smoke that keeps the slot), which spends no extra launch.

**Envelope:** 6 of 12 launches used (attempts 02 and 04, plus 4
diagnostics) and 9 of 400 requests.

## Attempt 05 — first screen: C3 and L3 pass, then a telemetry read race

Manifest `screen-db734edd4a4a` (`2c07cc0689`), with 5 frozen checkpoints and
784 MB of checkpoint RAM in admission. Admitted at 16.94 GiB. The load took
**14.3 s** on the warm lab kernel cache, against 45.4 s cold in attempt 04.

**C3 — passed (replay of attempt 04's miss).**

- The two smokes' rendered prompt, system and tool hashes were
  byte-identical (`cfc15bdd…`, `4a126f5b…`, `74234e98…`).
- The second smoke kept the slot. It reused **1147 of 1151** prompt tokens
  from cache, processed 4 and finished in 2.5 s, against 12.9 s cold.
- Both answers were exact.

**L3 — passed live**, measured with Hermes's real system prompt and
terminal tool:

| Check | Measured | Limit |
|---|---|---|
| Reference requests | 22 | at least 20 |
| Largest reference edit | 179 tokens | the smallest cap, 512 |
| Peak rendered prompt + worst-case echoed reasoning | 6,889 + 5,632 tokens | the input ceiling, 31,488 |

**First long session (off-greedy).** The opening request prefilled 3,709
tokens cold at 126 tok/s and emitted a valid terminal call in 47 tokens.
The second request reused 3,755 cached tokens and processed only 243.
History stayed append-only with thinking off.

**Failure.** The third request was in flight when the supervisor stopped
with `PermissionError: [Errno 13] Permission denied: …\sample.json`. The
resulting cleanup aborted the in-flight request (`wire_failure`
ConnectionAbortedError). Cleanup took 2.2 s, all 5 owned roots exited and the
listener was closed. Totals: 3 lab requests and 616.998 s charged
cumulatively.

**Diagnosis.** `telemetry.py` publishes each sample with `os.replace`. On
Windows, opening a file while it is being replaced fails with a sharing
violation. The supervisor reads 4 times a second, the writer replaces once a
second, and over about 10 minutes the race hit once. The reader has had this
race since the lab's first commit (`1f6abe7eca`); Sprint 2's shorter attempts
never hit it.

**Repair.** A sharing violation on read means "no new sample this tick". The
supervisor keeps the last sample, and the existing staleness rule (more than
3 telemetry periods) still bounds how long telemetry may be unreadable.
`publish.py` now also names `id_slot` and `finish_reason` when missing: the
pinned llama.cpp's OpenAI-compatible stream carries no `id_slot`.

**Envelope:** 7 of 12 launches (lab attempts 02, 04 and 05, plus 4
diagnostics) and 14 of 400 requests (10 lab and 4 diagnostic).

## Attempt 06 — the sampling screen completes (S1–S3)

Manifest `screen-f55beeb3380c` was frozen at `c9bcb37a55` and admitted at
16.96 GiB. The load took 18.5 s on the warm kernel cache. The attempt ran
11 sessions and 78 requests with no stop. The maximum supervisor lag was
0.56 s, and cleanup took 0.95 s. Charged time for this attempt was 4,179 s.

**Replays.** C3 passed again: both smokes were exact, and the second
reused the first's cached prefix. L3 passed on the first long request.

**Screen.** Each configuration ran user turns 1–3 in a fresh home and
fixture, with the slot erased first, at seed 42. These are **single seeded
screening runs, not evidence of statistical superiority** (S3).

| Configuration | Session | Verified | Machine time | Decoded | Requests | Note |
|---|---|---|---|---|---|---|
| off-greedy | 3 | 1/4 | 259 s | 690 | 7 | **off winner** |
| off-model-default | 6 (7) | 1/4 | 319 s | 871 | 10 | 7 is a surplus replicate: identical tokens, 322 s |
| off-vendor | 4, 5 | 1/4 each | 433 s, 393 s | 1,242, 1,117 | 10, 9 | contaminated twice, so a failure |
| on-greedy | 8 | 1/4 | 515 s | 1,499 | 8 | **on winner** |
| on-vendor (= model default) | 9 | 1/4 | 521 s | 1,638 | 7 | |
| on-mid-probe | 10 (11) | 1/4 | 549 s | 1,621 | 7 | report only, not selectable |

Every configuration fixed exactly what turn 3 asks for. The S2 ranking
(verified, then machine time per verified item, then decoded tokens)
selects `off-greedy` and `on-greedy`. These are recorded in `arms.json`
`screen_winners`. Neither mode is inconclusive. The off-mode choice does not
depend on the contamination rule: off-vendor ranked last on time per item
even before the failure was counted.

**Thinking on, echo off, cost little in cache.** The median uncached prompt
tokens per continued request was 56–144 with thinking off, and 245–292 with
thinking on and no echo. The pinned llama.cpp creates a context checkpoint
just before each generation. So the stripped reasoning only re-renders the
last assistant turn: about 200 extra tokens per turn, not a full
reprocess. Thinking roughly doubled machine time for the same verified
result (515 s against 259 s). The 256-token reasoning budget was enforced:
reasoning capped at 255 tokens.

**Determinism.** Sessions 6 and 7 used temperature 1.0 and decoded identical
token counts. Seed 42 plus byte-identical prompts (the C3 repair) makes even
stochastic sampling replay exactly, so same-seed replicates are not
independent samples. The mid-probe pair (10 and 11) did diverge, decoding
1,621 and 2,248 tokens.

**Prediction accuracy (O5, partial).** Across 70 requests, predicted over
actual seconds (after the rearm) had a median of 5.3, a minimum of 1.34 and
a maximum of 57. The predictor never under-predicted. It prices each request
at the full output cap, which makes it a safe bound but not a forecast.

**Failures, diagnoses and repairs** (`1850994283`, plus the scanner fixes
below, committed with the screen results):

1. **Isolation breach.** Sessions inherited the owner's `TEMP`, and Git Bash
   mounts `/tmp` there. off-vendor wrote a helper file into the shared temp
   folder in both of its sessions, so a file from the first session was
   visible to its re-run. The L4 scan caught both. Each session now gets a
   private `TEMP` inside its fresh home. The two lab-made files were removed
   from the owner's temp folder.
2. **Scan false positives,** which forced two needless re-runs:
   - the leading `.` was stripped from `./.git/*`, which turned it into
     `/.git`;
   - glob characters split `*/.git/*`;
   - a shell loop variable (`for f in inventory/*`) was read as an
     unresolvable path.

   The scan now keeps `./`, keeps glob characters inside a token, and skips
   variables the command binds itself. `/tmp` maps to the `TEMP` the session
   actually had, and Git Bash's mount table was confirmed. A bare `/` is
   deliberately not a candidate, because it is also division in inline
   code. Git Bash's `/` is its own install tree, so reaching the drive needs
   `/c/` or `C:\`, which are flagged.
3. **Verdicts are recomputed from evidence.** `screen.py` re-scans each
   session's recorded tool calls with the repaired scan, and reports the
   verdict recorded live alongside it. The repaired scan flags only
   off-vendor's two `/tmp` writes.

**Envelope:** 8 of 12 launches used (lab attempts 02, 04, 05 and 06, plus 4
diagnostics). Requests: 92 of 400 (88 lab and 4 diagnostic). 4 launches
remain for R0, R1, R2 and the conditional R3.

## Attempt 07 — R0 stopped by the other half of the telemetry race

Manifest `R0-7b7136c02fd2` was frozen at `d33c1e4371`, with `off-greedy` on
the long task and all 8 turns. Admitted at 17.51 GiB; the load took 18.8 s.
L3 passed. The first two requests reused cache as in the screen (3,759
tokens cached, 243 uncached).

**Failure.** The telemetry process died while request 91 was in flight,
with `PermissionError: [WinError 5]` on `os.replace(sample.tmp,
sample.json)`. The supervisor stopped with "critical telemetry process
exited", and cleanup aborted the request. Charged time for this attempt was
148.5 s.

**Diagnosis.** This is the same race as attempt 05, from the writer's side.
Windows also refuses to replace a file that another process has open. The
attempt-05 repair covered only the reader, so the bug class was not closed.
The other cross-process file paths in the lab were checked and are safe:

- `result.json` is read only after its writer exits.
- `events.jsonl` and `budget.json` each have a single writer.
- Logs are only `stat`'d while live.

**Repair.** The writer retries the replace for up to 0.5 s. If the
supervisor still holds the file, it skips that sample instead of dying, and
the supervisor's staleness rule bounds how long that may last. An offline
stress run tested both sides over 20 s, with the reader in a tight loop:

- **Writer:** 1,365 publishes, 0 skipped.
- **Reader:** 967 refused opens out of about 170,000 reads, all tolerated.
- **Corruption:** no torn read and no crash.

**Envelope:** 9 of 12 launches used. 3 remain, for R0, R1 and R2. R3 is
conditional on O3: R1's median uncached tokens per continued request must
exceed 2,000. The screen's thinking-on sessions measured 245–292, so R3 is
unlikely to be needed. A further failed launch would need the owner's
approval to extend the envelope.

## Attempt 08 — R0 (thinking off, greedy) completes the long task

Manifest `R0-310c9842e014` was frozen at `bead0e57aa`. Admitted; the load
took 14.9 s and L3 passed. The single 8-turn session finished with no stop.
The maximum supervisor lag was 0.36 s and cleanup took 0.83 s. Charged time
for this attempt was 764.7 s.

- **Verified: 4/4.** All 3 seeded defects were fixed and the feature was
  added, scored by the hidden verifier from fixture state alone. There was
  no contamination.
- **Requests: 18.** INT-0007 AC1's 20-request coverage is **not met**, and
  this is recorded separately from completion (L2). The model took fewer
  steps than the 22-request reference path.
- **Machine time:** 728 s. Decoded tokens: 2,138. That is **182 s and 535
  decoded tokens per verified item** (O1).
- **Cache:** append-only. After the cold 3,713-token opening prefill, the
  median uncached prompt per continued request was 56 tokens. Rendered input
  peaked at 7,738 tokens.
- **Where time went:** decode took 90% of machine time, at about 3.5 tok/s.
  On this host, decode speed is the bottleneck, as Sprint 2 found.
- **Resources:** the minimum available RAM per request was 6.29 GiB, against
  the 4 GiB reserve.

## Attempt 09 — R1 (thinking on, greedy, budget 256, echo off)

Manifest `R1-29e3a70e4c9e`. The load took 14.8 s and L3 passed. The single
session finished with no stop. The maximum supervisor lag was 0.33 s and
cleanup took 0.97 s. Charged time for this attempt was 1,427.2 s.

- **Verified: 4/4.** There was no contamination.
- **Requests: 20,** so **INT-0007 AC1's coverage is met.**
- **Machine time:** 1,389 s. Decoded tokens: 4,233, of which 1,999 were
  reasoning. That is **347 s and 1,058 decoded tokens per verified item**,
  about 1.9 times R0 for the same verified result.
- **Reasoning budget:** 3 of 20 requests hit it (255 tokens).

**Divergence (O2).** With echo off, every continued request rolls back
almost exactly the previous turn's generated tokens, reasoning included. A
468-token turn, for example, was followed by a 472-token rollback.
llama.cpp restores the context checkpoint it created at the end of the
previous prompt. It then reprocesses the re-rendered assistant turn, without
its think block, plus the new tool result. The divergence point is
therefore the start of the previous assistant turn, every turn.

| Measure | Value |
|---|---|
| Rollback range | 58–640 tokens |
| Median uncached prompt per continued request | 161 tokens |
| Largest uncached prompt (a tool output) | 1,095 tokens |
| Peak rendered input | 7,867 tokens |

The re-render cost is real but small, because each checkpoint sits just
before the generation.

**O3 — R3 is not run.** R1's median uncached prompt per continued request
was 161, which does not exceed the 2,000 threshold. The second condition,
frozen checkpoints of at least 2, was met (5). Checkpoint density has
nothing to recover here: the default end-of-prompt checkpoint already
bounds each rollback to one turn.

## Attempt 10 — R2 (R1 with reasoning echo): O2 answered, then a wire defect

Manifest `R2-e7903d921f15`, with `on-greedy` and `model.reasoning_echo:
true`. The load took 14.8 s and L3 passed. Charged time for this attempt was
1,139.0 s. The maximum supervisor lag was 0.34 s.

**O2 — echo keeps history append-only, except after a budget-truncated
think block.** Hermes replayed every earlier assistant turn with its
reasoning (12 of 12 turns by request 142). In 9 of 12 continued requests,
llama.cpp rolled back exactly 1 token and processed only the new tool
result: 25–58 uncached tokens, against a median of 161 in R1. The three large
rollbacks (494, 484 and 412 tokens) came exactly after the three turns whose
reasoning hit the 256-token budget. When the budget cuts a think block,
the forced end of thinking renders differently from what was generated, so
the template's re-render diverges at that turn. Otherwise the trimmed
re-render matches the generated block. Uncapped thinking (T-218) is where
the budget cut goes away.

**Failure.** Request 142 hit the 768-token output cap in the middle of a
tool call (`finish_reason: length`). Hermes detected the truncated tool call
and retried within about 1.6 s. The wire answered with 409, "unexpected or
concurrent inference request", and the session stopped at 13 requests with
3/4 verified. This counts as a failure in R2's denominators.

**Diagnosis.** This was a lab defect, not concurrency. The wire held its
one-request lock through the post-response accounting: two `/tokenize`
calls for the reasoning and visible split, plus the receipt. Hermes's client
finishes a streamed response at `[DONE]` and sent its retry while that tail
was still running. Earlier runs never exposed it, because tool execution
always separated consecutive requests.

**Repair.** The wire now tracks delivery separately from accounting:

- *In flight* ends when `[DONE]` (or the reassembled payload) reaches the
  client.
- A request arriving while another is in flight is refused as concurrent,
  through an atomic check-and-set.
- A sequential request waits on the accounting lock instead.

An offline repro uses a fake backend with a 0.8 s `/tokenize` and an
OpenAI-client-style reader that stops at `[DONE]`. On the pre-repair code it
**fails**: the sequential retry gets 409. On the repair it **passes 3 of 3**:
the sequential request is accepted, and a mid-stream concurrent request is
still refused while the first completes.

**Envelope:** 12 of 12 launches are used (8 lab and 4 diagnostic), and 146
of 400 requests (142 lab and 4 diagnostic). Replaying R2 needs a 13th launch,
so the owner was asked to extend the envelope by one.

**Owner decision (2026-10-03, in chat):** the envelope was extended by one
launch, to 13, for the R2 replay. No spare was approved.

## Attempt 11 — R2 replay stopped by the page-in resource guard (host maintenance)

Manifest `R2-b6a0ef378ab2` was frozen at the wire repair and admitted at
17.25 GiB; the load took 15.2 s and L3 passed. Charged time was 246.5 s.

The first two requests behaved as in attempt 10. Echo was on, the second
request reused 3,870 cached tokens and processed 238. During request 145,
three consecutive samples exceeded the 64 MiB/s page-in limit under RAM
pressure: 324, 70 and 83 MiB/s. Available RAM fell from 6.04 to 5.23 GiB in
about 3 s. The Sprint 2 paging guard stopped the attempt ("hard page-in rate
breached"). Cleanup aborted the in-flight request, and the listener closed.

**Cause: host maintenance, not the lab.** The backend's memory is fixed,
and the request was decoding. The Windows System log shows:

| Time (local) | Event |
|---|---|
| 20:28:06 | The console session went idle (Kernel-Power 566, session 528 → 530). |
| 20:33:30 | A secure trustlet started (IsolatedUserMode 5). |
| 20:33:31–33 | The page-in burst and the RAM draw that stopped the attempt. |
| 20:33:34 | The Background Intelligent Transfer Service was switched from demand start to auto start (SCM 7040). |
| 20:34:25 | Volsnap 24: shadow-copy storage could not grow, and the volume's shadow copies are at risk. |

Taken together, this is Windows idle maintenance starting once the machine
went idle. The guard did what it is for: it protected the owner's machine.
This is not a lab defect, so there is no repair. It is counted as a resource
stop for O5. C: had 180.8 GiB free and the lab tree is 0.65 GiB, so the
Volsnap warning points to the shadow-storage quota, a Windows setting the
owner controls. It was reported to the owner and not changed.

**Envelope:** all 13 launches used (12 approved plus 1 extension).
Requests: 149 of 400 (145 lab and 4 diagnostic). The owner is asked whether
to spend another launch on R2.

**Owner decision (2026-10-03, in chat):** one more launch, to 14, for a
second R2 replay. The owner keeps the PC active during the run, so Windows
idle maintenance does not start. The lab changes no system settings.

## Attempt 12 — second R2 replay stopped by the RAM reserve (owner applications)

Manifest `R2-8b1bcbff010f`, admitted at 17.33 GiB; the load took 15.4 s and
L3 passed. Ten requests completed, and they repeated attempt 10's echo
pattern: a large uncached re-render (491–523 tokens) followed each turn
whose reasoning hit the 256-token budget. Otherwise only the new tool result
was uncached (25–58 tokens). Charged time was 805.3 s.

**Stop.** Available RAM fell from 5.90 to 3.99 GiB in about 7 s, with
page-in bursts of 289 and 242 MiB/s. That crossed the 4 GiB reserve, and the
supervisor stopped the attempt ("RAM or VRAM reserve breached"). Cleanup
aborted the in-flight request. VRAM was not involved (2.4 GiB free).

**Cause: owner applications, not the lab.** The process table showed new
Chrome processes started at 20:50:05–08, alongside many resident
applications (game launchers, a cloud-sync client, an office assistant and
others). While the model runs it leaves about 6 GiB of headroom, so ordinary
desktop use can cross the 4 GiB reserve. The guard protected the machine as
designed. This is not a lab defect: no repair, and it is counted as a
resource stop for O5.

**Envelope:** all 14 launches used (12 approved plus 2 extensions).
Requests: 160 of 400 (156 lab and 4 diagnostic). R2 has not completed in
three attempts: one lab defect (repaired) and two host resource stops. Its
three partial runs (13, 3 and 10 requests) consistently answer O2.

**Owner decision (2026-10-03, in chat):** one more launch, to 15, for a
third R2 replay. The owner closes background applications and avoids
opening new ones for the run. It starts after the concurrent test-runner
hunt finishes, so the lab is the only heavy workload.

## Attempt 13 — R2 completes

Manifest `R2-03542237487a`, frozen at `4532740520`. The owner had closed
background applications. Admitted at 16.92 GiB; the load took 21.8 s and L3
passed. The single session finished with no stop. The maximum supervisor lag
was 0.44 s and cleanup took 0.81 s. Charged time was 1,461.4 s. The minimum
available RAM per request was 5.59 GiB, and the peak page-in was 94.7 MiB/s
in a single sample, which did not trip the guard.

- **Verified: 4/4.** There was no contamination.
- **Requests: 18.** INT-0007 AC1's coverage is **not met** (recorded
  separately).
- **Machine time:** 1,418 s. Decoded tokens: 4,603, of which 2,181 were
  reasoning. That is **354 s and 1,151 decoded tokens per verified item**,
  within a few percent of R1's 347 s and 1,058 tokens. On this host, echo is
  throughput-neutral.
- **O2:** the median uncached prompt per continued request was **60 tokens**,
  against R1's 161. 12 of 17 continued requests rolled back at most 1
  token, so history stays append-only. **All 5 large rollbacks (412–678
  tokens) followed exactly the turns whose reasoning hit the 256-token
  budget.** None followed any other turn. When the budget cuts the think
  block, the forced end of thinking re-renders differently from what was
  generated. Otherwise the template's trimmed re-render matches the
  generated block.

## Operational confidence record

Recorded at **2026-10-04T01:58Z** (commit `210d043a2a`). It precedes every Sprint 3 formal test
run (T-214, V1).

**Criteria met:**

- All planned full runs completed: R0 (attempt 08), R1 (attempt 09) and R2
  (attempt 13). R3's O3 condition was not met, and the reason is recorded
  under attempt 09.
- The screen completed (attempt 06), C1–C4 passed, and the calibration
  record exists.
- Every in-scope failure is linked to a diagnosis, a repair and a replay,
  listed below.
- **Time:** 10,788.8 s (3.0 h) charged across 13 lab attempts, against the
  host-derived 81,365 s backstop budget.
- **Envelope:** 15 launches (11 lab and 4 diagnostic), including the owner's
  three one-launch extensions. Requests: 178 of 400 (174 lab and 4
  diagnostic).

**Repair provenance (O4):**

| Failure (attempt) | Diagnosis | Repair | Replay |
|---|---|---|---|
| Prefill collapsed to 4.27 tok/s (02) | Fresh per-attempt `APPDATA` gave the driver a cold kernel JIT cache | `714f5afd4f`: lab-level kernel cache; growth counts as progress; compiled requests are not rate samples | 04 (cold cache, no false stall); 05 onward loaded in 14–22 s |
| Supervisor lag stop (02) | `cancel_active()` close waited on the reader lock; waits skipped `observe()` | `714f5afd4f`: socket shutdown; every supervisor wait keeps observing | 04: main-cancel settled in 0.84 s; maximum lag 0.38 s |
| 0 checkpoints frozen (04) | `write_calibration` got the post-load sample | `32a1d3342b`: admission sample | Recomputed from attempt 04's evidence at `a5413bc376` |
| C3 missed (04) | Per-session paths in the system prompt; slot erased | `32a1d3342b`: fixed live paths, archive, per-session `erase` | 05 and 06: byte-identical prompts, 1147/1151 reused |
| Telemetry read race (05) | Windows refuses to open a file mid-replace | `c9bcb37a55`: the reader keeps the last sample | 06 (78 requests, no recurrence) |
| Isolation breach via `/tmp` (06) | Sessions shared the owner's `TEMP` | `1850994283`: private session `TEMP` | 08–13: no shared-temp writes |
| Scan false positives (06) | `./` stripped; globs split; local variables | `1850994283`, `d33c1e4371` | Screen re-scanned from recorded tool calls |
| Telemetry writer race (07) | Windows refuses to replace an open file | `bead0e57aa`: the writer retries, then skips | 08–13 (offline stress run: 0 failures) |
| Sequential retry refused as concurrent (10) | The lock was held through post-response accounting | `c783199787`: delivery separated from accounting | Offline repro red to green. 11–13 had no truncated-tool-call retry, so the live path was not re-triggered. The formal integration test covers it. |
| Page-in stop (11) and reserve stop (12) | Host maintenance; owner applications | None: resource guards working as designed | 13 completed with apps closed |

**Prediction accuracy (O5)**, over all 165 requests with a prediction (all
after calibration):

| Prediction | Median predicted/actual | p10 | p90 | Range |
|---|---|---|---|---|
| Rearmed | 4.34 | 1.56 | 11.5 | 0.92–57 |
| Initial | 5.9 | 1.96 | 13.95 | 1.26–62 |

The predictor prices the full output cap at the smoothed decode rate. That
makes it a conservative bound, not a forecast, but not a strict one: one
request (attempt 10, request 142) ran 9% over its rearmed prediction. It
decoded the full 768-token cap at 3.27 tok/s with about 8K tokens of
context. Calibration measured 3.55 tok/s at about 1K. Decode slows as
context grows, and the T-215 prediction ignores that. No deadline was
affected, because enforcement uses the stall rule and the floor-priced
backstop. Noted for T-219.

**Every stall, backstop and resource stop (O5):**

- **Stall:** 1, in prefill (02), from cold kernel compilation.
- **Resource and lab stops:**
  - lag (02, a lab defect);
  - admission refused (03, the owner's apps);
  - telemetry race on read (05) and on write (07), both lab defects;
  - the wire concurrency refusal (10, a lab defect);
  - page-in during host maintenance (11);
  - the RAM reserve during owner app use (12).
- **Backstop:** none reached.

## Test-phase corrections and post-confidence lab changes (critique round 1)

These are recorded after the confidence record, in response to
[critique-01](critique-01.md).

**O5 accuracy claim corrected.** There were 169 post-calibration requests,
not 165:

- **165 completed requests** carry both predictions. Their rearmed
  predicted/actual statistics stand as recorded.
- **4 requests were stopped by an attempt stop** (attempts 05, 07, 11 and
  12). The pre-repair wire computed their predictions but never recorded
  them, and the stop surfaced only as a `wire_failure`.

The wire now records the initial prediction at send, and keeps elapsed time
and both predictions on every stop path. The supervisor writes a
`request_stopped` receipt with the attempt's stop reason. The republished
receipts mark those 4 requests `stopped`, with the real cause and an elapsed
time derived from receipt timestamps. Their predictions stay named missing.

**O1 machine time and denominators.**

- *Machine time* follows the screen's locked definition: first request to
  last response, excluding load. The full runs therefore read 721, 1,382 and
  1,410 s, not the session wall times (728, 1,389 and 1,418 s) used
  earlier.
- *"Failures and stops in the denominators"* (O1) means each run's cost
  includes every attempt of that run, failed or stopped, divided by the
  items it verified.

| Run | Completed run only | All attempts (O1) | Attempts included |
|---|---|---|---|
| R0 | 180 s, 535 tokens per item | **205 s, 558 tokens** | 07 (telemetry race), 08 |
| R1 | 346 s, 1,058 tokens per item | **345 s, 1,058 tokens** | 09 |
| R2 | 352 s, 1,151 tokens per item | **865 s, 2,636 tokens** | 10 (wire defect), 11 (host maintenance), 12 (owner apps), 13 |

The ranking is the same under both readings. R2's all-attempts cost is
dominated by one repaired lab defect and two host stops, not by echo; on the
completed run, echo was throughput-neutral.

**Lab changes after confidence (not replayed live; the launch envelope is
spent).** Each change is covered by the formal tests at `efeb4ef4c4`:

- *Behavior-preserving seams:*
  - `throughput.step_stop` replaces the inline stall and backstop checks;
  - `run.session_windows` collects every window a session uses;
  - `run.wait_while` is now module level;
  - `prepare.launch_flags` reproduces the published R2 argv;
  - `run.read_sample`;
  - `write_calibration` reads its admission receipt.
- *Receipt completeness:*
  - predictions are recorded at send and on every stop path;
  - the `request_stopped` receipt;
  - `id_slot` comes from `/slots`, because b10964 streams none, with
    `id_slot_source` recorded;
  - `publish.py` maps stopped and failed requests, and publishes attempts 01
    and 03.
- *Fixes:*
  - the wire's in-flight ownership race;
  - a repository path in the session `PATH`;
  - the telemetry writer's retry bound is now half its sample period, not a
    free 0.5 s.

**T5 bring-up replayed at `efeb4ef4c4`** (2026-10-04T02:52Z), with no model
loaded. The stall rule now watches each child's output:

- the chatty child survived 3 windows (6.0 s);
- the silent child was stopped at 2.109 s against a 2.0 s window;
- its 5-process tree was gone in 0.047 s;
- the sentinel survived.

## Test-phase corrections (critique round 2)

These are recorded in response to [critique-02](critique-02.md).

**O1 figures, recomputed from the published receipts.** Receipts now carry
each request's start and end, relative to the attempt start, and each
session's machine time (first request to last response). Cost per verified
item under O1 is the total machine time of every attempt of a run divided
by the total items those attempts verified. Partial items verified by a
stopped attempt count, because they were really produced.

| Run | Attempts: machine time, items verified | Completed run only | All attempts (O1) |
|---|---|---|---|
| R0 | 07: 100.5 s, 0 · 08: 720.8 s, 4 | 180.2 s, 534.5 tokens per item | **205.3 s, 557.5 tokens** |
| R1 | 09: 1,381.7 s, 4 | 345.4 s, 1,058.3 tokens per item | **345.4 s, 1,058.3 tokens** |
| R2 | 10: 1,094.2 s, 3 · 11: 192.1 s, 0 · 12: 761.8 s, 2 · 13: 1,410.2 s, 4 | 352.6 s, 1,150.8 tokens per item | **384.3 s, 1,171.6 tokens** |

This supersedes the round-1 table above. Round 1 divided by 4, ignoring
the partial items in stopped attempts, and rounded R1 two ways. The ranking
(R0 < R1 < R2) is unchanged. The token figures are lower bounds (see
round 6).

**Stopped sessions scored (L2).** Sessions that an attempt stop cut short
are now scored from their fixture state. Going forward, `run.py` does this
in its stop path (`session_stopped`). For earlier attempts, `publish.py`
scores the fixture that the stop preserved in `<attempt>/live`:

| Attempt | Session | Requests | Verified |
|---|---|---|---|
| 05 | screen session 3 | 3 | 0 |
| 07 | R0 | 3 | 0 |
| 11 | R2 | 3 | 0 |
| 12 | R2 | 11 | **2** |

(Request counts corrected in round 3; see below.)

**Further lab changes after confidence** (not replayed live, covered by the
formal tests at `1fca1a3095`):

- the stopped-request and stopped-session seams;
- `RequestExtrema`, which records resources on every loop exit;
- `erases_slot`;
- `probe_window`, which derives the backend probe timeout.

Requests stopped in attempts 02, 05, 07, 11 and 12, before
`RequestExtrema` existed, name their resource extrema as missing (corrected
in round 3).

**Plan deviation: the retained fixed values** (restated in round 3). The
locked plan retained the cadences and the guards counted in them, the 2 s
grace and 5 s cleanup, the wire's 1 s lock handoff and the `git` tool
timeouts. The Test phase listed every other fixed bound with its reason in
the lab README:

- the telemetry writer retry;
- the `nvidia-smi` query;
- the verifier process and thread bounds;
- one-time venv creation;
- the backend listener check after cleanup (0.2 s).

None of these bounds token work.

## Test-phase corrections (critique round 3)

These are recorded in response to [critique-03](critique-03.md). The code
changes are at `4f323770ee`. They were not replayed live, because no launch
envelope remains. The publish changes ran over every real attempt, and
all 13 receipts were republished.

**Stop causes.** Attempt 02's only request was stopped by its session's
stall rule (`stall in prefill (window 47.0s)`). The attempt itself stopped
later, on scheduler lag. The receipt had given the request the attempt's
cause. It now carries its own session's stop, and only a request in flight
at the attempt stop takes the attempt's reason.

**Cut-short sessions screened (L4).** Each cut-short session was screened
from the conversation its last request forwarded. In all four, that
request was in flight at the stop, so no executed tool call came after it:

| Attempt | Session | Requests | Messages screened | Tool calls | Flagged |
|---|---|---|---|---|---|
| 05 | screen session 3 | 3 | 6 | 2 | none |
| 07 | R0 | 3 | 6 | 2 | none |
| 11 | R2 | 3 | 6 | 2 | none |
| 12 | R2 | 11 | 22 | 6 | none |

Going forward, the wire also keeps the response it last delivered, so a
stop between requests screens the tool calls Hermes may already have run.

**O1 under every reading.** Machine time per verified item:

| Run | Completed run only | All attempts, all items verified (O1) | All attempts, cut-short items excluded | All attempts ÷ one run's 4 items |
|---|---|---|---|---|
| R0 | 180.2 s | **205.3 s** | 205.3 s | 205.3 s |
| R1 | 345.4 s | **345.4 s** | 345.4 s | 345.4 s |
| R2 | 352.6 s | **384.3 s** | 494.0 s | 864.6 s |

R0 < R1 < R2 under every reading. Attempt 12's two items now pass L4, so
O1 counts them; the other columns show what excluding them, or
reading the round-1 denominator, would give.

## Test-phase corrections (critique round 4)

These are recorded in response to [critique-04](critique-04.md). The code
changes are at `663bac6a2a`. Like round 3, they were not replayed live, and
all 13 receipts were republished.

- **Stall and backstop stops name their cause going forward.** A session's
  stop now records the in-flight request's `request_stopped` before the
  wire cancels it. No published attempt hit this path: attempt 02's stall
  predates the wire cancel, and its cause was corrected in round 3.
- **Fields named missing.** The stopped requests of attempts 02, 05, 07, 11
  and 12 now name their meaningful first token and tool-call count missing.
  Attempt 04's deliberately cancelled request names its tool-call count
  missing; it carries its first token (12.344 s). The pre-repair wire never
  recorded them. (Corrected in round 5.)
- **Cut-short tool-call validity.** Attempts 05, 07, 11 and 12 made 2, 2, 2
  and 6 tool calls in the conversations screened at publish. All were
  valid and known.
- **Screens publish what they saw.** The published counts, 6, 6, 6 and 22
  messages with those tool calls, match the round-3 table.
- **P2 at test time.** At 2026-10-05T21:38:24Z, head `663bac6a2a`, the live
  `config.yaml` and `presets.ini` equal the plan baseline. They are
  re-checked at close.

## Test-phase corrections (critique round 5)

These are recorded in response to [critique-05](critique-05.md). The code
changes are at `9c373121cd`. They were not replayed live; backlog **T-224**
replays them in Sprint 4's first lab attempt. All 13 receipts were
republished.

- **A dropped tool call.** In attempt 10, request 142 hit the 768-token cap
  mid-call (`finish_reason: length`). Hermes rejected the cut call and
  retried, so the call never entered its history. Validity, then computed
  from that history, showed 7 of 7 valid. The receipt now shows 8 delivered
  calls and names 1 unvalidated, request 142. Every other long session
  validates every delivered call. From now on the wire records validity
  for each delivered call, so a cut call is recorded invalid.
- **The token split.** Visible tokens are assistant content only. The
  published receipts did not count tool-call output, so each request now
  names the remainder of its decoded count (`unsplit_decoded_tokens`). In
  R0, R1 and R2 that remainder is the tool-call output plus template
  markup. The wire now counts tool-call output separately.
- **AC1 coverage on stopped sessions.** The cut-short long:all sessions of
  attempts 07, 11 and 12 (3, 3 and 11 requests) now record coverage not
  met.
- **Supervisor lag.** Only attempt 02 exceeded two telemetry periods (14.9
  s), and it is the only lag stop. Every other attempt peaked at 0.63 s or
  less.
- **Hermes timers.** Every session after calibration ran with its Hermes
  timer equal to its own request backstop: 1,931.4 s at the 512 cap and
  2,219.9 s at the 768 cap.

## Test-phase corrections (critique round 6)

These are recorded in response to [critique-06](critique-06.md), which passed
with caveats. The code changes are at `a730a0a39e`. They were not replayed
live (T-224), and all 13 receipts were republished.

- **Decoded tokens of stopped requests.** Token figures are lower bounds. Three stopped requests (attempt 07's request 91, attempt 11's 145 and attempt 12's 156) never returned a decode count, so their receipts name it missing and the sums count them as 0. Each receipt publishes how long the request ran after its prompt was fully processed: 30.5, 89.1 and 16.7 s. At the fastest decode rate any receipt shows (3.743 tok/s), that time allows about 114 more tokens in R0 and 396 in R2, or about 586.1 and 1,215.6 tokens per verified item. This is an estimate from the receipts, not a strict bound. (Restated in round 7.) R1 has no stopped
  request, so its figure is exact. From now on a stop receipt carries the last
  `/slots` decode count as an observed lower bound.
- **Schema 3.** Manifests frozen from now on carry schema 3. Their receipts
  must carry `id_slot` (from `/slots`) and tool-call tokens, and must
  validate every delivered call. The 13 published attempts are schema 2.

## Test-phase corrections (critique round 7)

These are recorded in response to [critique-07](critique-07.md), which passed
with caveats. The code changes are at `47522c6a2d`. All 13 receipts were
republished.

- **Echo and prefill.** Echo on cut the median continued request's
  uncached prompt from 161 to 60 tokens. It did not cut the total: R2's
  completed run (attempt 13) processed 8,259 uncached prompt tokens in
  90.3 s, against R1's 7,943 in 93.7 s. The policy's "about 60% of the
  prefill work" is corrected.
- **Peak input.** The peak rendered input across the full runs was 9,935
  tokens (attempt 13, request 174), within the 31,488-token ceiling. The
  7,867 above is R1's.
- **The screen re-scan, published.** Attempt 06's receipt now carries the
  S2 ranking under the current L4 scan, beside each session's live verdict:
  - sessions 6 and 7 (off-model-default) and 10 and 11 (on-mid-probe) were
    flagged live for `/.git/`, resolved against Git's install path, and the
    shell-local `$f`. Both are false positives of the pre-repair scanner,
    and the re-scan clears them;
  - sessions 4 and 5 (off-vendor) stay flagged for files written to the
    then-shared `/tmp`.

  Re-ranking the published sessions reproduces `screen_winners`
  (off-greedy, on-greedy).
- **The decode estimate.** Each stopped request publishes its seconds after
  prefill: 30.5 s (91), 89.1 s (145) and 16.7 s (156). The estimate uses the
  fastest decode rate any receipt shows (3.743 tok/s, attempt 06's request
  71), not the calibrated 3.55: 23 of 162 completed requests decoded faster.

## Test-phase corrections (critique round 8)

These are recorded in response to [critique-08](critique-08.md), which passed
with caveats. The test changes are at `32b8e50eaf`.

- **The uncounted screen session.** S2 ranks the screen that completed (attempt 06), one session per configuration under L4's pick. Attempt 05, an earlier screen stopped by the telemetry read race (a lab defect, repaired and replayed as attempt 06), is not counted. Its off-greedy session ran 3 requests for 116.0 s and verified 0 of turns 1–3. Counted the way O1 counts a stopped full-run attempt, thinking-off greedy would cost 375.4 s per verified item, against model default's 318.5 s (320.0 s across its two sessions), and model default would rank first. Thinking-off greedy against model default at full task length is unmeasured (backlog T-225).
- **Identity.** Every published manifest is now asserted to pin INT-0004
  AC1's identity: model, tokenizer, template, backend and corpus hashes,
  the Hermes commit, the interpreter and the seed.

## Test-phase corrections (critique round 9)

These are recorded in response to [critique-09](critique-09.md), which passed
with caveats. The code changes are at `a80294f17a`.

- **Attempt 10's refused retry.** Attempt 10's session ended when Hermes retried after request 142's cap-cut response and the wire refused the retry as concurrent. That refusal wrote no receipt, so the retry has no request record, and every published request reads `continuation_of_length_finish: false`. Since round 9 the wire receipts this refusal like every other one.
- **Identity.** The manifest check now also covers every backend library
  hash (33 files, the CUDA code included), a clean source tree, an integer
  seed and the interpreter.
- **The screen's inputs.** The published screen sessions are tied to the
  receipt's own session starts, machine-time spans and decoded tokens.
