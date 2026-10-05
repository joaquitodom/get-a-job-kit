from datetime import date

from tools.daily import Dealbreakers, apply_dealbreakers, drop_seen, order_batch, remember
from tools.sources import Posting


def P(n, title=None, company="Banco", work_mode=None, url=None):
    return Posting(source="t", company=company, title=title or f"Analista {n}", url=url or f"u{n}", work_mode=work_mode)


def test_postings_already_seen_by_url_or_by_company_and_title_are_dropped():
    seen = {"urls": ["u1"], "keys": ["banco|analista 2"]}
    fresh = drop_seen([P(1), P(2, url="otro-link"), P(3)], seen)
    assert [p.url for p in fresh] == ["u3"]


def test_title_dealbreaker_discards_with_its_reason():
    kept, discarded = apply_dealbreakers([P(1, title="Ejecutivo de Ventas"), P(2)], Dealbreakers(title_terms=["ventas"]))
    assert [p.url for p in kept] == ["u2"]
    assert discarded == [("u1", "El título contiene 'ventas', que marcaste como descarte.")]


def test_work_mode_dealbreaker_only_applies_when_the_posting_states_it():
    rules = Dealbreakers(work_modes=["remote"])
    kept, discarded = apply_dealbreakers([P(1, work_mode="remote"), P(2, work_mode=None), P(3, work_mode="hybrid")], rules)
    assert [p.url for p in kept] == ["u2", "u3"]
    assert [u for u, _ in discarded] == ["u1"]


def test_title_match_ignores_case_and_accents():
    kept, _ = apply_dealbreakers([P(1, title="Vendedor de CRÉDITOS")], Dealbreakers(title_terms=["creditos"]))
    assert kept == []


def test_collection_mode_keeps_everyone_in_a_reproducible_random_order():
    postings = [P(n) for n in range(10)]
    first = order_batch(postings, mode="recoleccion", day=date(2026, 9, 25))
    again = order_batch(postings, mode="recoleccion", day=date(2026, 9, 25))
    assert first == again and sorted(p.url for p in first) == sorted(p.url for p in postings)
    assert [p.url for p in first] != [p.url for p in postings]


def test_normal_mode_orders_by_the_rankers_output():
    postings = [P(n) for n in range(3)]
    ranker = lambda ps: list(reversed(ps))  # noqa: E731
    assert [p.url for p in order_batch(postings, mode="normal", day=date(2026, 9, 25), rank=ranker)] == ["u2", "u1", "u0"]


def test_remember_adds_urls_and_keys_without_duplicates():
    seen = remember({"urls": ["u1"], "keys": ["banco|analista 1"]}, [P(1), P(2)])
    assert seen == {"urls": ["u1", "u2"], "keys": ["banco|analista 1", "banco|analista 2"]}


import json  # noqa: E402

from tools.daily import confirmar  # noqa: E402


def _write_batch(day, avisos, confirmado=False):
    from pathlib import Path

    Path("data").mkdir(exist_ok=True)
    Path(f"data/diario-{day}.json").write_text(json.dumps(
        {"fecha": day, "modo": "recoleccion", "avisos": [{"source": "t", "company": "B", "title": a, "url": a} for a in avisos],
         "descartados": [], "errores": [], "confirmado": confirmado}), encoding="utf-8")


