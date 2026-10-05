"""Run every ranking candidate on the same postings.

  uv run python -m tools.ranking.run_eval <postings.json> <profile.md> [labels.json] [--only A,C]

Without labels it reports only time, errors and each candidate's top 5 (no quality numbers).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.ranking.eval import evaluate
from tools.ranking.registry import CANDIDATES
from tools.sources import Posting

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("postings", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("labels", type=Path, nargs="?")
    parser.add_argument("--only", default=",".join(CANDIDATES))
    args = parser.parse_args(argv)

    raw = json.loads(args.postings.read_text(encoding="utf-8"))
    postings = [Posting(**p) for p in raw.get("postings", raw)]
    profile = args.profile.read_text(encoding="utf-8")
    labels = json.loads(args.labels.read_text(encoding="utf-8")) if args.labels else {p.url: "?" for p in postings}
    rankers = [CANDIDATES[key.strip()]() for key in args.only.split(",")]

    titles = {p.url: f"{p.title} · {p.company}" for p in postings}
    for ranker, result in zip(rankers, evaluate(rankers, profile, postings, labels)):
        print(f"\n== {result.name}: {result.n} avisos, {result.seconds:.1f}s {('ERROR: ' + result.error[-300:]) if result.error else ''}")
        if ranker.meta:
            print("   meta:", ranker.meta)
        if args.labels and not result.error:
            print("   recall:", result.recall, "| lost@10:", len(result.lost.get(10, [])))
        for url in result.ranked[:5]:
            print("   -", titles[url])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
