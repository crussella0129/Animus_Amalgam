"""Hidden verifier, pre-check and contamination scan for the long multi-file task.

Lives outside the fixture so the model never sees it. Scores come from the fixture's state
alone, through the task interpreter in a separate process, never from the model's claims.

    python verify_long.py build-reference   # run the reference path, record its tool outputs
    python verify_long.py score <fixture> --python <task interpreter>
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
TASK = HERE / "tasks" / "long"
ITEMS = ("remove_guard", "discount", "total", "low_stock")
# Echoed reasoning a thinking arm may add to every replayed assistant turn (its budget).
ECHO_RESERVE_PER_REQUEST = 256

_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
results = {}

def item(name):
    def run(fn):
        try:
            results[name] = {"pass": bool(fn())}
        except Exception as exc:
            results[name] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}
    return run

@item("remove_guard")
def _():
    from inventory.models import Inventory
    inv = Inventory()
    inv.add("bolt", 0.5, 3)
    try:
        inv.remove("bolt", 5)
    except ValueError:
        pass
    else:
        return False
    if inv.quantity("bolt") != 3:
        return False
    inv.remove("bolt", 2)
    return inv.quantity("bolt") == 1

@item("discount")
def _():
    from inventory.models import Item
    from inventory.pricing import line_price
    return (
        line_price(Item("nut", 2.0, 10, 25)) == 15.0
        and line_price(Item("washer", 0.1, 50)) == 5.0
        and line_price(Item("gear", 4.0, 3, 50)) == 6.0
    )

@item("total")
def _():
    import inventory.report as report
    from inventory.models import Inventory
    # Scored apart from the discount defect: the total must sum whatever line_price returns.
    report.line_price = lambda i: round(
        i.unit_price * (1 - i.discount_percent / 100) * i.quantity, 2)
    inv = Inventory()
    inv.add("nut", 2.0, 10, 25)
    inv.add("washer", 0.1, 50)
    inv.add("gear", 4.0, 3, 50)
    return report.total_value(inv) == 26.0

@item("low_stock")
def _():
    from inventory.models import Inventory
    inv = Inventory()
    for name, quantity in (("washer", 5), ("bolt", 1), ("nut", 0), ("gear", 10)):
        inv.add(name, 1.0, quantity)
    if list(inv.low_stock(5)) != ["bolt", "nut"] or list(inv.low_stock(0)) != []:
        return False
    import check
    named = [c for c in check.CHECKS if "low_stock" in getattr(c, "__name__", "")]
    return bool(named) and all(c() for c in named)

print(json.dumps(results))
"""


def score(fixture: Path, python: Path) -> dict:
    """The 4 items from fixture state; a crashed or hung probe scores nothing."""
    try:
        done = subprocess.run(
            [str(python), "-E", "-s", "-B", "-c", _PROBE, str(fixture)],
            cwd=fixture,
            capture_output=True,
            text=True,
            timeout=60,
            env={"SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PATH": ""},
        )
        items = json.loads(done.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
        items = {name: {"pass": False, "error": f"probe: {exc}"} for name in ITEMS}
    return {
        "items": items,
        "passed": sum(bool(items.get(n, {}).get("pass")) for n in ITEMS),
        "of": len(ITEMS),
    }


# Glob characters stay in the token: */.git/* is a relative pattern, not /.git.
_CANDIDATE = re.compile(r"[\w.~$%{}:\\/+*?-]+")
_VAR = re.compile(r"\$\{(\w+)\}|\$(\w+)|%(\w+)%")
# Shell variables the command binds itself; their values are checked where they are bound.
_LOCAL = re.compile(r"\bfor\s+(\w+)\s+in\b|\b(\w+)=(?!=)|\bread\s+(?:-\w+\s+)*(\w+)")


def _path_candidates(command: str):
    local = {g for m in _LOCAL.finditer(command) for g in m.groups() if g}
    for token in _CANDIDATE.findall(command):
        # Trailing punctuation only: a leading "." is part of "./x".
        token = re.sub(r"(?<=\w)\.$", "", token.rstrip(",;:"))
        names = [g for m in _VAR.finditer(token) for g in m.groups() if g]
        if names and all(n in local for n in names):
            continue
        # A bare "/" is not a candidate: it is also division in inline code, and Git
        # Bash's / is its own install tree, so reaching the drive needs /c/ or C:\.
        if token in ("..", "~"):
            yield token
            continue
        if "://" in token or not re.search(r"\w", token.replace("$", "")):
            continue
        if token.startswith("\\") and not token.startswith("\\\\"):
            # A drive-less root path looks exactly like a string escape in inline code
            # (\n); agents name Windows paths with a drive, which is still checked.
            continue
        if (
            token.startswith(("/", "~", "../", "..\\", "$", "%"))
            or re.match(r"[A-Za-z]:[\\/]", token)
            or "/" in token
            or "\\" in token
        ):
            yield token


def _resolve(token: str, fixture: Path, msys_root: Path | None, session_temp: Path):
    """The absolute path a token names, or None when it cannot be resolved."""
    unresolved = []

    def expand(match):
        name = next(g for g in match.groups() if g)
        if name in ("PWD", "OLDPWD"):
            return str(fixture)
        unresolved.append(name)
        return match.group(0)

    token = _VAR.sub(expand, token)
    if unresolved:
        return None
    if token == "~" or token.startswith(("~/", "~\\")):
        return None  # the session home is never inside the fixture
    drive = re.match(r"/([A-Za-z])(/.*)?$", token)
    if drive and len(token) > 1:
        return Path(f"{drive.group(1)}:/{(drive.group(2) or '/').lstrip('/')}")
    if token == "/tmp" or token.startswith("/tmp/"):
        return session_temp / token[len("/tmp/") :]  # Git Bash mounts /tmp on TEMP
    if token.startswith("/"):
        return (msys_root / token.lstrip("/")) if msys_root else None
    path = Path(token)
    return path if path.is_absolute() else fixture / path


def screened(conversation) -> dict:
    """What an L4 screen saw, so an empty screen cannot pass as a clean one."""
    return {
        "messages": len(conversation),
        "tool_calls": sum(len(m.get("tool_calls") or []) for m in conversation),
    }


def contamination(
    conversation: list, fixture: Path, allowlist: list, session_temp: Path
) -> list:
    """Terminal tool paths that resolve outside the fixture and off the allowlist (L4).

    ``session_temp`` is the TEMP the session ran with, where Git Bash mounts ``/tmp``.
    """
    fixture = fixture.resolve()
    allowed = [Path(a).resolve() for a in allowlist]
    msys_root = next(
        (p.parents[1] for p in allowed if p.parts[-2:] == ("usr", "bin")), None
    )
    found = []
    for message in conversation:
        for call in message.get("tool_calls") or []:
            fn = call.get("function") or {}
            if fn.get("name") != "terminal":
                continue
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                continue
            tokens = list(_path_candidates(str(args.get("command", ""))))
            if args.get("workdir"):
                tokens.append(str(args["workdir"]))
            for token in tokens:
                if token.startswith("/dev/"):
                    continue
                path = _resolve(token, fixture, msys_root, session_temp)
                if path is not None:
                    path = Path(os.path.normpath(path))
                    if path == fixture or fixture in path.parents:
                        continue
                    if any(path == a or a in path.parents for a in allowed):
                        continue
                found.append({
                    "token": token,
                    "resolved": None if path is None else str(path),
                })
    return found


def reference_messages() -> list:
    """The reference path as the chat messages Hermes would replay, outputs included."""
    turns = json.loads((TASK / "turns.json").read_text(encoding="utf-8"))
    reference = json.loads((TASK / "reference.json").read_text(encoding="utf-8"))
    messages, n = [], 0
    for user, steps in zip(turns, reference["turns"], strict=True):
        messages.append({"role": "user", "content": user})
        for step in steps:
            if "reply" in step:
                messages.append({"role": "assistant", "content": step["reply"]})
                continue
            n += 1
            call_id = f"call_ref_{n}"
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": step["command"]}),
                        },
                    }
                ],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(
                    {
                        "output": step["output"],
                        "exit_code": step["exit_code"],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
            })
    return messages


