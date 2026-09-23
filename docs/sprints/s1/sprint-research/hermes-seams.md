# Hermes integration findings

Research snapshot: Amalgam `6223d9e2bc3280e6e21d0b0a6961eadfafe4183e`.
Paths and line numbers below refer to that commit, not the separately installed
Hermes runtime. This is evidence for T-104, not a selected implementation.

## Existing attachment points

| Surface | Evidence at the snapshot | Meaning for Amalgam |
|---|---|---|
| Custom OpenAI-compatible endpoint | `plugins/model-providers/custom/__init__.py:100`; `agent/agent_init.py:259` | Local/llama.cpp aliases and endpoint-specific extra body already exist. An external service need not add core tools or fork the agent loop. |
| Provider profile | `providers/base.py:42,144,197`; `providers/__init__.py:395` | An out-of-tree model-provider plugin can own setup metadata, model capabilities and request defaults. |
| Request-specific policy | `agent/turn_api_request.py:140`; `hermes_cli/middleware.py:88` | Existing `llm_request` middleware sees the complete request and session/turn/request identity. Scope any use to the Amalgam endpoint. |
| Custom client | `providers/base.py:331`; `agent/agent_runtime_helpers.py:1739` | The profile may supply an OpenAI-shaped client, including an in-process implementation. It inherits streaming, cancellation, cleanup and auxiliary-call responsibilities. |
| Observability | `agent/turn_api_request.py:42`; `agent/turn_response_intake.py:58` | Existing pre/post request observers expose request size, timings, first chunk, usage and tool-call counts. |
| Context engine | `agent/context_engine.py:120` | Request-only context selection exists, but explicitly changes the cache prefix. It is not cost-free prefix reuse. |

The ordinary profile hooks `build_extra_body` and `build_api_kwargs_extras`
receive model, endpoint, reasoning and session metadata, **not** current
messages and tools (`agent/transports/chat_completions.py:552-578`). Static
configuration cannot implement state-dependent grammar selection by itself.
The server can derive policy from the existing request; middleware is only
needed if additional session facts are required. Do not add a parallel manager
before identifying such a missing fact.

## Tool-call path and semantic ownership

`model_tools.py:500` selects definitions; `:515` sanitizes schema shapes,
including shapes rejected by llama.cpp's grammar converter.
`agent/turn_request_assembly.py:196` works from the conversation's tools;
`agent/chat_completion_helpers.py:1406` passes messages/tools to
`agent/transports/chat_completions.py:343`. The transport normalizes returned
calls at `:601,645`. `agent/turn_tool_validation.py:70` checks names and JSON,
with some repair behavior, before `model_tools.py:867` dispatches through
existing middleware, guards and approvals.

An Amalgam service should return that same tool-call protocol. It should not
execute tools, invent a second authority system, or translate successful JSON
parsing into a claim that the requested operation is correct.

Auxiliary structured output is implemented in `agent/plugin_llm.py:403`,
with parsing/validation at `:316`. Provider unsupported-format declarations
are in `providers/base.py:140`. This does not establish that a blanket main-loop
JSON schema is compatible with every model's prose, thinking and native tool
syntax.

## Cache constraints

Freeze system text, prior messages, tool definitions/order and the chat
template during a conversation. Adaptation outside the rendered prompt is a
candidate, not a proven invariant: grammar, `tool_choice` or response-format
changes might change the backend's rendered tokens or reuse policy.
`agent/chat_completion_helpers.py:2244` documents a concrete SGLang case where
`tool_choice="none"` renders with no tools and changes the prefix.

Measure actual server token-prefix equality and cached token counts.
`supports_prompt_cache_key` (`providers/base.py:98`) and a stable Hermes
message list are not substitutes for that measurement. Profile/controller
state must use the existing session and profile identity, never a shared
process-global adaptive state.

## Compression and timeouts

- `agent/context_compressor.py:2531` floors the effective compression ratio
  at 75% for windows below 512,000 tokens. Lowering the configured ratio alone
  can therefore leave a local model with a much larger trigger than intended.
- `compression.threshold_tokens` is an absolute downward cap
  (`agent/context_compressor.py:2518`, `hermes_cli/config_defaults.py:566`).
  The cap must be chosen after measuring the fixed system/tool prefix and
  reserving completion and compression capacity.
- Tool-only proactive pruning and micro-compaction are off by default
  (`config_defaults.py:588,600`). Pruning has reclaimability/tail checks and
  hysteresis (`context_compressor.py:3149`); micro-compaction explicitly warns
  about repeated cache breaks.
- Provider request timeout and stale timeout are separate, with per-model
  overrides (`hermes_cli/timeouts.py:34,39`). Local streaming has its own
  default (`agent/chat_completion_helpers.py:599,604`). Compression has an
  inactivity budget and a total ceiling (`config_defaults.py:624`).

Increasing those budgets permits longer work; it does not make that work fit
RAM/VRAM or make compaction succeed. A compressor using the same local server
may also compete for cache residency. This latter mechanism needs a controlled
test; the local logs establish failures, not every cause.

## Managed runtime growth and the installed source

Follow-up inspection found the installed runtime checkout at
`C:/Users/charl/AppData/Local/hermes/hermes-agent`, current commit
`5dd70d7cb6560c3ff8aff294ec44ec4f8d1558e5`. This is different from Amalgam.
The two inspected `hermes_cli/local_runtime/growth.py` and `context_policy.py`
files have identical hashes. The installed compressor was read directly;
this still does not establish the historical process's exact source state.

`context_policy.py:1,16-18` defines a 65,536-token floor, 1.5 growth ladder
and 85% occupancy gate as constants, not configuration knobs. A separate
compression floor is 64,000 (`agent/model_metadata.py:317`). With no output
reservation, the installed compressor's formula (`context_compressor.py:2524-2568`)
gives exactly the logged thresholds: 65,536 times .75 is below 64,000, so the
floor binds and the 85% window cap yields 55,705; 98,304 times .75 exceeds
the floor and yields 73,728. The configured absolute 256,000 cap lowers neither.

`agent/turn_context_compaction.py:308` attempts runtime growth before
compression. `growth.py:112` passes `occupancy_confirmed=True`; this bypasses
the separate occupancy check. A lower compression cap therefore must not be
treated as a managed-growth cap. `agent/conversation_loop.py:419` also calls
the growth helper without measured decode speed, so that path does not apply
the policy's speed floor (`context_policy.py:197`). This is a source finding,
not a reproduced upstream bug or proof of the slowdown's entire cause.

For a bounded future baseline, use a fresh profile/process with
`local_runtime.enabled: false` (`bootstrap.py:272`), a distinct external
endpoint and explicitly fixed server context/parallelism. `growth.py:81`
declines growth without a supervisor or for a different endpoint. Verify
those preconditions and the actual context before any load test.

## Existing verification to reuse in a later implementation

The following are located coverage, not tests run during this research:

- `tests/agent/test_provider_client_seam.py` and
  `tests/agent/test_auxiliary_provider_supplied_client.py`.
- `tests/hermes_cli/test_plugins.py:304` (real middleware registration).
- `tests/agent/transports/test_chat_completions.py:833,932`
  (request body/cache-key behavior).
- `tests/tools/test_schema_sanitizer.py`.
- `tests/agent/test_compression_small_ctx_threshold_floor.py:33`,
  `tests/agent/test_auxiliary_compression_timeout_floor.py`, and
  `tests/agent/test_preflight_compression_cap_e2e.py`.

Run affected Python tests through `scripts/run_tests.sh`; an eventual plugin
needs real temporary-home imports and A-to-B-to-A profile isolation evidence.
