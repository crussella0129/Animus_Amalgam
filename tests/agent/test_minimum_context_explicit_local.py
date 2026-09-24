"""The 64K floor admits an explicitly pinned local custom window only without auto-compression.

Reproduced in Sprint 2 operation: a real llama.cpp server fixed at 8192 tokens was refused
by ``_enforce_minimum_context`` although the operator had pinned that exact capacity and
disabled automatic compression, mirroring the existing explicit LM Studio exception.
"""

from unittest.mock import patch

import pytest

LOCAL = "http://127.0.0.1:18082/v1"


def _build_custom_agent(cfg, base_url=LOCAL, probed_ctx=8192, served_num_ctx=None):
    import agent.context_compressor as cc_mod

    with (
        # The served window a local server reports; never probe the network in tests.
        patch("agent.agent_init.query_ollama_num_ctx", return_value=served_num_ctx),
        patch("model_tools.get_tool_definitions", return_value=[]),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI"),
        patch("hermes_cli.config.load_config", return_value=cfg),
        patch("hermes_cli.config.load_config_readonly", return_value=cfg),
        patch("agent.model_metadata.get_model_context_length", return_value=probed_ctx),
        patch.object(cc_mod, "get_model_context_length", return_value=probed_ctx),
    ):
        from run_agent import AIAgent

        return AIAgent(
            model="local-pilot",
            provider="custom",
            api_key="local",
            base_url=base_url,
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )


def _cfg(compression=False, **model):
    return {
        "agent": {},
        "model": {"context_length": 8192, **model},
        "compression": {"enabled": compression},
    }


@pytest.mark.parametrize("served", [None, 8192])
def test_pinned_local_window_without_auto_compression_is_admitted(served):
    agent = _build_custom_agent(_cfg(), served_num_ctx=served)
    assert agent.context_compressor.context_length == 8192


@pytest.mark.parametrize(
    "cfg, base_url, served",
    [
        (_cfg(compression=True), LOCAL, None),  # automatic compression keeps the floor
        (
            _cfg(),
            "https://example.invalid/v1",
            None,
        ),  # only a local server can be pinned
        (_cfg(ollama_num_ctx=16384), LOCAL, None),  # configured served window > pin
        (_cfg(), LOCAL, 4096),  # detected served window < pin
    ],
)
def test_floor_still_applies_outside_the_explicit_local_pin(cfg, base_url, served):
    with pytest.raises(ValueError, match="below the minimum"):
        _build_custom_agent(cfg, base_url=base_url, served_num_ctx=served)
