"""Drive HermesCLI itself; experimental budgets never change live settings."""

import argparse
import json
import os
from pathlib import Path
import sys
import subprocess
import threading
import time


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument(
        "--mode",
        choices=[
            "smoke",
            "operate",
            "workflow",
            "exercise",
            "main-cancel",
            "aux-cancel",
        ],
        required=True,
    )
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--interrupt-file", type=Path, required=True)
    args = parser.parse_args()
    if args.mode in ("workflow", "exercise"):
        # Fresh CLI processes share one already-admitted backend. Toolsets stay
        # fixed within each conversation and all calls retain the owner's budget.
        stages = (
            ("smoke", "operate", "main-cancel")
            if args.mode == "exercise"
            else ("smoke", "operate")
        )
        for mode in stages:
            stage_path = args.result.with_name("stage.json")
            pending = stage_path.with_suffix(".tmp")
            pending.write_text(json.dumps({"mode": mode}), encoding="utf-8")
            os.replace(pending, stage_path)
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--lab",
                    str(args.lab),
                    "--url",
                    args.url,
                    "--mode",
                    mode,
                    "--result",
                    str(args.result.with_name(f"result-{mode}.json")),
                    "--interrupt-file",
                    str(args.interrupt_file),
                ],
                check=True,
            )
        return
    os.chdir(args.lab / "fixture")
    from cli import HermesCLI

    cli = HermesCLI(
        model="amalgam-pilot",
        provider="custom",
        base_url=args.url,
        api_key="local-pilot",
        toolsets=["terminal", "file"] if args.mode == "operate" else [],
        reasoning="none",
        max_turns=6,
        run_budget=300,
        ignore_rules=True,
    )
    cli._single_query_mode = True
    if not cli._init_agent(
        request_overrides={
            "temperature": 0,
            "top_p": 1,
            "seed": 42,
            "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
        }
    ):
        raise RuntimeError("Hermes CLI agent initialization failed")
    cli.agent.max_tokens = 128

    def watch_interrupt():
        while not args.interrupt_file.exists():
            time.sleep(0.1)
        cli.agent.interrupt(hard_cancel=True, tool_reason="pilot cancellation")

    threading.Thread(target=watch_interrupt, daemon=True).start()
    if args.mode == "aux-cancel":
        from agent.conversation_compression_manual import (
            compress_now,
            parse_compress_args,
        )

        history = []
        for i in range(12):
            history.extend([
                {
                    "role": "user",
                    "content": f"Record {i}: update the fixture retry_limit from 2 to 3.",
                },
                {
                    "role": "assistant",
                    "content": f"Record {i} acknowledged. Verify settings.json with check.py before claiming completion.",
                },
            ])
        result = compress_now(cli.agent, history, parse_compress_args(""))
        responses = [{"compression_status": result.status}]
    else:
        prompts = {
            "smoke": ["Reply with exactly AMALGAM_OK. Do not use tools."],
            "main-cancel": [
                "Write a numbered list of 100 distinct prime numbers. No introduction."
            ],
            "operate": [
                "Read settings.json in the current directory and report retry_limit. Use the file tool.",
                "Change retry_limit to 3 in settings.json using the file tool. Preserve valid JSON. Then run "
                + json.dumps(sys.executable)
                + " check.py and report its actual result.",
                "Run "
                + json.dumps(sys.executable)
                + " missing_check.py. When it fails, recover by running "
                + json.dumps(sys.executable)
                + " check.py. Report the failure and recovery truthfully.",
            ],
        }[args.mode]
        responses = []
        for prompt in prompts:
            if args.interrupt_file.exists():
                break
            responses.append(cli.chat(prompt))
    args.result.write_text(
        json.dumps(
            {
                "session_id": cli.session_id,
                "responses": responses,
                "fixture": json.loads(
                    Path("settings.json").read_text(encoding="utf-8")
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
