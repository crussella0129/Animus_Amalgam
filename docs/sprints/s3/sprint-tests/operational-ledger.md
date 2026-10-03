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
