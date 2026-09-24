# Sprint 2 read-only inventory

Collected without loading a model or changing the installed Hermes profile.
Paths below use workspace-relative aliases to keep public evidence portable.
Model names describe local artifacts, not verified publisher provenance.

## Selected artifact and comparison

| Field | Selected first | Available later comparison |
|---|---|---|
| Alias | `HERMES_LOCAL/models/Qwen3.8-27B-UD-Q4_K_M.gguf` | `FERRIC/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf` |
| File bytes | 16,464,440,224 | 4,683,073,536 |
| Full SHA-256 | `322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482` | `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` |
| GGUF version | 3 | 3 |
| Header name / architecture | Qwen3.8-27B / qwen35 | Qwen2.5 Coder 7B Instruct GGUF / qwen2 |
| Blocks | 65 | 28 |
| Declared context | 262,144 | 131,072 |
| Vocabulary entries | 248,320 | 152,064 |
| Tensor bytes | 16,453,443,584 | 4,677,120,000 |
| Embedded tokenizer metadata SHA-256 | `46bfddc9ebc958e47d494711342ad3143a25308288aee0279e37546143db3ef1` | `56e11a9607bb06a1d4366aad99d7da08353492440cc75bcffdd89a70ee6cb19c` |
| Embedded template metadata SHA-256 | `3a0497e618ff1b4afb12431e2e45d8edff1bbec81491ba80aaa51ff04700b1f4` | `24f79a69401549da90b4da8477caf9cab6fc0a58929b81767003df310a513e33` |

Full file hashes use SHA-256 over file bytes. Metadata came from the existing
`hermes_cli.local_runtime.gguf.read_gguf_header` at the Amalgam pin below.
Tokenizer fingerprints hash UTF-8 JSON with sorted keys, compact separators
and `ensure_ascii=False`, selecting keys starting `tokenizer.` except those
containing `chat_template`. Template fingerprints use the same encoding for
keys containing `chat_template`. These are normalized embedded metadata
fingerprints, not publisher-file hashes or rendered-prefix hashes. Both
artifacts contain `tokenizer.chat_template`. Record rendered prompt/token IDs
separately before any inference.

The 27B local artifact label and header are consistent with the previous
session. Publisher revision and license/source chain remain unverified; do
not download replacements or claim authenticity from the filename. The 27B
hash completed at 2026-09-23T23:34:41-04:00. An additional 27B copy exists in
Ferric, but its byte identity was not verified and it is not the selected path.

## Backend and software

- Hermes source: `cd2185c288398b19941b968e4352bf38bbcafbda`.
- Server alias: `HERMES_LOCAL/runtimes/llamacpp/b10964/cuda/llama-server.exe`.
- Server executable SHA-256:
  `aa2e1f5c67be55f11be26ae58d643a545ca07c6de498f6f870330ac2f4dfec73`.
- Actual `--version`: 0.4.1-dev, build 10964, commit `b29c606e2`,
  Clang 20.1.8, Windows x86_64. Official source resolves to
  `b29c606e28a01b1bc8c1351026a0fa6e616bf6c4`.
- Installed runtime manifest: CUDA, tag b10964. Archive fingerprints:
  `cudart-llama-bin-win-cuda-12.4-x64.zip` →
  `8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6`;
  `llama-b10964-bin-win-cuda-12.4-x64.zip` →
  `264f20d7ee3860aecca9ec12418357a9f3e80349a2b186f66c63859ded1a9593`.
  DLL hashes and actual loaded-device features remain manifest-stage work.
- Rust toolchain observed: cargo 1.98.1 / rustc 1.98.1.
- Installed Hermes Python used only for read-only inspection: 3.11.16,
  PyYAML 6.0.3, psutil 7.2.2. This is not a frozen evaluation environment.

Local `--help` confirms fixed context, explicit GPU layers, q8_0 K/V,
flash-attention selection, `--fit off`, one-slot parallelism, no speculation,
cache-RAM control, no-context-shift, metrics and slot inspection. Defaults
include context from model, automatic parallelism, 8,192 MiB prompt cache,
automatic fit and unlimited prediction. Override relevant defaults explicitly.
The HTTP timeout is not an independent end-to-end request deadline.

## Host snapshots

Windows 11 Pro 10.0.26200; Ryzen 9 5900X, 12 cores / 24 logical processors;
visible RAM 34,281,484,288 bytes. RTX 2080 Ti, 11,264 MiB VRAM, driver 596.49.
Identity came from read-only OS queries and `nvidia-smi`.

At 2026-09-23T23:34:43-04:00, psutil reported 7,799,349,248 available RAM
bytes (7.26 GiB), and `nvidia-smi` reported 1,851 MiB used / 9,177 MiB free
dedicated VRAM. Earlier snapshots showed roughly 6.9 GiB RAM and 9.0 GiB
VRAM available. These observations are not persistent capacity reservations.
No explanation for unrelated memory use was established.

The selected tensor data is 15.32 GiB. At the later snapshot, subtracting the
protocol's 4 GiB RAM and 1 GiB VRAM reserves leaves about 11.22 GiB combined.
Even that optimistic shared placement capacity is below the weight bytes,
before runtime overhead. The conservative no-paging gate would reject this
snapshot. This is a policy inference, not an observed OOM or a measured peak.
Real placement needs separate CPU and GPU checks as well as the aggregate
lower bound. Fresh measurements govern any later attempt.

## Not measured

No load peak, inference timings, native grammar behavior, cache reuse, GPU
placement, server context, rendered-prefix size or cancellation performance
was measured. No server was started. A small fixed context alone does not
establish fit. No raw logs, live configuration, secrets or owner transcript
are included in this inventory.
