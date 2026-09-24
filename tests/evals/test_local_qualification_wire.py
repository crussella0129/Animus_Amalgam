"""The lab wire guard bounds real Hermes traffic before generation (Sprint 2 T-207 D1/D2).

A loopback capture backend stands in for llama.cpp here; live inference evidence is the
published attempt receipts, not this test.
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
    def __init__(self):
        self.completions = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/apply-template":
                    reply = {"prompt": " ".join(m["content"] for m in body["messages"])}
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


@pytest.fixture
def lab():
    backend = CaptureBackend()
    records, consumed = [], []
    wire = Wire(
        backend.url,
        "ephemeral-token",
        lambda kind, **data: records.append({"kind": kind, **data}),
        lambda: consumed.append(1) or len(consumed),
        INPUT_LIMIT,
    )
    yield backend, wire, records, consumed
    wire.close()
    backend.server.shutdown()


def _post(wire, words, model="amalgam-pilot", max_tokens=None):
    body = {
        "model": model,
        "stream": True,
        "messages": [{"role": "user", "content": " ".join(["w"] * words)}],
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    request = urllib.request.Request(
        wire.url + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def test_admitted_request_is_bounded_once_and_original_is_preserved(lab):
    backend, wire, records, consumed = lab
    status, payload = _post(wire, words=10, max_tokens=4096)
    assert status == 200 and b"[DONE]" in payload
    assert len(backend.completions) == 1 and len(consumed) == 1
    sent = backend.completions[0]
    assert sent["max_tokens"] == 128
    assert sent["chat_template_kwargs"] == {"enable_thinking": False}
    request = next(r for r in records if r["kind"] == "request")
    assert request["original_body"]["max_tokens"] == 4096
    assert request["input_tokens"] == 10 and wire.failure is None


@pytest.mark.parametrize(
    "words, model", [(INPUT_LIMIT + 1, "amalgam-pilot"), (10, "other-model")]
)
def test_oversized_or_misrouted_request_never_reaches_generation(lab, words, model):
    backend, wire, _records, consumed = lab
    status, _ = _post(wire, words=words, model=model)
    assert status == 422
    assert backend.completions == [] and consumed == []
    assert wire.failure  # the owner stops the attempt on any wire failure
