"""The lab wire guard bounds Hermes traffic before generation (Sprint 2 T-207 D1/D2).

This is a lab-component integration test: the real ``Wire`` over loopback HTTP against a
capture backend that stands in for llama.cpp's template/tokenize/completion endpoints.
The Hermes side of the boundary is evidenced live by the published attempt receipts.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import urllib.error
import urllib.request

import pytest

from evals.local_qualification.wire import Wire

INPUT_LIMIT = 50


class CaptureBackend:
    """Renders messages AND tool schemas, as a real chat template does, and counts
    whitespace-separated words as tokens."""

    def __init__(self):
        self.completions = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/apply-template":
                    text = [m["content"] for m in body["messages"]]
                    text += [
                        t["function"]["description"] for t in body.get("tools") or []
                    ]
                    reply = {"prompt": " ".join(text)}
                elif self.path == "/tokenize":
                    reply = {"tokens": list(range(len(body["content"].split())))}
                else:
                    owner.completions.append(body)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    chunk = {"choices": [{"delta": {"content": "ok"}}]}
                    self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
                    self.wfile.write(b"data: [DONE]\n\n")
                    return
                data = json.dumps(reply).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

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

    def make(remaining=18):
        backend = CaptureBackend()
        records = []
        consume, consumed = _budget(remaining)
        wire = Wire(
            backend.url,
            "ephemeral-token",
            lambda kind, **data: records.append({"kind": kind, **data}),
            consume,
            INPUT_LIMIT,
            backend_timeout=30,
        )
        opened.append((wire, backend))
        return backend, wire, records, consumed

    yield make
    for wire, backend in opened:
        wire.close()
        backend.server.shutdown()


def _post(wire, words, model="amalgam-pilot", max_tokens=None, tool_words=0):
    body = {
        "model": model,
        "stream": True,
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
    request = urllib.request.Request(
        wire.url + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def test_admitted_request_is_bounded_once_and_original_is_preserved(make_lab):
    backend, wire, records, consumed = make_lab()
    status, payload = _post(wire, words=10, max_tokens=4096, tool_words=5)
    assert status == 200 and b"[DONE]" in payload
    assert len(backend.completions) == 1 and len(consumed) == 1
    sent = backend.completions[0]
    assert sent["max_tokens"] == 128
    assert sent["chat_template_kwargs"] == {"enable_thinking": False}
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
    status, _ = _post(wire, words=words, tool_words=tool_words, model=model)
    assert status == 422
    assert backend.completions == [] and consumed == []
    assert wire.failure  # the owner stops the attempt on any wire failure


def test_exhausted_request_budget_refuses_before_generation(make_lab):
    backend, wire, _records, consumed = make_lab(remaining=0)
    status, _ = _post(wire, words=10)
    assert status == 422
    assert backend.completions == [] and consumed == []
    assert "budget exhausted" in wire.failure
