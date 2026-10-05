"""Workday career sites (Mastercard, Natura, Citi and many banks) through their public JSON endpoints.

The careers page `https://<tenant>.<wdN>.myworkdayjobs.com/<site>` answers the same JSON its own page uses at
`/wday/cxs/<tenant>/<site>/jobs` (search, POST) and `/wday/cxs/<tenant>/<site>/job/<path>` (one posting, GET).
No login, no browser: the same data a visitor sees.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from tools.sources import Posting, _html_to_text, _iso_date

LANG_RE = re.compile(r"^[a-z]{2}-[A-Z]{2}$")
DAYS_RE = re.compile(r"(\d+)\+? days? ago", re.IGNORECASE)
PAGE = 20


def cxs_base(site_url: str) -> str:
    """`https://mastercard.wd1.myworkdayjobs.com/en-US/CorporateCareers` -> its JSON base URL."""
    parts = urlsplit(site_url)
    tenant = parts.netloc.split(".")[0]
    segments = [s for s in parts.path.split("/") if s and not LANG_RE.match(s)]
    if not segments:
        raise ValueError(f"No encuentro el sitio de Workday en {site_url}")
    return f"{parts.scheme}://{parts.netloc}/wday/cxs/{tenant}/{segments[0]}"


def job_api_url(job_url: str) -> str:
    """A posting's public URL (`.../CorporateCareers/job/Buenos-Aires/Title_R-1`) -> its JSON URL."""
    parts = urlsplit(job_url)
    segments = [s for s in parts.path.split("/") if s and not LANG_RE.match(s)]
    if "job" not in segments or segments.index("job") == 0:
        raise ValueError(f"No es un aviso de Workday: {job_url}")
    i = segments.index("job")
    tenant = parts.netloc.split(".")[0]
    return f"{parts.scheme}://{parts.netloc}/wday/cxs/{tenant}/{segments[i - 1]}/" + "/".join(segments[i:])


def days_ago(posted_on: str | None) -> int | None:
    """'Posted Today' -> 0, 'Posted Yesterday' -> 1, 'Posted 3 Days Ago' -> 3, 'Posted 30+ Days Ago' -> 30."""
    text = (posted_on or "").lower()
    if "today" in text or "hoy" in text:
        return 0
    if "yesterday" in text or "ayer" in text:
        return 1
    match = DAYS_RE.search(text)
    return int(match.group(1)) if match else None


def company_name(site_url: str) -> str:
    return urlsplit(site_url).netloc.split(".")[0].capitalize()


def parse_job(data: dict, company: str, public_url: str) -> Posting:
    info = data.get("jobPostingInfo", data)
    remote = (info.get("remoteType") or "").lower()
    return Posting(
        source="workday",
        company=company,
        title=info["title"].strip(),
        url=info.get("externalUrl") or public_url,
        location=info.get("location"),
        work_mode="remote" if "remote" in remote else "hybrid" if "hybrid" in remote else None,
        description=_html_to_text(info.get("jobDescription", "")),
        published=_iso_date(info.get("startDate")),
    )


def fetch_site(site_url: str, search_text: str, max_days: int, post_json, get_json, max_results: int = 100) -> list[Posting]:
    """Postings of one Workday site matching `search_text`, published in the last `max_days` days."""
    base = cxs_base(site_url)
    public = site_url.rstrip("/")
    company = company_name(site_url)
    postings, offset = [], 0
    while offset < max_results:
        page = post_json(f"{base}/jobs", {"appliedFacets": {}, "limit": PAGE, "offset": offset, "searchText": search_text})
        jobs = page.get("jobPostings", [])
        for job in jobs:
            age = days_ago(job.get("postedOn"))
            if age is None or age > max_days:
                continue
            path = job["externalPath"]
            postings.append(parse_job(get_json(base + path), company, public + path))
        offset += PAGE
        if len(jobs) < PAGE or offset >= page.get("total", 0):
            break
    return postings
