"""Inspect and bound the real CLI's local wire; no synthetic model replies.

Every request goes upstream streaming with ``return_progress`` (the pinned llama.cpp sends
progress only on streaming requests). Progress chunks are consumed here and never reach the
client; a non-streaming client gets one reassembled response. The active slot's ``/slots``
counters are polled as a second progress signal, covering deltas the server's parser withholds.
"""

import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
import time
import urllib.request

# Thinking is controlled only through chat_template_kwargs; these would conflict upstream.
_CONFLICTING_FIELDS = ("max_completion_tokens", "reasoning_effort", "reasoning")


def bound_body(body, arm, sampling, seed):
    """The backend body for one request under a session arm (pure, for tests)."""
    bounded = {k: v for k, v in body.items() if k not in _CONFLICTING_FIELDS}
    bounded.update(
        sampling,
        seed=seed,
        max_tokens=arm["output_cap"],
        stream=True,
        return_progress=True,
        chat_template_kwargs={"enable_thinking": bool(arm["thinking"])},
    )
    bounded.pop("reasoning_budget_tokens", None)
    if arm["thinking"] and arm.get("reasoning_budget") is not None:
        bounded["reasoning_budget_tokens"] = arm["reasoning_budget"]
    return bounded


class Reassembler:
    """Folds streamed chat-completion deltas into one non-streaming response."""

    def __init__(self):
        self.content, self.reasoning, self.tool_calls = [], [], {}
        self.finish_reason, self.last = None, {}

    def add(self, data):
        self.last = data
        for choice in data.get("choices", []):
            delta = choice.get("delta", {})
            self.content.append(delta.get("content") or "")
            self.reasoning.append(delta.get("reasoning_content") or "")
            for call in delta.get("tool_calls") or []:
                slot = self.tool_calls.setdefault(
                    call.get("index", 0),
                    {
                        "id": None,
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                slot["id"] = call.get("id") or slot["id"]
                fn = call.get("function") or {}
                slot["function"]["name"] += fn.get("name") or ""
                slot["function"]["arguments"] += fn.get("arguments") or ""
            self.finish_reason = choice.get("finish_reason") or self.finish_reason

    def message(self):
        message = {"role": "assistant", "content": "".join(self.content) or None}
        if any(self.reasoning):
            message["reasoning_content"] = "".join(self.reasoning)
        if self.tool_calls:
            message["tool_calls"] = [
                self.tool_calls[i] for i in sorted(self.tool_calls)
            ]
        return message

    def response(self):
        message = self.message()
        return {
            "id": self.last.get("id"),
            "object": "chat.completion",
            "created": self.last.get("created"),
            "model": self.last.get("model"),
            "choices": [
                {"index": 0, "message": message, "finish_reason": self.finish_reason}
            ],
            "usage": self.last.get("usage"),
        }


class Wire:
    def __init__(
        self,
        backend_url,
        token,
        record,
        consume_request,
        probe_timeout,
        observation_period,
        predictor=None,
        kernel_cache_bytes=None,
    ):
        self.backend_url, self.token = backend_url, token
        self.record, self.consume_request = record, consume_request
        self.probe_timeout, self.observation_period = probe_timeout, observation_period
        # predictor(uncached_tokens, output_cap) -> seconds; None while calibrating.
        self.predictor = predictor
        # kernel_cache_bytes() -> the backend's CUDA JIT cache size; growth marks compilation.
        self.kernel_cache_bytes = kernel_cache_bytes or (lambda: None)
        self.active = None
        self.last_slots = None
        self.failure = None
        self.session = None
        # One request in flight: _in_flight holds the owning handler's token from
        # acceptance until the client has the whole response, and _gate makes every
        # check-and-set atomic. lock then serializes the accounting tail, which a
        # sequential client never waits for: it sends its next request at [DONE]
        # (attempt 10's truncated-tool-call retry was refused as concurrent). Only the
        # owner may release the token, so a finishing handler cannot clear the claim of
        # the request already waiting behind it.
        self._gate = threading.Lock()
        self._in_flight = None
        self.lock = threading.Lock()
        self._upstream_sock = None
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
                owner._handle(self)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def begin_session(
        self,
        session_id,
        arm,
        sampling,
        seed,
        input_ceiling,
        request_limit,
        precheck=None,
    ):
        self.failure = None
        self.session = {
            "id": session_id,
            "arm": arm,
            "sampling": sampling,
            "seed": seed,
            "input_ceiling": input_ceiling,
            "request_limit": request_limit,
            "requests": 0,
            "last_finish": None,
            "first_request": None,
            # precheck(original_body) -> result; runs once, on the first request, before generation.
            "precheck": precheck,
        }

    def end_session(self):
        session, self.session = self.session, None
        return session

    @staticmethod
    def probe(base_url, token, path, timeout, body=None, method=None):
        request = urllib.request.Request(
            base_url + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
            method=method,
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def backend(self, path, body=None, method=None):
        return self.probe(
            self.backend_url, self.token, path, self.probe_timeout, body, method
        )

    def probe_slots(self):
        return self.backend("/slots")

    def slot_busy(self, timeout):
        """llama.cpp answers /slots only between batches, so a timeout means still busy."""
        try:
            slots = self.probe(
                self.backend_url, self.token, "/slots", timeout, None, None
            )
        except OSError:
            return True
        return any(s.get("is_processing") for s in slots)

    def erase_slot(self):
        return self.backend("/slots/0?action=erase", {}, method="POST")

    def cancel_active(self):
        """Shut the upstream socket down; llama.cpp stops the slot when its client leaves.

        Never close() here: the response's buffered reader holds its lock while the handler
        thread blocks in readline, so close() waits until the backend's current batch ends.
        """
        active, sock = self.active, self._upstream_sock
        if active is not None:
            active["cancelled"] = True
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _progress(self, **fields):
        active = self.active
        if active is not None:
            now = time.monotonic()
            if active.get("first_event") is None:
                active["first_event"] = now - active["started"]
            active.update(last_progress=now, **fields)

    def _poll_slots(self, request_id):
        seen = None
        while self.active is not None and self.active["request_id"] == request_id:
            try:
                slots = self.backend("/slots")
                self.last_slots = slots
                working = [s for s in slots if s.get("is_processing")]
                if working and self.active is not None:
                    self.active.setdefault("slot_seen", working[0].get("id"))
                counters = [
                    (
                        s.get("n_prompt_tokens_processed"),
                        s.get("next_token", [{}])[0].get("n_decoded")
                        if isinstance(s.get("next_token"), list)
                        else s.get("n_decoded"),
                    )
                    for s in slots
                    if s.get("is_processing")
                ]
                if counters and counters != seen:
                    if seen is not None:
                        self._progress(slots_progress=counters)
                    seen = counters
            except (OSError, ValueError, KeyError, IndexError):
                pass
            time.sleep(self.observation_period)

    def _reject(self, handler, reason, **data):
        self.failure = reason
        self.record("wire_failure", error=reason, **data)
        try:
            handler.send_error(
                422, "pilot gate rejected or failed; inspect local receipt"
            )
        except OSError:
            pass

    def _release_in_flight(self, token):
        with self._gate:
            if self._in_flight is token:
                self._in_flight = None

    def _handle(self, handler):
        token = object()
        with self._gate:
            refused = (
                handler.path != "/v1/chat/completions" or self._in_flight is not None
            )
            if not refused:
                self._in_flight = token
        if refused or not self.lock.acquire(timeout=self.probe_timeout):
            if not refused:
                self._release_in_flight(token)
            handler.send_error(409, "Unexpected endpoint or concurrent request")
            self.failure = "unexpected or concurrent inference request"
            return
        connection = None
        request_id = None
        try:
            session = self.session
            if session is None:
                raise ValueError("request outside a lab session")
            size = int(handler.headers.get("Content-Length", "0"))
            if not 0 < size <= 4 * 1024 * 1024:
                raise ValueError("request size outside pilot bound")
            original = json.loads(handler.rfile.read(size))
            if original.get("model") != "amalgam-pilot":
                raise ValueError("wrong model")
            client_streams = bool(original.get("stream"))
            body = bound_body(
                original, session["arm"], session["sampling"], session["seed"]
            )
            prompt = self.backend("/apply-template", body)["prompt"]
            tokens = len(
                self.backend(
                    "/tokenize",
                    {"content": prompt, "add_special": False, "parse_special": True},
                )["tokens"]
            )
            if tokens > session["input_ceiling"]:
                raise ValueError(
                    f"rendered input {tokens} exceeds {session['input_ceiling']}"
                )
            if session["requests"] >= session["request_limit"]:
                raise ValueError("session request limit reached")
            if session["precheck"] is not None:
                check, session["precheck"] = session["precheck"], None
                result = check(original)
                self.record("task_precheck", session=session["id"], **result)
                if not result["passed"]:
                    raise ValueError("task pre-check failed (L3)")
            request_id = self.consume_request()
            session["requests"] += 1
            messages = original.get("messages") or []
            session["last_messages"] = messages
            system = (
                messages[0]
                if messages and messages[0].get("role") == "system"
                else None
            )
            started = time.monotonic()
            kernel_start = self.kernel_cache_bytes()
            cap = session["arm"]["output_cap"]
            predicted = self.predictor(tokens, cap) if self.predictor else None
            self.active = {
                "request_id": request_id,
                "started": started,
                "last_progress": started,
                "phase": "pre_first_event",
                "input_tokens": tokens,
                "output_cap": cap,
                "first_token": None,
                "progress": None,
                "predicted_initial": predicted,
                "predicted_rearmed": None,
                "cancelled": False,
            }
            event = {
                "request_id": request_id,
                "session": session["id"],
                "original_body": original,
                "backend_body": body,
                "input_tokens": tokens,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "system_sha256": hashlib.sha256(
                    json.dumps(system, sort_keys=True).encode()
                ).hexdigest()
                if system
                else None,
                "tools_sha256": hashlib.sha256(
                    json.dumps(original.get("tools"), sort_keys=True).encode()
                ).hexdigest(),
                "client_streams": client_streams,
                "continuation_of_length_finish": session["last_finish"] == "length",
                "predicted_initial_seconds": predicted,
            }
            if session["first_request"] is None:
                session["first_request"] = {
                    k: event[k]
                    for k in (
                        "input_tokens",
                        "prompt_sha256",
                        "system_sha256",
                        "tools_sha256",
                    )
                }
            self.record("request", **event)
            threading.Thread(
                target=self._poll_slots, args=(request_id,), daemon=True
            ).start()
            port = int(self.backend_url.rsplit(":", 1)[1])
            connection = http.client.HTTPConnection("127.0.0.1", port)
            connection.connect()
            self._upstream_sock = connection.sock
            connection.request(
                "POST",
                handler.path,
                json.dumps(body),
                {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.token,
                },
            )
            response = connection.getresponse()
            if client_streams:
                handler.send_response(response.status)
                handler.send_header("Content-Type", "text/event-stream")
                handler.end_headers()
            folded = Reassembler()
            texts = {"reasoning": [], "content": []}
            timings = id_slot = None
            while True:
                line = response.readline()
                if not line:
                    break
                if not line.startswith(b"data: {"):
                    if client_streams and line.strip() == b"data: [DONE]":
                        handler.wfile.write(line + b"\n")
                        handler.wfile.flush()
                        self._release_in_flight(token)  # the client is done
                    continue
                data = json.loads(line[6:])
                if "prompt_progress" in data:
                    progress = data["prompt_progress"]
                    phase = (
                        "prefill"
                        if progress.get("processed", 0) < progress.get("total", 0)
                        else "decode"
                    )
                    if self.predictor and self.active["predicted_rearmed"] is None:
                        # First progress event: the exact uncached count is now known.
                        uncached = progress.get("total", 0) - progress.get("cache", 0)
                        self.active["predicted_rearmed"] = (
                            time.monotonic() - started + self.predictor(uncached, cap)
                        )
                    self._progress(phase=phase, progress=progress)
                    self.record("progress", request_id=request_id, **progress)
                    continue
                id_slot = data.get("id_slot", id_slot)
                timings = data.get("timings", timings)
                folded.add(data)
                for choice in data.get("choices", []):
                    delta = choice.get("delta", {})
                    texts["reasoning"].append(delta.get("reasoning_content") or "")
                    texts["content"].append(delta.get("content") or "")
                    meaningful = (
                        delta.get("content")
                        or delta.get("reasoning_content")
                        or delta.get("tool_calls")
                    )
                    if meaningful:
                        if self.active["first_token"] is None:
                            self.active["first_token"] = time.monotonic() - started
                        self._progress(phase="decode")
                if client_streams:
                    handler.wfile.write(line + b"\n")
                    handler.wfile.flush()
            if self.active["cancelled"]:
                raise ConnectionAbortedError("upstream shut down by the lab")
            if not client_streams:
                payload = json.dumps(folded.response()).encode()
                handler.send_response(response.status)
                handler.send_header("Content-Type", "application/json")
                handler.send_header("Content-Length", str(len(payload)))
                handler.end_headers()
                handler.wfile.write(payload)
            self._release_in_flight(token)  # delivered; accounting follows
            # Hermes may run this response's tool calls before any further request.
            session["last_messages"] = [*messages, folded.message()]
            split = {}
            for kind, parts in texts.items():
                text = "".join(parts)
                split[kind] = (
                    len(self.backend("/tokenize", {"content": text})["tokens"])
                    if text
                    else 0
                )
            session["last_finish"] = folded.finish_reason
            kernel_end = self.kernel_cache_bytes()
            self.record(
                "response_end",
                request_id=request_id,
                session=session["id"],
                status=response.status,
                seconds=time.monotonic() - started,
                meaningful_first_token_seconds=self.active["first_token"],
                first_event_seconds=self.active.get("first_event"),
                predicted_initial_seconds=self.active["predicted_initial"],
                predicted_rearmed_seconds=self.active["predicted_rearmed"],
                id_slot=id_slot
                if id_slot is not None
                else self.active.get("slot_seen"),
                id_slot_source="stream"
                if id_slot is not None
                else ("slots" if self.active.get("slot_seen") is not None else None),
                finish_reason=folded.finish_reason,
                timings=timings,
                reasoning_tokens=split["reasoning"],
                visible_tokens=split["content"],
                tool_calls=len(folded.tool_calls),
                progress=self.active.get("progress"),
                kernel_compiled=None
                if kernel_start is None
                else kernel_end > kernel_start,
            )
        except Exception as exc:
            # A request that never completes still keeps its timing (INT-0007 AC7).
            timing = (
                {
                    "seconds": time.monotonic() - self.active["started"],
                    "meaningful_first_token_seconds": self.active["first_token"],
                    "predicted_initial_seconds": self.active["predicted_initial"],
                    "predicted_rearmed_seconds": self.active["predicted_rearmed"],
                }
                if self.active is not None
                else {}
            )
            if self.active is not None and self.active["cancelled"]:
                # A lab-initiated cancel is an outcome, not a wire failure.
                self.record(
                    "response_cancelled",
                    request_id=request_id,
                    error=f"{type(exc).__name__}: {exc}",
                    **timing,
                )
            else:
                self._reject(
                    handler,
                    f"{type(exc).__name__}: {exc}",
                    request_id=request_id,
                    **timing,
                )
        finally:
            self._upstream_sock = None
            if connection is not None:
                connection.close()
            self.active = None
            self._release_in_flight(token)
            self.lock.release()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        # Let a response thread finish recording before the owner's receipt stream closes.
        if not self.lock.acquire(timeout=1):
            raise RuntimeError("wire handler did not settle during owned cleanup")
        self.lock.release()
