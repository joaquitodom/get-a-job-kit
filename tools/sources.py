"""Job posting sources, each normalized into one Posting shape so ranking and Notion only see one format."""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import UTC, datetime
from dataclasses import dataclass

TAG_RE = re.compile(r"<[^>]+>")
BLANKS_RE = re.compile(r"\n\s*\n+")


@dataclass(frozen=True)
class Posting:
    source: str
    company: str
    title: str
    url: str
    location: str | None = None
    work_mode: str | None = (
        None  # "onsite" | "hybrid" | "remote" | None when the posting does not say
    )
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    salary_text: str | None = None
    description: str = ""
    published: str | None = None  # ISO date (YYYY-MM-DD)


def _html_to_text(raw: str) -> str:
    text = TAG_RE.sub("\n", html.unescape(html.unescape(raw or "")))
    return BLANKS_RE.sub("\n\n", text).strip()


def _iso_date(value: str | None) -> str | None:
    return value[:10] if value else None


def parse_greenhouse(data: dict, board: str) -> list[Posting]:
    return [
        Posting(
            source="greenhouse",
            company=job.get("company_name") or board,
            title=job["title"].strip(),
            url=job["absolute_url"],
            location=(job.get("location") or {}).get("name"),
            description=_html_to_text(job.get("content", "")),
            published=_iso_date(job.get("first_published") or job.get("updated_at")),
        )
        for job in data.get("jobs", [])
    ]


WORK_MODES = {"onsite": "onsite", "on-site": "onsite", "hybrid": "hybrid", "remote": "remote"}


def _work_mode(value: str | None) -> str | None:
    return WORK_MODES.get((value or "").strip().lower())


def _lever_period(interval: str | None) -> str | None:
    for period in ("hour", "day", "week", "month", "year"):
        if interval and period in interval:
            return period
    return None


def _epoch_ms_to_date(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, UTC).date().isoformat()


def parse_lever(data: list, board: str) -> list[Posting]:
    postings = []
    for job in data:
        salary = job.get("salaryRange") or {}
        postings.append(
            Posting(
                source="lever",
                company=board,
                title=job["text"].strip(),
                url=job["hostedUrl"],
                location=(job.get("categories") or {}).get("location"),
                work_mode=_work_mode(job.get("workplaceType")),
                salary_min=salary.get("min"),
                salary_max=salary.get("max"),
                salary_currency=salary.get("currency"),
                salary_period=_lever_period(salary.get("interval")),
                description=job.get("descriptionPlain", "").strip(),
                published=_epoch_ms_to_date(job.get("createdAt")),
            )
        )
    return postings


def parse_ashby(data: dict, board: str) -> list[Posting]:
    return [
        Posting(
            source="ashby",
            company=board,
            title=job["title"].strip(),
            url=job["jobUrl"],
            location=job.get("location"),
            work_mode=_work_mode(job.get("workplaceType")),
            salary_text=(job.get("compensation") or {}).get("scrapeableCompensationSalarySummary"),
            description=job.get("descriptionPlain", "").strip(),
            published=_iso_date(job.get("publishedAt")),
        )
        for job in data.get("jobs", [])
        if job.get("isListed", True)
    ]


JOBSPY_PERIODS = {"hourly": "hour", "daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}


def _clean(value):
    """pandas uses NaN for missing values; treat it (and empty strings) as unknown."""
    if value is None or (isinstance(value, float) and value != value) or value == "":
        return None
    return value


def parse_jobspy(rows: list[dict]) -> list[Posting]:
    postings = []
    for row in rows:
        posted = _clean(row.get("date_posted"))
        postings.append(
            Posting(
                source=row["site"],
                company=_clean(row.get("company")) or "",
                title=str(row["title"]).strip(),
                url=row["job_url"],
                location=_clean(row.get("location")),
                # False only means JobSpy did not detect remote work; it does not prove the job is onsite.
                work_mode="remote" if row.get("is_remote") is True else None,
                salary_min=_clean(row.get("min_amount")),
                salary_max=_clean(row.get("max_amount")),
                salary_currency=_clean(row.get("currency")),
                salary_period=JOBSPY_PERIODS.get(_clean(row.get("interval")) or ""),
                description=_clean(row.get("description")) or "",
                published=posted.isoformat() if posted else None,
            )
        )
    return postings


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())


def posting_key(p: Posting) -> str:
    """Identity across sources: the same role at the same company, however each site spells it."""
    return f"{_normalize(p.company)}|{_normalize(p.title)}"


def dedup(postings: list[Posting]) -> list[Posting]:
    seen_urls: set[str] = set()
    seen_keys: set[str] = set()
    unique = []
    for p in postings:
        key = posting_key(p)
        if p.url in seen_urls or key in seen_keys:
            continue
        seen_urls.add(p.url)
        seen_keys.add(key)
        unique.append(p)
    return unique
