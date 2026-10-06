# Sprint 3 Meta

- **Sprint number:** 3
- **Book schema version:** 2
- **Start timestamp:** 2026-09-24T20:01:42Z
- **End timestamp:** 2026-10-06T10:58:37Z
- **Model:** Claude Opus 5.5 (claude-opus-5-5)
- **Bundle version:** 0.22.0
- **Exit status:** success
- **Token count:** (filled at Loop Phase if observable)
- **Summary:** Host-calibrated deadlines, a hardened lab, a sampling × thinking screen and full long-task runs of the winners with reasoning echo on the real 27B
- **Intents:** [INT-0007](../../intents/INT-0007-decode-budget-long-session.md), [INT-0004](../../intents/INT-0004-bounded-local-model-qualification.md)
- **Completion evidence:** Test phase passed on the 11th critic round (proceed-with-caveats; 5 blocks repaired); formal 321/321 at 35087cbdf7; R0-R2 4/4 verified with O1 205.3/345.4/384.3 s per item; INT-0007 AC2 (off, bounded), AC3, AC6 (measured settings) and AC7 (lab route) met, AC1 partly (T-223); INT-0004 AC1, AC2 and AC4 gaps closed; P2 live fingerprints unchanged at close (2026-10-06T10:58Z)
- **Checkpoint:** https://github.com/crussella0129/Animus_Amalgam/pull/4
- 2026-10-03 owner-directed environment reset, after the owner freed disk and
  memory. The owner believed the model had been deleted. The read-only check
  found it present and byte-identical (SHA-256 `322e194f…`), so it was kept,
  by owner choice, and no re-download happened. Per the owner's choices:
  - The lab environments went to the Recycle Bin (repo `.hermes-sandbox`,
    repo `.venv`, `C:\Users\<user>\amalgam-lab`). Sprint 2's raw private
    receipts went with them; their fingerprints remain in the Book.
  - Vanilla Hermes's stale llama.cpp downloads, the `cuda124-staging` probe
    and the `b10964` runtime also went to the Recycle Bin.
  - The runtime was reinstalled from the official b10964 CUDA 12.4 release
    archives. Their hashes match the pins (`8c79a9b2…`, `264f20d7…`), the
    binary hash `aa2e1f5c…` is identical, and vanilla Hermes's own verifier
    accepts it. Hermes's current installer would choose CUDA 13.3, so the
    pinned 12.4 pair was installed directly.
  - The lab venv (outside the repo, project not installed) and the test venv
    were rebuilt from `uv.lock` with the same base interpreter.

  Vanilla Hermes and the lab share the one model file. The live
  `config.yaml` and `presets.ini` are unchanged, matching the P2 baseline.
