"""Read one posting from its link, or list LinkedIn postings, without the browser.

  uv run python -m tools.aviso leer <link>                     # title, company, location and full text
  uv run python -m tools.aviso linkedin "<término>" [--lugar "Latin America"] [--remoto] [--dias 7] [--guardar <archivo.json>]

`leer` understands LinkedIn (/jobs/view/<id> or ?currentJobId=<id>), Workday, Lever, Greenhouse and Ashby links.
Anything else: open it in the built-in browser. LinkedIn is read only through its public guest pages (the same a
logged-out visitor sees): never his account, never the browser, never "Easy Apply".
Saving cuts the browser and screenshot cost of reading each posting (usage budget, CLAUDE.md).
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from tools.sources import Posting, _html_to_text, parse_ashby, parse_greenhouse, parse_lever

UA = {"User-Agent": "Mozilla/5.0 (job-hunt-kit)"}
LINKEDIN_JOB = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{id}"
LINKEDIN_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&f_TPR=r{secs}{remote}&start={start}"


def _get(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip() if match else None


def linkedin_id(url: str) -> str | None:
    parts = urlsplit(url)
    if "linkedin.com" not in parts.netloc:
        return None
    query = parse_qs(parts.query).get("currentJobId")
    if query:
        return query[0]
    match = re.search(r"/jobs/view/(?:[^/]*?-)?(\d{6,})", parts.path)
    return match.group(1) if match else None


def parse_linkedin_job(page: str, job_id: str) -> Posting:
    body = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', page, re.S)
    return Posting(
        source="linkedin",
        company=_first(r'topcard__org-name-link[^>]*>(.*?)</a>', page) or "",
        title=_first(r'top-card-layout__title[^>]*>(.*?)</h2>', page) or "",
        url=f"https://www.linkedin.com/jobs/view/{job_id}",
        location=_first(r'topcard__flavor--bullet[^>]*>(.*?)</span>', page),
        description=_html_to_text(body.group(1)) if body else "",
    )


def parse_linkedin_search(page: str) -> list[dict]:
    """One results page of the guest search: id, title, company, location, relative date."""
    results = []
    for card in re.split(r"<li>", page)[1:]:
        job_id = re.search(r"jobPosting:(\d+)", card)
        if not job_id:
            continue
        results.append(
            {
                "id": job_id.group(1),
                "url": f"https://www.linkedin.com/jobs/view/{job_id.group(1)}",
                "title": _first(r'base-search-card__title[^>]*>(.*?)</h3>', card),
                "company": _first(r'base-search-card__subtitle[^>]*>(.*?)</h4>', card),
                "location": _first(r'job-search-card__location[^>]*>(.*?)</span>', card),
                "fecha": _first(r'<time[^>]*>(.*?)</time>', card),
            }
        )
    return results


def read(url: str, get=_get) -> Posting:
    job_id = linkedin_id(url)
    if job_id:
        return parse_linkedin_job(get(LINKEDIN_JOB.format(id=job_id)), job_id)
    parts = urlsplit(url)
    segments = [s for s in parts.path.split("/") if s]
    if "myworkdayjobs.com" in parts.netloc:
        from tools.workday import company_name, job_api_url, parse_job

        return parse_job(json.loads(get(job_api_url(url))), company_name(url), url)
    if parts.netloc == "jobs.lever.co" and len(segments) >= 2:
        job = json.loads(get(f"https://api.lever.co/v0/postings/{segments[0]}/{segments[1]}"))
        return parse_lever([job], board=segments[0])[0]
    if "greenhouse.io" in parts.netloc and "jobs" in segments:
        board, job = segments[segments.index("jobs") - 1], segments[segments.index("jobs") + 1]
        data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job}?content=true"))
        return parse_greenhouse({"jobs": [data]}, board=board)[0]
    if parts.netloc == "jobs.ashbyhq.com" and len(segments) >= 2:
        data = json.loads(get(f"https://api.ashbyhq.com/posting-api/job-board/{segments[0]}?includeCompensation=true"))
        for posting in parse_ashby(data, board=segments[0]):
            if segments[1] in posting.url:
                return posting
        raise LookupError("El aviso ya no figura en el portal de Ashby (puede estar cerrado).")
    raise ValueError("No sé leer este sitio sin el navegador: abrilo en el navegador de Claude.")


def search_linkedin(term: str, place: str, remote: bool, days: int, pages: int = 2, get=_get) -> list[dict]:
    found: dict[str, dict] = {}
    for page in range(pages):
        url = LINKEDIN_SEARCH.format(
            q=quote(term), loc=quote(place), secs=days * 86400, remote="&f_WT=2" if remote else "", start=page * 25
        )
        for row in parse_linkedin_search(get(url)):
            found.setdefault(row["id"], row)
    return list(found.values())


def _option(args: list[str], name: str, default=None):
    return args[args.index(name) + 1] if name in args else default


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args[:1] == ["leer"] and len(args) >= 2:
        try:
            posting = read(args[1])
        except Exception as exc:
            print(f"No pude leer el aviso: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(asdict(posting), ensure_ascii=False, indent=1))
        return 0
    if args[:1] == ["linkedin"] and len(args) >= 2:
        rows = search_linkedin(
            args[1],
            place=_option(args, "--lugar", "Argentina"),
            remote="--remoto" in args,
            days=int(_option(args, "--dias", 7)),
        )
        out = _option(args, "--guardar")
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{len(rows)} avisos guardados en {out}")
        else:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
