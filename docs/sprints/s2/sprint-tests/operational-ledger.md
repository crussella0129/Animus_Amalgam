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
