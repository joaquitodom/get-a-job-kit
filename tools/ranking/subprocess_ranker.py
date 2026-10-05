"""Run a ranking candidate as a separate process, so heavy models live in their own environment.

Protocol: the process reads one JSON object on stdin
  {"profile": str, "postings": [posting dicts], "train_postings": [...], "train_labels": {url: label}}
and prints one JSON object on stdout: {"ranked": [url, ...], "scores": {url: {"puntaje": 0-100, "motivo": str}} (optional), "meta": {...} (optional)}.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict

from tools.sources import Posting


class SubprocessRanker:
    def __init__(
        self,
        name: str,
        command: list[str],
        trainable: bool = False,
        timeout: int = 1800,
    ):
        self.name = name
        self.command = command
        self.trainable = trainable
        self.timeout = timeout
        self.meta: dict = {}
        self.scores: dict = {}
        self._train_postings: list[Posting] = []
        self._train_labels: dict[str, str] = {}

    def fit(
        self, profile: str, postings: list[Posting], labels: dict[str, str]
    ) -> None:
        # Training happens inside the process together with ranking; keep the data until then.
        self._train_postings, self._train_labels = postings, labels

    def rank(self, profile: str, postings: list[Posting]) -> list[Posting]:
        payload = {
            "profile": profile,
            "postings": [asdict(p) for p in postings],
            "train_postings": [asdict(p) for p in self._train_postings],
            "train_labels": self._train_labels,
        }
        result = subprocess.run(
            self.command,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()[-2000:] or f"exit code {result.returncode}"
            )
        output = json.loads(result.stdout.strip().splitlines()[-1])
        self.meta = output.get("meta", {})
        self.scores = output.get("scores", {})
        by_url = {p.url: p for p in postings}
        return [by_url[u] for u in output["ranked"] if u in by_url]
