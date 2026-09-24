# Local Hermes operational lab

Sprint 2 operates the real Hermes CLI in a disposable home and fixture
directory. Formal unit/integration verification follows operational confidence.
See the locked Sprint 2 plans for the approved limits and task sequence.

The existing Python runtime already supplies suspended child creation and
Windows kill-on-close Job Object ownership in
`hermes_cli.local_runtime.processes.spawn_server`. Reusing that implementation
avoids a second process controller. Python here is glue for existing Hermes
interfaces; no new Rust owner is needed unless operation exposes a gap.

The disposable environment lives under ignored `.hermes-sandbox/s2/` and is
installed from the repository's unchanged `uv.lock`. The live Hermes profile,
environment and model files are not edited. Private raw evidence stays in the
sandbox; sanitized receipts are published in the Sprint Book.

The lab records both the CLI's original request and the request delivered to
llama.cpp. Its local wire guard applies the frozen 128-token/sampling budget
to both main and auxiliary traffic and checks the backend-rendered prompt
before generation. Production compression deliberately omits user caps; this
experiment does not restore those caps globally or pretend that its bounded
request is an unmodified stock-Hermes request. This is an operational probe,
not the later native/static comparison.