def test_confirm_uses_the_latest_unconfirmed_batch_even_after_midnight(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_batch("2026-09-24", ["ayer"])
    confirmar()
    seen = json.loads((tmp_path / "postulaciones/vistos.json").read_text(encoding="utf-8"))
    assert seen["urls"] == ["ayer"]
    assert json.loads((tmp_path / "data/diario-2026-09-24.json").read_text(encoding="utf-8"))["confirmado"] is True


def test_confirm_skips_batches_already_confirmed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_batch("2026-09-23", ["viejo"])
    _write_batch("2026-09-24", ["ya"], confirmado=True)
    confirmar()
    assert json.loads((tmp_path / "postulaciones/vistos.json").read_text(encoding="utf-8"))["urls"] == ["viejo"]


def test_normal_mode_without_a_ranker_falls_back_to_collection_order():
    postings = [P(n) for n in range(5)]
    day = date(2026, 9, 25)
    assert order_batch(postings, mode="normal", day=day) == order_batch(postings, mode="recoleccion", day=day)


def test_work_mode_dealbreakers_accept_spanish_names():
    kept, _ = apply_dealbreakers([P(1, work_mode="remote"), P(2, work_mode="onsite")], Dealbreakers.from_config({"work_modes": ["remoto"]}))
    assert [p.url for p in kept] == ["u2"]


def test_unknown_dealbreaker_keys_are_ignored():
    assert Dealbreakers.from_config({"title_terms": ["ventas"], "otra_cosa": 1}).title_terms == ["ventas"]


from tools.daily import archive_external, load_external  # noqa: E402


def _write_external(name, rows):
    from pathlib import Path

    Path("data/externos").mkdir(parents=True, exist_ok=True)
    Path(f"data/externos/{name}").write_text(json.dumps(rows), encoding="utf-8")


def test_external_postings_are_loaded_from_every_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_external("2026-09-26-bumeran.json", [{"source": "bumeran", "company": "Banco", "title": "Analista", "url": "b1"}])
    _write_external("2026-09-26-alerta-zonajobs.json", [{"source": "alerta-zonajobs", "company": "Fintech", "title": "Analista", "url": "z1"}])
    postings, errors = load_external()
    assert sorted(p.url for p in postings) == ["b1", "z1"] and errors == []


def test_external_entries_without_title_or_link_are_skipped_and_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_external("x.json", [{"source": "bumeran", "company": "B", "title": "", "url": "b1"}, {"source": "bumeran", "company": "B", "title": "Ok", "url": "b2"}])
    postings, errors = load_external()
    assert [p.url for p in postings] == ["b2"] and len(errors) == 1


def test_confirmed_external_files_are_archived_so_they_are_not_loaded_twice(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_external("x.json", [{"source": "bumeran", "company": "B", "title": "Ok", "url": "b2"}])
    archive_external(["data/externos/x.json"])
    assert load_external() == ([], [])
    assert (tmp_path / "data/externos/procesados/x.json").exists()


from tools.daily import score_batch  # noqa: E402


class _Ranker:
    def __init__(self, fail=False):
        self.fail, self.scores = fail, {}

    def rank(self, profile, postings):
        if self.fail:
            raise RuntimeError("modelo caido")
        self.scores = {p.url: {"puntaje": 10 * i, "motivo": f"r{i}"} for i, p in enumerate(postings)}
        return list(reversed(postings))


def test_score_batch_orders_by_the_ranker_and_returns_its_scores():
    postings = [P(n) for n in range(3)]
    ordered, scores, error = score_batch(postings, _Ranker(), "perfil", day=date(2026, 9, 26))
    assert [p.url for p in ordered] == ["u2", "u1", "u0"]
    assert scores["u1"] == {"puntaje": 10, "motivo": "r1"} and error is None


def test_a_failing_ranker_falls_back_to_collection_order_and_reports_it():
    postings = [P(n) for n in range(5)]
    day = date(2026, 9, 26)
    ordered, scores, error = score_batch(postings, _Ranker(fail=True), "perfil", day=day)
    assert ordered == order_batch(postings, mode="recoleccion", day=day)
    assert scores == {} and "modelo caido" in error


def test_normal_mode_writes_score_and_reason_into_the_batch(tmp_path, monkeypatch):
    import tools.daily as daily
    import tools.ranking.registry as registry
    import tools.search as search
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    Path("profile").mkdir()
    Path("profile/busqueda.toml").write_text('terms = ["x"]\nmodo = "normal"\nranking = "A"\n', encoding="utf-8")
    Path("profile/PROFILE.md").write_text("perfil de prueba", encoding="utf-8")
    monkeypatch.setattr(search, "run_search", lambda cfg: search.SearchResult(postings=[P(1), P(2)], errors=[]))
    monkeypatch.setattr(registry, "get", lambda name: _Ranker())
    batch = json.loads(daily.preparar(date(2026, 9, 26)).read_text(encoding="utf-8"))
    assert [a["url"] for a in batch["avisos"]] == ["u2", "u1"]
    assert batch["avisos"][0]["puntaje"] == 10 and batch["avisos"][0]["motivo"] == "r1"
    assert batch["ranking"] == "A"


def test_batch_includes_monthly_usd_salary_when_it_is_known(tmp_path, monkeypatch):
    import tools.daily as daily
    import tools.search as search
    from pathlib import Path

    from tools.sources import Posting

    monkeypatch.chdir(tmp_path)
    Path("profile").mkdir()
    Path("profile/busqueda.toml").write_text('terms = ["x"]\n', encoding="utf-8")
    paid = Posting(source="t", company="B", title="Con sueldo", url="s1", salary_min=24000, salary_max=36000, salary_currency="USD", salary_period="year")
    monkeypatch.setattr(search, "run_search", lambda cfg: search.SearchResult(postings=[paid, P(9)], errors=[]))
    batch = json.loads(daily.preparar(date(2026, 9, 26)).read_text(encoding="utf-8"))
    by_url = {a["url"]: a for a in batch["avisos"]}
    assert by_url["s1"]["sueldo_usd_mes"] == [2000.0, 3000.0]
    assert "sueldo_usd_mes" not in by_url["u9"]


def test_confirm_archives_the_batch_with_posting_texts_in_a_synced_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_batch("2026-09-26", ["a1", "a2"])
    confirmar()
    archived = json.loads((tmp_path / "postulaciones/lotes/diario-2026-09-26.json").read_text(encoding="utf-8"))
    assert [p["url"] for p in archived["avisos"]] == ["a1", "a2"]


from tools.daily import pick_control  # noqa: E402


def test_control_sample_is_random_reproducible_and_of_the_requested_size():
    postings = [P(n) for n in range(20)]
    day = date(2026, 9, 28)
    first = pick_control(postings, 5, day)
    assert first == pick_control(postings, 5, day) and len(first) == 5
    assert first != {p.url for p in postings[:5]}


def test_control_sample_never_exceeds_the_batch():
    assert len(pick_control([P(1), P(2)], 5, date(2026, 9, 28))) == 2


def test_capped_batch_marks_the_control_sample(tmp_path, monkeypatch):
    import tools.daily as daily
    import tools.search as search
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    Path("profile").mkdir()
    Path("profile/busqueda.toml").write_text('terms = ["x"]\nmax_para_decidir = 5\nmuestra_control = 3\n', encoding="utf-8")
    monkeypatch.setattr(search, "run_search", lambda cfg: search.SearchResult(postings=[P(n) for n in range(10)], errors=[]))
    batch = json.loads(daily.preparar(date(2026, 9, 28)).read_text(encoding="utf-8"))
    assert sum(1 for a in batch["avisos"] if a.get("control")) == 3
    assert batch["max_para_decidir"] == 5


def test_uncapped_batch_has_no_control_marks(tmp_path, monkeypatch):
    import tools.daily as daily
    import tools.search as search
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    Path("profile").mkdir()
    Path("profile/busqueda.toml").write_text('terms = ["x"]\n', encoding="utf-8")
    monkeypatch.setattr(search, "run_search", lambda cfg: search.SearchResult(postings=[P(n) for n in range(4)], errors=[]))
    batch = json.loads(daily.preparar(date(2026, 9, 28)).read_text(encoding="utf-8"))
    assert not any(a.get("control") for a in batch["avisos"]) and batch["max_para_decidir"] is None


def test_control_sample_can_stay_out_of_notion(tmp_path, monkeypatch):
    import tools.daily as daily
    import tools.search as search
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    Path("profile").mkdir()
    Path("profile/busqueda.toml").write_text(
        'terms = ["x"]\nmax_para_decidir = 5\nmuestra_control = 3\nmuestra_control_destino = "archivo"\n', encoding="utf-8"
    )
    monkeypatch.setattr(search, "run_search", lambda cfg: search.SearchResult(postings=[P(n) for n in range(10)], errors=[]))
    batch = json.loads(daily.preparar(date(2026, 9, 28)).read_text(encoding="utf-8"))
    assert not any(a.get("control") for a in batch["avisos"])
    assert len(batch["control_archivo"]) == 3


def test_confirm_ignores_extra_fields_in_the_batch(tmp_path, monkeypatch):
    """29-sep-2026: confirmar crashed on `control: true` (Posting got an unexpected keyword)."""
    import tools.daily as daily
    from pathlib import Path

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(daily, "DATA", tmp_path / "data")
    monkeypatch.setattr(daily, "SEEN", tmp_path / "postulaciones/vistos.json")
    (tmp_path / "data").mkdir()
    row = {"source": "linkedin", "company": "X", "title": "T", "url": "u1", "control": True, "puntaje": 80, "sueldo_usd_mes": [1, 2]}
    (tmp_path / "data/diario-2026-09-29.json").write_text(
        json.dumps({"fecha": "2026-09-29", "avisos": [row], "descartados": [row | {"url": "u2", "title": "T2", "motivo": "m"}], "confirmado": False}),
        encoding="utf-8",
    )
    daily.confirmar()
    assert set(json.loads(Path("postulaciones/vistos.json").read_text(encoding="utf-8"))["urls"]) == {"u1", "u2"}
