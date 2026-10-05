import sys

import pytest

from tools.ranking.subprocess_ranker import SubprocessRanker
from tools.sources import Posting

POSTINGS = [Posting(source="t", company="C", title=f"T{n}", url=f"u{n}") for n in range(3)]

REVERSE = "import json,sys; d=json.load(sys.stdin); print(json.dumps({'ranked': [p['url'] for p in d['postings']][::-1]}))"
ECHO_TRAIN = (
    "import json,sys; d=json.load(sys.stdin); "
    "print(json.dumps({'ranked': [p['url'] for p in d['postings']], 'meta': {'train': sorted(d['train_labels'])}}))"
)


def test_postings_come_back_in_the_order_the_process_prints():
    ranker = SubprocessRanker("rev", [sys.executable, "-c", REVERSE])
    assert [p.url for p in ranker.rank("perfil", POSTINGS)] == ["u2", "u1", "u0"]


def test_a_failing_process_raises_with_its_error_text():
    ranker = SubprocessRanker("bad", [sys.executable, "-c", "import sys; sys.exit('modelo no encontrado')"])
    with pytest.raises(RuntimeError, match="modelo no encontrado"):
        ranker.rank("perfil", POSTINGS)


def test_trainable_ranker_sends_its_training_labels_along_with_the_postings():
    ranker = SubprocessRanker("learn", [sys.executable, "-c", ECHO_TRAIN], trainable=True)
    ranker.fit("perfil", POSTINGS[:1], {"u0": "si"})
    ranker.rank("perfil", POSTINGS[1:])
    assert ranker.meta == {"train": ["u0"]}


WITH_SCORES = (
    "import json,sys; d=json.load(sys.stdin); urls=[p['url'] for p in d['postings']]; "
    "print(json.dumps({'ranked': urls, 'scores': {u: {'puntaje': 90 - i, 'motivo': 'm'+str(i)} for i, u in enumerate(urls)}}))"
)


def test_scores_reported_by_the_process_are_kept():
    ranker = SubprocessRanker("s", [sys.executable, "-c", WITH_SCORES])
    ranker.rank("perfil", POSTINGS)
    assert ranker.scores["u0"] == {"puntaje": 90, "motivo": "m0"}


def test_a_process_without_scores_leaves_them_empty():
    ranker = SubprocessRanker("rev", [sys.executable, "-c", REVERSE])
    ranker.rank("perfil", POSTINGS)
    assert ranker.scores == {}
