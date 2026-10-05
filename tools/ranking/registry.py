"""Ranking candidates, shared by the evaluation (run_eval) and the daily run, so what is measured is what runs."""

from __future__ import annotations

from pathlib import Path

from tools.ranking.subprocess_ranker import SubprocessRanker

EVAL_DIR = Path(__file__).resolve().parents[2] / "evaluacion"


def _candidate(name: str, module: str, trainable: bool = False) -> SubprocessRanker:
    command = ["uv", "run", "--quiet", "--directory", str(EVAL_DIR), "python", "-m", f"candidates.{module}"]
    return SubprocessRanker(name, command, trainable=trainable)


CANDIDATES = {
    "A": lambda: _candidate("A embeddings+reranker", "embeddings"),
    "B": lambda: _candidate("B ollama", "ollama_rank"),
    "C": lambda: _candidate("C gliclass", "gliclass_rank"),
    "D": lambda: _candidate("D setfit", "setfit_rank", trainable=True),
    "G": lambda: _candidate("G laya", "laya_rank"),
    "E": lambda: _candidate("E claude", "claude_rank"),
}


def get(name: str) -> SubprocessRanker:
    if name not in CANDIDATES:
        raise ValueError(f"Ranking desconocido: {name}. Opciones: {', '.join(sorted(CANDIDATES))}.")
    return CANDIDATES[name]()
