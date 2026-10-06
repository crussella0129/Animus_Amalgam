"""Drive HermesCLI itself for one lab session; experimental bounds never change live settings.

The repository is importable only through this process's own ``sys.path``: the environment the
CLI and its tools inherit carries no repository path.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time

from wire import tool_call_validity

REPO = Path(__file__).resolve().parents[2]
TASKS = Path(__file__).resolve().parent / "tasks"

FIXED_PROMPTS = {
    "smoke": ["Reply with exactly AMALGAM_OK. Do not use tools."],
    "decode-sample": [
        "Write the integers from 1 to 40 in order, separated by single spaces. "
        "Output nothing else. Do not use tools."
    ],
    "main-cancel": [
        "Write a numbered list of 100 distinct prime numbers. No introduction."
    ],
}
EXPECTED = {
    "smoke": "AMALGAM_OK",
    "decode-sample": " ".join(str(i) for i in range(1, 41)),
}


def workload_prompts(workload):
    if workload in FIXED_PROMPTS:
        return FIXED_PROMPTS[workload]
    task, _, span = workload.partition(":")
    turns = json.loads((TASKS / task / "turns.json").read_text(encoding="utf-8"))
    if span == "all":
        return turns
    first, last = (int(x) for x in span.split("-"))
    return turns[first - 1 : last]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--arm", required=True, help="session arm as JSON")
    parser.add_argument("--workload", required=True)
    parser.add_argument("--max-turns", type=int, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--interrupt-file", type=Path, required=True)
    args = parser.parse_args()
    arm = json.loads(args.arm)
    sys.path.insert(0, str(REPO))
    os.chdir(args.fixture)
    from cli import HermesCLI

    uses_tools = args.workload.startswith("long")
    started = time.monotonic()
    cli = HermesCLI(
        model="amalgam-pilot",
        provider="custom",
        base_url=args.url,
        api_key="local-pilot",
        toolsets=["terminal"] if uses_tools else [],
        reasoning=None if arm["thinking"] else "none",
        max_turns=args.max_turns,
        ignore_rules=True,
    )
    cli._single_query_mode = True
    if not cli._init_agent():
        raise RuntimeError("Hermes CLI agent initialization failed")
    cli.agent.max_tokens = arm["output_cap"]
    ready = time.monotonic() - started

    def watch_interrupt():
        while not args.interrupt_file.exists():
            time.sleep(0.1)
        cli.agent.interrupt(hard_cancel=True, tool_reason="lab cancellation")

    threading.Thread(target=watch_interrupt, daemon=True).start()
    responses = []
    for prompt in workload_prompts(args.workload):
        if args.interrupt_file.exists():
            break
        responses.append(cli.chat(prompt))
    known = {t["function"]["name"] for t in (cli.agent.tools or [])}
    result = {
        "session_id": cli.session_id,
        "cli_start_seconds": ready,
        "responses": responses,
        "conversation": cli.conversation_history,
        "tool_calls": tool_call_validity(cli.conversation_history, known),
    }
    if args.workload in EXPECTED:
        result["expected_answer"] = responses == [EXPECTED[args.workload]]
    args.result.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.workload in EXPECTED and not result["expected_answer"]:
        raise SystemExit(
            f"{args.workload} answer did not match the independent expected value"
        )


if __name__ == "__main__":
    main()