def precheck(backend, original: dict, smallest_cap: int, input_ceiling: int) -> dict:
    """L3 on the live backend with Hermes's own system prompt and tools from ``original``.

    ``backend(path, body)`` is a metadata probe (template and tokenizer only, no generation).
    """
    messages = reference_messages()
    requests = sum(1 for m in messages if m["role"] == "assistant")
    system = [m for m in original.get("messages", []) if m.get("role") == "system"]
    body = {"messages": system + messages}
    if original.get("tools"):
        body["tools"] = original["tools"]
    prompt = backend("/apply-template", body)["prompt"]
    peak = len(
        backend(
            "/tokenize",
            {"content": prompt, "add_special": False, "parse_special": True},
        )["tokens"]
    )
    largest = max(
        len(
            backend(
                "/tokenize",
                {
                    "content": m["content"]
                    or json.dumps({
                        "name": "terminal",
                        "arguments": json.loads(
                            m["tool_calls"][0]["function"]["arguments"]
                        ),
                    })
                },
            )["tokens"]
        )
        for m in messages
        if m["role"] == "assistant"
    )
    worst = peak + ECHO_RESERVE_PER_REQUEST * requests
    return {
        "reference_requests": requests,
        "largest_reference_edit_tokens": largest,
        "smallest_cap": smallest_cap,
        "peak_rendered_tokens": peak,
        "echo_reserve_tokens": ECHO_RESERVE_PER_REQUEST * requests,
        "input_ceiling": input_ceiling,
        "passed": requests >= 20 and largest <= smallest_cap and worst <= input_ceiling,
    }


def build_reference(python: Path) -> None:
    """Run the reference path on a fixture copy; record outputs; prove 0/4 → 4/4."""
    sys.path.insert(0, str(HERE.parents[1]))
    from tools.environments.local import _find_bash, _git_bash_bin_dirs

    bash = _find_bash()
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([
        str(python.parent),
        *_git_bash_bin_dirs(),
        env["PATH"],
    ])
    reference_path = TASK / "reference.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "fixture"
        shutil.copytree(TASK / "fixture", fixture)
        scores = [score(fixture, python)["passed"]]
        for steps in reference["turns"]:
            for step in steps:
                if "command" not in step:
                    continue
                done = subprocess.run(
                    [bash, "-c", step["command"]],
                    cwd=fixture,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                step["output"] = (done.stdout + done.stderr).replace(tmp, "<tmp>")
                step["exit_code"] = done.returncode
            scores.append(score(fixture, python)["passed"])
    if scores[0] != 0 or scores[3] < 1 or scores[-1] != len(ITEMS):
        raise SystemExit(f"reference path does not score 0 → (turn 3) ≥1 → 4: {scores}")
    reference["scores_after_turn"] = scores
    # LF on every host: the task-corpus digest hashes these bytes.
    reference_path.write_bytes((json.dumps(reference, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({"scores_after_turn": scores}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-reference")
    build.add_argument("--python", type=Path, default=Path(sys.executable))
    scoring = sub.add_parser("score")
    scoring.add_argument("fixture", type=Path)
    scoring.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    if args.command == "build-reference":
        build_reference(args.python)
    else:
        print(json.dumps(score(args.fixture, args.python), indent=1))


if __name__ == "__main__":
    main()
