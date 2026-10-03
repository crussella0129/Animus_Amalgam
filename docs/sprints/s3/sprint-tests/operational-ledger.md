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
