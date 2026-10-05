"""Compare ranking candidates on the same postings against his own labels (si / no / tal vez).

A ranker is any object with `name`, `trainable` and `rank(profile, postings) -> postings in order`.
Trainable rankers also have `fit(profile, postings, labels)`. When any ranker is trainable, every
ranker is scored on the same held-out split so the numbers stay comparable.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from tools.sources import Posting

HIT = "si"


def recall_at_k(ranked_urls: list[str], labels: dict[str, str], k: int) -> float | None:
    targets = {u for u, label in labels.items() if label == HIT}
    if not targets:
        return None
    return len(targets & set(ranked_urls[:k])) / len(targets)


def lost_at_k(ranked_urls: list[str], labels: dict[str, str], k: int) -> list[str]:
    top = set(ranked_urls[:k])
    return sorted(u for u, label in labels.items() if label == HIT and u not in top)


def split_labels(
    labels: dict[str, str], test_fraction: float, seed: int
) -> tuple[dict, dict]:
    urls = sorted(labels)
    random.Random(seed).shuffle(urls)
    cut = max(1, round(len(urls) * test_fraction))
    test = {u: labels[u] for u in urls[:cut]}
    train = {u: labels[u] for u in urls[cut:]}
    return train, test


@dataclass
class Result:
    name: str
    ranked: list[str] = field(default_factory=list)
    recall: dict[int, float | None] = field(default_factory=dict)
    lost: dict[int, list[str]] = field(default_factory=dict)
    n: int = 0  # postings this ranker was given
    seconds: float = 0.0
    error: str | None = None


def evaluate(
    rankers,
    profile: str,
    postings: list[Posting],
    labels: dict[str, str],
    ks=(10, 15),
    test_fraction: float = 0.5,
    seed: int = 0,
) -> list[Result]:
    by_url = {p.url: p for p in postings}
    has_labels = any(label in (HIT, "no") for label in labels.values())
    if has_labels and any(r.trainable for r in rankers):
        # Hold out a split only when there is something to learn from; otherwise everyone sees everything.
        train, scored = split_labels(labels, test_fraction, seed)
    else:
        train, scored = {}, labels
    candidates = [by_url[u] for u in scored if u in by_url]

    results = []
    for ranker in rankers:
        result = Result(name=ranker.name, n=len(candidates))
        start = time.perf_counter()
        try:
            if ranker.trainable:
                ranker.fit(profile, [by_url[u] for u in train if u in by_url], train)
            result.ranked = [p.url for p in ranker.rank(profile, candidates)]
        except Exception as exc:  # one broken candidate must not hide the others
            result.error = str(exc)
        result.seconds = time.perf_counter() - start
        for k in ks:
            result.recall[k] = recall_at_k(result.ranked, scored, k)
            result.lost[k] = lost_at_k(result.ranked, scored, k)
        results.append(result)
    return results
