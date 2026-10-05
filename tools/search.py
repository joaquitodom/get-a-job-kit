"""Run every configured job source, normalize and deduplicate the results.

Usage: uv run python -m tools.search [profile/busqueda.toml]
"""

from __future__ import annotations

import json
import sys
import tomllib
import urllib.request
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from pathlib import Path

from tools.sources import (
    Posting,
    dedup,
    parse_ashby,
    parse_greenhouse,
    parse_jobspy,
    parse_lever,
)

ATS = {
    "greenhouse": (
        "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
        parse_greenhouse,
    ),
    "lever": ("https://api.lever.co/v0/postings/{board}?mode=json", parse_lever),
    "ashby": (
        "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true",
        parse_ashby,
    ),
}


@dataclass
class SearchConfig:
    terms: list[str]
    location: str | None = None
    country: str | None = None
    jobspy_sites: list[str] = field(default_factory=list)
    greenhouse: list[str] = field(default_factory=list)
    lever: list[str] = field(default_factory=list)
    ashby: list[str] = field(default_factory=list)
    results_per_term: int = 25
    hours_old: int = 72
    workday: list[str] = field(default_factory=list)  # careers page URLs, e.g. https://mastercard.wd1.myworkdayjobs.com/CorporateCareers
    workday_buscar: str | None = None  # text searched on each Workday site; defaults to the city in `location`

    @classmethod
    def load(cls, path: Path) -> SearchConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        companies = data.pop("companies", {})
        known = {f.name for f in fields(cls)} - set(ATS) - {"workday"}
        # The same file also holds the daily-run sections (modo, descartes); they are not search settings.
        return cls(
            **{k: v for k, v in data.items() if k in known},
            **{kind: companies.get(kind, []) for kind in ATS},
            workday=companies.get("workday", []),
        )


@dataclass
class SourceError:
    source: str
    message: str


@dataclass
class SearchResult:
    postings: list[Posting]
    errors: list[SourceError]


def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "job-hunt-kit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _post_json(url: str, body: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"User-Agent": "job-hunt-kit", "Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _scrape(**kwargs) -> list[dict]:
    from jobspy import scrape_jobs

    return scrape_jobs(**kwargs).to_dict("records")


def run_search(
    config: SearchConfig, get_json=_get_json, scrape=_scrape, post_json=_post_json
) -> SearchResult:
    postings: list[Posting] = []
    errors: list[SourceError] = []

    for kind, (url_template, parse) in ATS.items():
        for board in getattr(config, kind):
            try:
                postings += parse(
                    get_json(url_template.format(board=board)), board=board
                )
            except Exception as exc:  # one broken source must not stop the daily run
                errors.append(SourceError(f"{kind}:{board}", str(exc)))

    if config.workday:
        from tools.workday import fetch_site

        search_text = config.workday_buscar or (config.location or "").split(",")[0].strip()
        max_days = max(1, -(-config.hours_old // 24))
        for site in config.workday:
            try:
                postings += fetch_site(site, search_text, max_days, post_json=post_json, get_json=get_json)
            except Exception as exc:
                errors.append(SourceError(f"workday:{site}", str(exc)))

    if config.jobspy_sites:
        for term in config.terms:
            try:
                postings += parse_jobspy(
                    scrape(
                        site_name=config.jobspy_sites,
                        search_term=term,
                        google_search_term=f"{term} jobs near {config.location}"
                        if config.location
                        else f"{term} jobs",
                        linkedin_fetch_description=True,
                        location=config.location,
                        country_indeed=config.country,
                        results_wanted=config.results_per_term,
                        hours_old=config.hours_old,
                    )
                )
            except Exception as exc:
                errors.append(SourceError(f"jobspy:{term}", str(exc)))

    return SearchResult(postings=dedup(postings), errors=errors)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    config_path = Path(args[0]) if args else Path("profile/busqueda.toml")
    result = run_search(SearchConfig.load(config_path))

    out = Path("data") / f"busqueda-{date.today().isoformat()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "postings": [asdict(p) for p in result.postings],
                "errors": [asdict(e) for e in result.errors],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"Encontré {len(result.postings)} avisos. Guardados en {out}")
    for error in result.errors:
        print(f"No pude leer {error.source}: {error.message}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
