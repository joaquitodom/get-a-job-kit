"""Deterministic half of the daily run. Claude does the rest (Notion, email, CVs) with the `corrida-diaria` skill.

  uv run python -m tools.daily preparar    # search, drop seen, apply explicit deal-breakers, write data/diario-<date>.json
  uv run python -m tools.daily confirmar   # after the batch is in Notion: remember those postings as seen

Postings are marked as seen only on `confirmar`, so a failed Notion load loses nothing: they come back tomorrow.
"""

from __future__ import annotations

import json
import random
import sys
import tomllib
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from pathlib import Path

from tools.sources import Posting, _normalize, dedup, posting_key

CONFIG = Path("profile/busqueda.toml")
SEEN = Path("postulaciones/vistos.json")
DATA = Path("data")
EXTERNAL = DATA / "externos"  # postings gathered by skills (browser, alert emails), one JSON list per file


def load_external() -> tuple[list[Posting], list[str]]:
    """Postings other skills left in data/externos/. Returns (postings, problems)."""
    postings, problems = [], []
    for path in sorted(EXTERNAL.glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            if not row.get("title") or not row.get("url"):
                problems.append(f"{path.name}: aviso sin título o sin link, lo salteé.")
                continue
            known = {k: v for k, v in row.items() if k in Posting.__dataclass_fields__}
            postings.append(Posting(**{"company": "", **known}))
    return postings, problems


def archive_external(paths: list[str]) -> None:
    done = EXTERNAL / "procesados"
    done.mkdir(parents=True, exist_ok=True)
    for name in paths:
        path = Path(name)
        if path.exists():
            path.replace(done / path.name)


@dataclass
class Dealbreakers:
    """Only what the user confirmed as absolute. Each rule fires only when the posting states the fact."""

    title_terms: list[str] = field(default_factory=list)
    work_modes: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, raw: dict) -> Dealbreakers:
        modes = [WORK_MODE_NAMES.get(_normalize(m), _normalize(m)) for m in raw.get("work_modes", [])]
        return cls(title_terms=list(raw.get("title_terms", [])), work_modes=modes)


WORK_MODE_NAMES = {"presencial": "onsite", "hibrido": "hybrid", "remoto": "remote"}


def drop_seen(postings: list[Posting], seen: dict) -> list[Posting]:
    urls, keys = set(seen.get("urls", [])), set(seen.get("keys", []))
    return [p for p in postings if p.url not in urls and posting_key(p) not in keys]


def apply_dealbreakers(
    postings: list[Posting], rules: Dealbreakers
) -> tuple[list[Posting], list[tuple[str, str]]]:
    kept, discarded = [], []
    terms = [(t, _normalize(t)) for t in rules.title_terms]
    for p in postings:
        title = _normalize(p.title)
        hit = next((raw for raw, norm in terms if norm and norm in title), None)
        if hit:
            discarded.append(
                (p.url, f"El título contiene '{hit}', que marcaste como descarte.")
            )
        elif p.work_mode is not None and p.work_mode in rules.work_modes:
            discarded.append(
                (p.url, f"La modalidad es '{p.work_mode}', que marcaste como descarte.")
            )
        else:
            kept.append(p)
    return kept, discarded


def order_batch(
    postings: list[Posting], mode: str, day: date, rank=None
) -> list[Posting]:
    if mode == "recoleccion" or rank is None:
        # While their labels are being collected (or until a ranker is chosen), no ranker decides the order.
        shuffled = list(postings)
        random.Random(day.isoformat()).shuffle(shuffled)
        return shuffled
    return rank(postings)


def score_batch(postings: list[Posting], ranker, profile: str, day: date) -> tuple[list[Posting], dict, str | None]:
    """Order by the configured ranker. If it fails, fall back to collection order: the day's batch is never lost."""
    try:
        ordered = ranker.rank(profile, postings)
        return ordered, dict(getattr(ranker, "scores", {}) or {}), None
    except Exception as exc:
        return order_batch(postings, mode="recoleccion", day=day), {}, f"El ranking falló ({exc}); el lote va en orden aleatorio."


def pick_control(postings: list[Posting], k: int, day: date) -> set[str]:
    """Random sample that reaches them no matter what the screening decides: unbiased labels for the ranking eval."""
    urls = sorted(p.url for p in postings)
    return set(random.Random(f"control-{day.isoformat()}").sample(urls, min(k, len(urls))))


def remember(seen: dict, postings: list[Posting]) -> dict:
    urls, keys = list(seen.get("urls", [])), list(seen.get("keys", []))
    for p in postings:
        if p.url not in urls:
            urls.append(p.url)
        if posting_key(p) not in keys:
            keys.append(posting_key(p))
    return {"urls": urls, "keys": keys}


def _salary_fields(p: Posting, rates) -> dict:
    from tools.salary import monthly_usd

    usd = monthly_usd(p, rates)
    return {"sueldo_usd_mes": list(usd)} if usd else {}


