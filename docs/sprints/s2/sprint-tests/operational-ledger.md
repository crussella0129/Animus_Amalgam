# Sprint 2 operational development ledger

Official unit/integration suites have not run. Operational confidence is
pending. These are environment bring-up and actual-operation observations.

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
