import json

import pytest

from tools import gpt_filtro
from tools.gpt_filtro import build_prompt, compact, parse, screen

AVISOS = [
    {"url": "u1", "title": "FP&A Sr", "company": "Banco", "description": "x" * 5000, "location": "None"},
    {"url": "u2", "title": "Dev", "company": "Soft", "description": "python"},
]


def answer(rows):
    return "Acá va:\n" + json.dumps(rows)


def test_compact_trims_description_and_drops_unknowns():
    c = compact(AVISOS[0])
    assert len(c["description"]) == gpt_filtro.DESC_CHARS and "location" not in c


def test_prompt_carries_rules_cv_and_postings():
    p = build_prompt("REGLAS", "MI CV", AVISOS)
    assert "REGLAS" in p and "MI CV" in p and '"u2"' in p


def test_valid_answer_is_parsed_in_order_and_dashes_are_removed():
    rows = [
        {"url": "u2", "decision": "descartado", "puntaje": 5, "motivo": "Otra área — técnico", "proximo_paso": ""},
        {"url": "u1", "decision": "para_decidir", "puntaje": 72.4, "motivo": "Encaja", "proximo_paso": None},
    ]
    out = parse(answer(rows), ["u1", "u2"])
    assert [r["url"] for r in out] == ["u1", "u2"]
    assert out[0]["puntaje"] == 72 and out[1]["motivo"] == "Otra área, técnico"


@pytest.mark.parametrize(
    "rows",
    [
        [{"url": "u1", "decision": "para_decidir", "puntaje": 70, "motivo": "ok"}],
        [{"url": "u1", "decision": "quizas", "puntaje": 70, "motivo": "ok"}, {"url": "u2", "decision": "descartado", "puntaje": 1, "motivo": "x"}],
        [{"url": "u1", "decision": "para_decidir", "puntaje": 170, "motivo": "ok"}, {"url": "u2", "decision": "descartado", "puntaje": 1, "motivo": "x"}],
    ],
)
def test_incomplete_or_invalid_answers_are_rejected(rows):
    with pytest.raises(ValueError):
        parse(answer(rows), ["u1", "u2"])


def test_no_json_is_rejected():
    with pytest.raises(ValueError):
        parse("no sé", ["u1"])


def test_screen_calls_gpt_in_chunks():
    calls = []

    def runner(prompt):
        calls.append(prompt)
        urls = [u for u in ("u1", "u2") if f'"{u}"' in prompt]
        return answer([{"url": u, "decision": "para_decidir", "puntaje": 50, "motivo": "m"} for u in urls])

    out = screen(AVISOS, "R", "CV", runner=runner, chunk=1)
    assert len(calls) == 2 and [r["url"] for r in out] == ["u1", "u2"]


def test_disabled_by_default(tmp_path):
    cfg = tmp_path / "b.toml"
    cfg.write_text('terms = ["x"]\n', encoding="utf-8")
    assert gpt_filtro.enabled(cfg) is False
    cfg.write_text('terms = ["x"]\nfiltro_gpt = true\n', encoding="utf-8")
    assert gpt_filtro.enabled(cfg) is True