def _profile_text() -> str:
    """What the ranker compares postings against: their profile plus their stated preferences."""
    parts = [Path("profile/PROFILE.md"), Path("profile/preferences.md")]
    return "\n\n".join(p.read_text(encoding="utf-8") for p in parts if p.exists())


def _load_seen() -> dict:
    return (
        json.loads(SEEN.read_text(encoding="utf-8"))
        if SEEN.exists()
        else {"urls": [], "keys": []}
    )


def _batch_path(day: date) -> Path:
    return DATA / f"diario-{day.isoformat()}.json"


def _latest_unconfirmed() -> Path | None:
    for path in sorted(DATA.glob("diario-*.json"), reverse=True):
        if not json.loads(path.read_text(encoding="utf-8")).get("confirmado", False):
            return path
    return None


def preparar(day: date) -> Path:
    from tools.search import SearchConfig, run_search

    raw = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    rules = Dealbreakers.from_config(raw.get("descartes", {}))
    mode = raw.get("modo", "recoleccion")
    result = run_search(SearchConfig.load(CONFIG))
    external, problems = load_external()
    external_files = [str(f) for f in sorted(EXTERNAL.glob('*.json'))]
    fresh = drop_seen(dedup(result.postings + external), _load_seen())
    kept, discarded = apply_dealbreakers(fresh, rules)
    ranking = raw.get("ranking")
    scores, ranking_error = {}, None
    if mode == "normal" and ranking:
        from tools.ranking import registry

        batch, scores, ranking_error = score_batch(kept, registry.get(ranking), _profile_text(), day=day)
    else:
        batch = order_batch(kept, mode="recoleccion", day=day)
    cap = raw.get("max_para_decidir")
    control = pick_control(batch, int(raw.get("muestra_control", 10)), day) if cap and len(batch) > cap else set()
    # "archivo": the sample is only recorded in the batch file (the user asked not to see it in Notion, 30-sep-2026).
    control_in_notion = raw.get("muestra_control_destino", "notion") != "archivo"
    DATA.mkdir(exist_ok=True)
    from tools.salary import ExchangeRates

    rates = ExchangeRates(casa=raw.get("dolar", "oficial"))
    out = _batch_path(day)
    by_url = {p.url: p for p in fresh}
    out.write_text(
        json.dumps(
            {
                "fecha": day.isoformat(),
                "modo": mode,
                "ranking": ranking if mode == "normal" else None,
                "max_para_decidir": cap,
                "avisos": [asdict(p) | scores.get(p.url, {}) | _salary_fields(p, rates) | ({"control": True} if control_in_notion and p.url in control else {}) for p in batch],
                "control_archivo": [] if control_in_notion else sorted(control),
                "descartados": [
                    asdict(by_url[u]) | {"motivo": reason} for u, reason in discarded
                ],
                "errores": [asdict(e) for e in result.errors] + [{"source": "externos", "message": m} for m in problems] + ([{"source": "ranking", "message": ranking_error}] if ranking_error else []),
                "externos": external_files,
                "confirmado": False,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(
        f"{len(batch)} avisos nuevos, {len(discarded)} descartados por tus reglas. Lote: {out}"
    )
    for e in result.errors:
        print(f"No pude leer {e.source}: {e.message}", file=sys.stderr)
    return out


def _as_posting(row: dict) -> Posting:
    """Batch rows carry extras (motivo, control, puntaje, sueldo_usd_mes); only the Posting fields matter here."""
    names = {f.name for f in fields(Posting)}
    return Posting(**{k: v for k, v in row.items() if k in names})


def confirmar() -> None:
    """Mark the most recent unconfirmed batch as seen, whatever day it is now (catch-up runs can cross midnight)."""
    path = _latest_unconfirmed()
    if path is None:
        print("No hay lotes pendientes de confirmar.")
        return
    batch = json.loads(path.read_text(encoding="utf-8"))
    loaded = [_as_posting(p) for p in batch["avisos"] + batch["descartados"]]
    SEEN.parent.mkdir(exist_ok=True)
    SEEN.write_text(json.dumps(remember(_load_seen(), loaded), ensure_ascii=False, indent=1), encoding="utf-8")
    archive_external(batch.get("externos", []))
    # A copy with the posting texts where the sync hook saves it: the ranking eval joins it with their Notion labels.
    archive = Path("postulaciones/lotes") / path.name
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(json.dumps({"fecha": batch.get("fecha"), "avisos": batch["avisos"], "descartados": batch["descartados"], "control_archivo": batch.get("control_archivo", [])}, ensure_ascii=False, indent=1), encoding="utf-8")
    batch["confirmado"] = True
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Marcados como vistos: {len(loaded)} avisos ({path.name}).")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    day = date.today()
    if args[:1] == ["preparar"]:
        preparar(day)
    elif args[:1] == ["confirmar"]:
        confirmar()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
