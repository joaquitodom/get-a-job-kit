"""Salaries in dollars at each amount's own date (peso figures go stale in months; see CLAUDE.md, Salary data).

Rates come from argentinadatos.com (historical, per day). Default rate: official, sell side ("oficial", "venta");
`dolar = "<casa>"` in profile/busqueda.toml changes it (for example "blue" or "bolsa" for MEP).
Anything that cannot be converted honestly (other currencies, hourly pay, no rate available) is unknown: None.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from tools.sources import Posting

API = "https://api.argentinadatos.com/v1/cotizaciones/dolares/{casa}/{d:%Y/%m/%d}"
MAX_LOOKBACK_DAYS = (
    7  # weekends and holidays have no rate: use the latest business day before
)
PER_MONTH = {"month": 1.0, "year": 1 / 12}


def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "job-hunt-kit"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise LookupError("no rate published for that day") from exc  # e.g. today, early in the morning
        raise


class ExchangeRates:
    def __init__(
        self,
        casa: str = "oficial",
        get_json=_get_json,
        cache: Path = Path("data/cotizaciones.json"),
    ):
        self.casa, self.get_json, self.cache_path = casa, get_json, cache
        self._cache = (
            json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
        )

    def _save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self._cache, indent=1), encoding="utf-8")

    def venta(self, on: date) -> float | None:
        for back in range(MAX_LOOKBACK_DAYS + 1):
            day = on - timedelta(days=back)
            key = f"{self.casa}:{day.isoformat()}"
            if key in self._cache:
                return self._cache[key]
            try:
                value = float(self.get_json(API.format(casa=self.casa, d=day))["venta"])
            except LookupError:
                continue  # no rate that day
            except Exception:
                return None  # API unreachable: unknown, never a guess
            self._cache[key] = value
            self._save()
            return value
        return None


def monthly_usd(p: Posting, rates: ExchangeRates) -> tuple[float, float | None] | None:
    """(min, max) monthly salary in USD, or None when it is unknown."""
    if p.salary_min is None or p.salary_period not in PER_MONTH:
        return None
    factor = PER_MONTH[p.salary_period]
    if p.salary_currency == "USD":
        to_usd = 1.0
    elif p.salary_currency == "ARS":
        rate = rates.venta(
            date.fromisoformat(p.published) if p.published else date.today()
        )
        if not rate:
            return None
        to_usd = 1 / rate
    else:
        return None
    low = round(p.salary_min * factor * to_usd, 2)
    high = (
        round(p.salary_max * factor * to_usd, 2) if p.salary_max is not None else None
    )
    return low, high
