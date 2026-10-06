"""Rank the sampling screen per thinking mode and record the winners (T-212 S2).

Single seeded screening runs: the ranking selects a configuration for the full runs; it is
not evidence of statistical superiority (S3). Contamination verdicts are recomputed from
each session's recorded tool calls with the current scan, so a scan repair applies to the
evidence already gathered; the verdict recorded live is reported beside it.

    python screen.py --lab <lab> --attempt <screen attempt dir name> [--write]
"""

import argparse
import json
import math
import os
from pathlib import Path

import verify_long

HERE = Path(__file__).resolve().parent


def rank(candidates: list[dict]) -> tuple[list[dict], bool]:
    """Selectable candidates in S2 order; True when every one scored 0 (inconclusive).

    Each candidate has ``verified`` items, ``machine_s`` and ``decoded`` tokens. The order is
    verified items descending, machine time per verified item ascending, decoded tokens
    ascending; with no verified item anywhere, machine time alone decides.
    """
    eligible = [c for c in candidates if c["selectable"]]
    inconclusive = all(c["verified"] == 0 for c in eligible)

    def key(c):
        if inconclusive:
            return (c["machine_s"], c["decoded"])
        per_item = c["machine_s"] / c["verified"] if c["verified"] else math.inf
        return (-c["verified"], per_item, c["decoded"])

    return sorted(eligible, key=key), inconclusive


def pick(sessions: list[dict]) -> dict:
    """One candidate per arm under L4: the first clean session counts; a second
    contaminated session makes the arm a failure (0 verified items, still ranked)."""
    for s in sessions:
        if not s["contamination"]:
            return s
        if s is not sessions[0]:
            return {**s, "verified": 0, "failed_by_contamination": True}
    return {**sessions[0], "verified": 0, "failed_by_contamination": True}


def screen_results(attempt: Path) -> list[dict]:
    """Every long screen session, from the receipts and archived session state."""
    arms = json.loads((HERE / "arms.json").read_text(encoding="utf-8"))
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    events = [
        json.loads(line) for line in (attempt / "events.jsonl").open(encoding="utf-8")
    ]
    starts, ends, decoded = {}, {}, {}
    for e in events:
        session = e.get("session")
        if e["kind"] == "request":
            starts.setdefault(session, e["at"])
        elif e["kind"] in ("response_end", "response_cancelled"):
            ends[session] = e["at"]
            decoded[session] = decoded.get(session, 0) + (
                (e.get("timings") or {}).get("predicted_n") or 0
            )
    live = attempt / "live"
    results = []
    for e in events:
        if e["kind"] != "session_end" or not e["workload"].startswith("long"):
            continue
        s = e["session"]
        archived = attempt / f"session-{s:02d}"
        result = json.loads((archived / "result.json").read_text(encoding="utf-8"))
        # Sessions ran at the live paths; a private TEMP exists only after that repair.
        private = archived / "home" / "tmp"
        temp = live / "home" / "tmp" if private.is_dir() else Path(os.environ["TEMP"])
        verification = e.get("verification") or {}
        score = verification.get("score") or {}
        arm = arms["session_arms"][e["arm"]]
        results.append({
            "session": s,
            "arm": e["arm"],
            "thinking": arm["thinking"],
            "selectable": arm["selectable"],
            "rerun_of": e.get("rerun_of"),
            "stop": e.get("stop"),
            "requests": e.get("requests"),
            "verified": score.get("passed", 0),
            "items": {k: v.get("pass") for k, v in (score.get("items") or {}).items()},
            "machine_s": ends.get(s, starts.get(s, 0)) - starts.get(s, 0),
            "decoded": decoded.get(s, 0),
            "contamination": verify_long.contamination(
                result.get("conversation") or [],
                live / "fixture",
                [*manifest["allowlist"], str(live / "home")],
                temp,
            ),
            "contamination_recorded_live": verification.get("contamination"),
        })
    return results


def report(results: list[dict]) -> tuple[dict, dict]:
    """The winners per thinking mode, and the published report: each mode's ranking
    under L4's pick and every session with its re-scanned and live verdicts."""
    by_arm = {}
    for r in results:
        by_arm.setdefault(r["arm"], []).append(r)
    chosen = [pick(sessions) for sessions in by_arm.values()]
    winners, published = {}, {"label": "single seeded screening runs", "modes": {}}
    for mode, thinking in (("off", False), ("on", True)):
        ordered, inconclusive = rank([c for c in chosen if c["thinking"] is thinking])
        published["modes"][mode] = {
            "ranking": [
                {
                    k: c[k]
                    for k in ("arm", "session", "verified", "machine_s", "decoded")
                }
                for c in ordered
            ],
            "inconclusive": inconclusive,
        }
        if ordered:
            winners[mode] = ordered[0]["arm"]
    published["sessions"] = results
    return winners, published


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument(
        "--write", action="store_true", help="record winners in arms.json"
    )
    args = parser.parse_args()
    winners, published = report(screen_results(args.lab / "attempts" / args.attempt))
    print(json.dumps(published, indent=1))
    if args.write:
        path = HERE / "arms.json"
        text = path.read_text(encoding="utf-8")
        old = '"screen_winners": {}'
        if text.count(old) != 1:
            raise SystemExit("arms.json already records screen winners")
        new = '"screen_winners": ' + json.dumps(winners)
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        print(json.dumps({"screen_winners": winners}))


if __name__ == "__main__":
    main()
