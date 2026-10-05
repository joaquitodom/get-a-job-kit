"""Bumeran / ZonaJobs (same platform) results pages -> Postings.

The `corrida-diaria` skill opens a results page in the built-in browser, runs `extraer.js` on it and saves the
result; `uv run python -m tools.portales <fuente> <archivo>` turns it into data/externos/<fecha>-<fuente>.json.
Low volume and no evasion: a page showing a challenge or CAPTCHA is refused, never worked around.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from urllib.parse import urljoin, urlsplit, urlunsplit

from tools.sources import Posting

WORK_MODES = {"presencial": "onsite", "híbrido": "hybrid", "hibrido": "hybrid", "remoto": "remote"}
BOILERPLATE = ("Postulación rápida",)
DAYS_RE = re.compile(r"hace (\d+) d[ií]as?")
SAME_DAY_RE = re.compile(r"hace \d+ (horas?|minutos?)|\bhoy\b")


SITES = {"bumeran": "https://www.bumeran.com.ar", "zonajobs": "https://www.zonajobs.com.ar"}


def search_url(site: str, term: str) -> str:
    """Results page for a search term. Only the sites whose terms he accepted the risk for; never LinkedIn."""
    if site not in SITES:
        raise ValueError(f"Sitio no soportado: {site}. Solo {', '.join(SITES)}.")
    plain = "".join(c for c in unicodedata.normalize("NFKD", term.lower()) if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return f"{SITES[site]}/empleos-busqueda-{slug}.html"


class ChallengePage(RuntimeError):
    pass


def _published(text: str, today: date) -> str | None:
    lowered = text.lower()
    if "más de" in lowered or "mas de" in lowered:
        return None  # a lower bound, not a date
    if m := DAYS_RE.search(lowered):
        return (today - timedelta(days=int(m.group(1)))).isoformat()
    if "ayer" in lowered:
        return (today - timedelta(days=1)).isoformat()
    if SAME_DAY_RE.search(lowered):
        return today.isoformat()
    return None


def _clean_url(url: str) -> str:
    """Drop query and fragment (utm tracking): the same posting must have one link across both sites."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def parse_cards(page: dict, source: str, today: date) -> list[Posting]:
    if page.get("challenge"):
        raise ChallengePage("La página mostró un control anti-bot. Claude no lo resuelve: si él está, que lo resuelva en el navegador y se vuelve a extraer; si no, esta fuente se saltea hoy.")
    postings = []
    for card in page.get("cards", []):
        h2 = [h["text"] for h in card["headings"] if h["tag"] == "H2"]
        h3 = [h["text"] for h in card["headings"] if h["tag"] == "H3"]
        if not h2:
            continue
        date_text = next((t for t in h3 if t.lower().startswith(("publicado", "actualizado"))), "")
        rest = [t for t in h3 if t != date_text]
        mode = next((WORK_MODES[t.lower()] for t in rest if t.lower() in WORK_MODES), None)
        rest = [t for t in rest if t.lower() not in WORK_MODES]
        description = card.get("description", "")
        for noise in BOILERPLATE:
            description = description.replace(noise, "")
        postings.append(Posting(
            source=source,
            company=rest[0] if rest else "",
            title=h2[0],
            url=_clean_url(urljoin(page["url"], card["href"])),
            location=rest[1] if len(rest) > 1 else None,
            work_mode=mode,
            description=description.strip(),
            published=_published(date_text, today),
        ))
    return postings
