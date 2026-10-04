"""The lab wire bounds Hermes traffic, streams it and receipts it (Sprint 2 T-207, Sprint 3 T-211).

A lab-component integration test: the real ``Wire`` over loopback HTTP against a capture
backend standing in for llama.cpp's template, tokenize, slots and streaming completion
endpoints. Regressions: attempt 02 (a cancel blocked the supervisor until the backend's
batch ended) and attempt 10 (an immediate sequential retry was refused as concurrent).
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import urllib.error
import urllib.request

import pytest

from evals.local_qualification.wire import Wire

INPUT_LIMIT = 50
ARM_THINKING = {"output_cap": 768, "thinking": True, "reasoning_budget": 256}
ARM_PLAIN = {"output_cap": 512, "thinking": False, "reasoning_budget": None}
GREEDY = {
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": 0,
    "min_p": 0.0,
    "presence_penalty": 0.0,
    "repeat_penalty": 1.0,
}


class CaptureBackend:
    """Renders messages and tool schemas as a chat template does, counts words as tokens,
    and streams a progress chunk, reasoning and content deltas and a final timings chunk."""

    def __init__(self):
        self.completions = []
        self.chunk_delay = 0.0  # seconds between streamed chunks
        self.tokenize_delay = 0.0  # the wire's post-response accounting runs /tokenize
        self.slots = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _json(self, value):
                data = json.dumps(value).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._json(owner.slots)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/apply-template":
                    text = [m.get("content") or "" for m in body["messages"]]
                    text += [
                        t["function"]["description"] for t in body.get("tools") or []
                    ]
                    return self._json({"prompt": " ".join(text)})
                if self.path == "/tokenize":
                    time.sleep(owner.tokenize_delay)
                    return self._json({
                        "tokens": list(range(len(body["content"].split())))
                    })
                owner.completions.append(body)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                chunks = [
                    {
                        "prompt_progress": {
                            "total": 3,
                            "cache": 0,
                            "processed": 3,
                            "time_ms": 1,
                        }
                    },
                    {"choices": [{"delta": {"reasoning_content": "think it over"}}]},
                    {"choices": [{"delta": {"content": "ok done"}}]},
                    {
                        "id_slot": 0,
                        "choices": [{"delta": {}, "finish_reason": "stop"}],
                        "timings": {
                            "cache_n": 0,
                            "prompt_n": 3,
                            "prompt_ms": 30.0,
                            "predicted_n": 5,
                            "predicted_ms": 1500.0,
                            "predicted_per_second": 3.3,
                        },
                    },
                ]
                try:
                    for chunk in chunks:
                        self.wfile.write(
                            b"data: " + json.dumps(chunk).encode() + b"\n\n"
                        )
                        self.wfile.flush()
                        time.sleep(owner.chunk_delay)
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except OSError:
                    pass  # the wire hung up (a cancel)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"


def _budget(remaining):
    consumed = []

    def consume():
        if len(consumed) >= remaining:
            raise RuntimeError("aggregate request budget exhausted")
        consumed.append(1)
        return len(consumed)

    return consume, consumed


@pytest.fixture
def make_lab():
    opened = []

    def make(remaining=18, arm=ARM_PLAIN, request_limit=24, predictor=None):
        backend = CaptureBackend()
        records = []
        consume, consumed = _budget(remaining)
        wire = Wire(
            backend.url,
            "ephemeral-token",
            lambda kind, **data: records.append({"kind": kind, **data}),
            consume,
            30,
            0.05,
            predictor,
        )
        wire.begin_session(1, arm, GREEDY, 42, INPUT_LIMIT, request_limit)
        opened.append((wire, backend))
        return backend, wire, records, consumed

    yield make
    for wire, backend in opened:
        wire.close()
        backend.server.shutdown()


def _body(words, model="amalgam-pilot", max_tokens=None, tool_words=0, stream=True):
    body = {
        "model": model,
        "stream": stream,
        "reasoning_effort": "none",
        "messages": [{"role": "user", "content": " ".join(["w"] * words)}],
    }
    if tool_words:
        body["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": "terminal",
                    "description": " ".join(["t"] * tool_words),
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    return body


def _post(wire, body, stop_at_done=False):
    """POST like the OpenAI client: with ``stop_at_done`` the client is finished at
    ``[DONE]`` and does not wait for the server to close the connection."""
    request = urllib.request.Request(
        wire.url + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    if not stop_at_done:
        with response:
            return response.status, response.read()
    lines = []
    while line := response.readline():
        lines.append(line)
        if line.strip() == b"data: [DONE]":
            break
    response.fp = None  # abandon the connection rather than drain it
    return response.status, b"".join(lines)


def test_admitted_request_is_bounded_once_and_original_is_preserved(make_lab):
    backend, wire, records, consumed = make_lab(arm=ARM_THINKING)
    status, payload = _post(wire, _body(10, max_tokens=4096, tool_words=5))
    assert status == 200 and b"[DONE]" in payload
    assert len(backend.completions) == 1 and len(consumed) == 1
    sent = backend.completions[0]
    assert sent["max_tokens"] == ARM_THINKING["output_cap"]
    assert sent["chat_template_kwargs"] == {"enable_thinking": True}
    assert sent["reasoning_budget_tokens"] == ARM_THINKING["reasoning_budget"]
    assert {k: sent[k] for k in GREEDY} == GREEDY and sent["seed"] == 42
    assert sent["stream"] is True and sent["return_progress"] is True
    assert "reasoning_effort" not in sent  # thinking is set only by the template kwargs
    request = next(r for r in records if r["kind"] == "request")
    assert request["original_body"]["max_tokens"] == 4096
    assert request["input_tokens"] == 15 and wire.failure is None


@pytest.mark.parametrize(
    "words, tool_words, model",
    [
        (INPUT_LIMIT + 1, 0, "amalgam-pilot"),  # messages alone exceed the ceiling
        (10, INPUT_LIMIT, "amalgam-pilot"),  # tool schemas push it over
        (10, 0, "other-model"),  # misrouted
    ],
)
def test_oversized_or_misrouted_request_never_reaches_generation(
    make_lab, words, tool_words, model
):
    backend, wire, _records, consumed = make_lab()
    status, _ = _post(wire, _body(words, tool_words=tool_words, model=model))
    assert status == 422
    assert backend.completions == [] and consumed == []
    assert wire.failure  # the owner stops the attempt on any wire failure


def test_exhausted_request_budget_refuses_before_generation(make_lab):
    backend, wire, _records, consumed = make_lab(remaining=0)
    status, _ = _post(wire, _body(10))
    assert status == 422
    assert backend.completions == [] and consumed == []
    assert "budget exhausted" in wire.failure


def test_session_request_limit(make_lab):
    backend, wire, _records, consumed = make_lab(request_limit=1)
    assert _post(wire, _body(10))[0] == 200
    assert _post(wire, _body(10))[0] == 422
    assert len(backend.completions) == 1 and len(consumed) == 1
    assert "session request limit" in wire.failure


def test_wire_streams_and_reassembles(make_lab):
    backend, wire, _records, _consumed = make_lab(arm=ARM_THINKING)
    _status, streamed = _post(wire, _body(10, stream=True))
    assert b"prompt_progress" not in streamed and b"[DONE]" in streamed
    _status, folded = _post(wire, _body(10, stream=False))
    response = json.loads(folded)
    message = response["choices"][0]["message"]
    assert message["content"] == "ok done"
    assert message["reasoning_content"] == "think it over"
    assert response["choices"][0]["finish_reason"] == "stop"
    # Both clients went upstream streaming, with progress requested.
    assert all(c["stream"] and c["return_progress"] for c in backend.completions)


def test_slot_counters_are_progress_while_deltas_are_withheld(make_lab):
    backend, wire, _records, _consumed = make_lab()
    backend.chunk_delay = 0.6
    backend.slots = [
        {
            "is_processing": True,
            "n_prompt_tokens_processed": 3,
            "next_token": [{"n_decoded": 1}],
        }
    ]
    sender = threading.Thread(target=lambda: _post(wire, _body(10)))
    sender.start()
    deadline = time.monotonic() + 5
    while (
        wire.active is None or wire.active.get("first_event") is None
    ) and time.monotonic() < deadline:
        time.sleep(0.01)
    backend.slots = [
        {
            "is_processing": True,
            "n_prompt_tokens_processed": 3,
            "next_token": [{"n_decoded": 2}],
        }
    ]
    while (
        wire.active is not None
        and "slots_progress" not in wire.active
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    seen = wire.active is not None and "slots_progress" in wire.active
    sender.join()
    assert seen


def test_receipt_fields_complete_or_named_missing(make_lab):
    _backend, wire, records, _consumed = make_lab(
        arm=ARM_THINKING, predictor=lambda uncached, cap: 1.0 + uncached + cap
    )
    _post(wire, _body(10))
    end = next(r for r in records if r["kind"] == "response_end")
    assert end["timings"]["prompt_n"] == 3 and end["timings"]["predicted_n"] == 5
    assert end["finish_reason"] == "stop" and end["id_slot"] == 0
    assert end["reasoning_tokens"] == 3 and end["visible_tokens"] == 2
    assert end["meaningful_first_token_seconds"] is not None
    assert end["predicted_initial_seconds"] and end["predicted_rearmed_seconds"]
    assert (
        "kernel_compiled" in end
    )  # None when no kernel cache is wired: named, not dropped


def test_cancel_returns_promptly_and_is_recorded_as_a_cancel(make_lab):
    """Attempt 02: closing the upstream waited for the reader's lock until the backend's
    next chunk; the supervisor froze and its lag guard stopped the attempt."""
    backend, wire, records, _consumed = make_lab()
    backend.chunk_delay = 3.0
    sender = threading.Thread(target=lambda: _post(wire, _body(10)))
    sender.start()
    deadline = time.monotonic() + 5
    while (
        wire.active is None or wire.active.get("first_event") is None
    ) and time.monotonic() < deadline:
        time.sleep(0.01)
    started = time.monotonic()
    wire.cancel_active()
    elapsed = time.monotonic() - started
    sender.join(timeout=10)
    assert elapsed < 0.5
    assert any(r["kind"] == "response_cancelled" for r in records)
    assert wire.failure is None


def test_sequential_request_after_done_is_accepted_and_concurrent_is_refused(make_lab):
    """Attempt 10: a retry sent at [DONE] arrived during the previous handler's accounting
    and was refused as concurrent, stopping R2."""
    backend, wire, _records, _consumed = make_lab()
    backend.tokenize_delay = 0.8
    assert _post(wire, _body(10), stop_at_done=True)[0] == 200
    assert _post(wire, _body(10), stop_at_done=True)[0] == 200
    assert wire.failure is None
    backend.tokenize_delay = 0.0
    backend.chunk_delay = 1.0
    results = {}
    first = threading.Thread(target=lambda: results.update(a=_post(wire, _body(10))[0]))
    first.start()
    time.sleep(0.5)  # the first request is mid-stream
    results["b"] = _post(wire, _body(10))[0]
    first.join()
    assert results == {"a": 200, "b": 409}
    assert "concurrent" in wire.failure
