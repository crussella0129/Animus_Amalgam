# Hermes decoding and integration seams

This chapter describes Amalgam commit
`6223d9e2bc3280e6e21d0b0a6961eadfafe4183e`. Where noted, it also compares
the separately installed Hermes checkout at
`5dd70d7cb6560c3ff8aff294ec44ec4f8d1558e5`. The checkouts are not
interchangeable evidence for an earlier running process.

## Smallest existing attachment point

Hermes already supports the first Amalgam experiment without a core tool or a
second agent loop:

1. `plugins/model-providers/custom/__init__.py:100` recognizes local,
   vLLM, and llama.cpp aliases. `agent/agent_init.py:259` attaches endpoint-
   specific static request data.
2. A user-installed model-provider plugin can register `ProviderProfile`
   metadata and defaults (`providers/base.py:42,144,197`;
   `providers/__init__.py:395`).
3. Static profile hooks receive model, endpoint, reasoning, and session
   metadata, not current messages/tools
   (`agent/transports/chat_completions.py:552-578`). If an experiment needs
   request-specific policy, existing `llm_request` middleware sees the
   complete request and request/session identity (`agent/turn_api_request.py:140`;
   `hermes_cli/middleware.py:88`). It must be scoped to the intended endpoint.
4. A profile may supply an OpenAI-shaped custom client
   (`providers/base.py:331`; `agent/agent_runtime_helpers.py:1739`). That is a
   later option because the client inherits streaming, cancellation, cleanup,
   interruption, and auxiliary-call obligations.

The first baseline is therefore the existing custom endpoint. A narrow Rust
sidecar or provider plugin is added only for a concrete missing policy,
configuration, or protocol capability. The sidecar remains an inference/
policy boundary; Hermes owns the conversation, authority, tools, and results.

## Existing tool-call path

`model_tools.py:500` selects tool definitions and `:515` sanitizes shapes that
include llama.cpp grammar-converter incompatibilities.
`agent/turn_request_assembly.py:196` constructs a decorated request without
mutating canonical history. `agent/chat_completion_helpers.py:1406` passes
messages and tools to `agent/transports/chat_completions.py:343`.

The transport normalizes completions and tool calls at
`agent/transports/chat_completions.py:601,645`.
`agent/turn_tool_validation.py:70` checks names and JSON, rejects truncated
arguments, and permits valid members of mixed batches. `model_tools.py:867`
then dispatches through existing guards, middleware, and approvals.

An Amalgam service should consume those existing definitions and return the
same tool-call protocol. Grammar enforcement can guarantee representable
shape; the existing harness still decides whether a tool is authorized,
whether arguments make sense, and whether execution proves the task complete.

Hermes auxiliary structured output is built in `agent/plugin_llm.py:403` and
parsed/validated at `:316`; unsupported format declarations live in
`providers/base.py:140`. This does not prove that a blanket main-loop response
schema is compatible with prose, reasoning, and native tool syntax.

## Observation without new core instrumentation

The pre-request observer (`agent/turn_api_request.py:42`) exposes approximate
tokens, characters, tools, and request IDs. The post-request observer
(`agent/turn_response_intake.py:58`) exposes duration, first chunk, usage, and
tool-call count. `agent/transports/chat_completions.py:670` extracts reported
cached tokens. A future plugin can record experiment receipts through these
surfaces, supplemented by server prompt/decode timing and host resource data.

`supports_prompt_cache_key` defaults off (`providers/base.py:98`). Even when
enabled, a routing key is not evidence that a local backend reused KV state.

## Cache and session invariants

For a conversation, keep system bytes, serialized prior messages, tool
definitions/order, and the chat template stable. Adaptation outside rendered
tokens is only a candidate invariant: grammar metadata, response format, and
`tool_choice` may affect rendering or server cache residency. A documented
SGLang path changes rendering when `tool_choice="none"`
(`agent/chat_completion_helpers.py:2244`). Every backend needs token-prefix
and actual cached-token evidence.

Any controller state must be keyed by the existing profile and session
identity. A process-global policy would leak across profiles and conflict with
Hermes's multiplex rules. Context-engine selection can alter a request without
rewriting stored history (`agent/context_engine.py:120`), but it deliberately
changes the cache prefix and is not a free context-reduction mechanism.

## Compression and managed growth

For windows below 512K, `agent/context_compressor.py:2524-2568` raises the
configured compression ratio to at least 75%. The installed source also uses
a 64,000-token minimum (`agent/model_metadata.py:317`) and a conditional 85%
window cap. This exactly yields the logged 55,705 threshold for a 65,536
window and 73,728 for a 98,304 window when no output reservation applies.
An absolute `threshold_tokens` value is a downward cap, so the observed
256,000 value lowered neither threshold.

Managed runtime growth is constant-driven rather than exposed as a dedicated
toggle (`hermes_cli/local_runtime/context_policy.py:1,16-18`).
`agent/turn_context_compaction.py:308` attempts growth before compression;
`hermes_cli/local_runtime/growth.py:112` marks occupancy confirmed. The call
from `agent/conversation_loop.py:419` does not provide measured decode speed,
so that path does not apply the policy's speed floor. These are source facts,
not proof that one line caused the whole observed slowdown.

A bounded experiment should use a fresh profile/process with
`local_runtime.enabled: false` (`hermes_cli/local_runtime/bootstrap.py:272`)
and a separately launched fixed-context llama.cpp endpoint. `growth.py:81`
declines growth without its in-process supervisor or for a different endpoint.
The test must verify the endpoint and actual server context before load; a
configuration edit does not reconfigure an already-running backend.

## Existing implementation verification surfaces

Future code should extend behavior rather than test source text. Located
coverage includes:

- `tests/agent/test_provider_client_seam.py` and
  `tests/agent/test_auxiliary_provider_supplied_client.py`;
- real plugin middleware invocation at `tests/hermes_cli/test_plugins.py:304`;
- request/cache-key behavior at
  `tests/agent/transports/test_chat_completions.py:833,932`;
- `tests/tools/test_schema_sanitizer.py`;
- compression threshold and timeout coverage in
  `tests/agent/test_compression_small_ctx_threshold_floor.py:33`,
  `tests/agent/test_auxiliary_compression_timeout_floor.py`, and
  `tests/agent/test_preflight_compression_cap_e2e.py`.

Any eventual provider/plugin integration needs the real import/resolution path
under a temporary `HERMES_HOME`, plus A-to-B-to-A profile isolation when it
holds state. Python tests run through `scripts/run_tests.sh`.

## Decision boundary

Start with the existing custom endpoint. Add a Rust policy/protocol service
only when it can consume Hermes's frozen tool vocabulary and improve measured
outcomes while returning ordinary Hermes responses. Add a provider plugin only
for a demonstrated configuration or per-session metadata gap. Consider an
in-process client or a new token-mask engine only after profiling isolates a
specific requirement existing engines cannot meet.
