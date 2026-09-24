"""Inspect and bound the real CLI's local wire; no synthetic model replies."""

import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import urllib.request


class Wire:
    def __init__(self, backend_url, token, record, consume_request, input_limit):
        self.backend_url, self.token = backend_url, token
        self.record, self.consume_request = record, consume_request
        self.active = None
        self.failure = None
        self.lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                try:
                    value = owner.backend(self.path)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps(value).encode())
                except Exception as exc:
                    self.send_error(503, type(exc).__name__)

            def do_POST(self):
                if self.path != "/v1/chat/completions" or not owner.lock.acquire(False):
                    self.send_error(409, "Unexpected endpoint or concurrent request")
                    owner.failure = "unexpected or concurrent inference request"
                    return
                connection = None
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 1024 * 1024:
                        raise ValueError("request size outside pilot bound")
                    body = json.loads(self.rfile.read(size))
                    original = dict(body)
                    if body.get("model") != "amalgam-pilot":
                        raise ValueError("wrong model")
                    # The lab's backend budget covers auxiliary calls, whose
                    # production helper intentionally omits user output caps.
                    # Preserve both bodies so this is never mistaken for an
                    # unmodified stock-Hermes request.
                    body.update(
                        max_tokens=128,
                        temperature=0,
                        top_p=1,
                        seed=42,
                        chat_template_kwargs={"enable_thinking": False},
                    )
                    body.pop("max_completion_tokens", None)
                    prompt = owner.backend("/apply-template", body)["prompt"]
                    tokens = owner.backend(
                        "/tokenize",
                        {
                            "content": prompt,
                            "add_special": False,
                            "parse_special": True,
                        },
                    )["tokens"]
                    if len(tokens) > input_limit:
                        owner.record(
                            "rejected_request",
                            input_tokens=len(tokens),
                            original_body=original,
                        )
                        raise ValueError(
                            f"rendered input {len(tokens)} exceeds {input_limit}"
                        )
                    request_id = owner.consume_request()
                    owner.active = {
                        "request_id": request_id,
                        "started": time.monotonic(),
                    }
                    owner.record(
                        "request",
                        request_id=request_id,
                        original_body=original,
                        backend_body=body,
                        input_tokens=len(tokens),
                        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                        token_ids=tokens,
                    )
                    port = int(owner.backend_url.rsplit(":", 1)[1])
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", port, timeout=300
                    )
                    connection.request(
                        "POST",
                        self.path,
                        json.dumps(body),
                        {
                            "Content-Type": "application/json",
                            "Authorization": "Bearer " + owner.token,
                        },
                    )
                    response = connection.getresponse()
                    self.send_response(response.status)
                    self.send_header(
                        "Content-Type",
                        response.getheader("Content-Type", "application/json"),
                    )
                    self.end_headers()
                    first = None
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        if line.startswith(b"data: {"):
                            data = json.loads(line[6:])
                            meaningful = any(
                                c.get("delta", {}).get("content")
                                or c.get("delta", {}).get("tool_calls")
                                for c in data.get("choices", [])
                            )
                            if meaningful and first is None:
                                first = time.monotonic() - owner.active["started"]
                            owner.record("chunk", request_id=request_id, data=data)
                        self.wfile.write(line)
                        self.wfile.flush()
                    owner.record(
                        "response_end",
                        request_id=request_id,
                        status=response.status,
                        seconds=time.monotonic() - owner.active["started"],
                        meaningful_first_token_seconds=first,
                    )
                except Exception as exc:
                    owner.failure = f"{type(exc).__name__}: {exc}"
                    owner.record("wire_failure", error=owner.failure)
                    try:
                        self.send_error(
                            422, "pilot gate rejected or failed; inspect local receipt"
                        )
                    except OSError:
                        pass
                finally:
                    if connection is not None:
                        connection.close()
                    owner.active = None
                    owner.lock.release()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def backend(self, path, body=None):
        request = urllib.request.Request(
            self.backend_url + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.token,
            },
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.load(response)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        # The backend has already exited; allow its response thread to finish
        # recording before the owner's receipt stream is closed.
        if not self.lock.acquire(timeout=1):
            raise RuntimeError("wire handler did not settle during owned cleanup")
        self.lock.release()
