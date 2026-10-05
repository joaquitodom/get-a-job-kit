from datetime import date

from tools.salary import ExchangeRates, monthly_usd
from tools.sources import Posting

RATES = {"2026-09-01": 1535.0, "2026-09-04": 1550.0}


def fake_get(calls):
    def get(url):
        calls.append(url)
        key = "-".join(url.rstrip("/").split("/")[-3:])
        if key not in RATES:
            raise LookupError("no data for that day")
        return {"casa": "oficial", "venta": RATES[key], "fecha": key}
    return get


def P(**kw):
    base = dict(source="t", company="C", title="T", url="u", published="2026-09-01")
    return Posting(**(base | kw))


def rates(tmp_path, calls=None):
    return ExchangeRates(casa="oficial", get_json=fake_get([] if calls is None else calls), cache=tmp_path / "cot.json")


def test_ars_is_converted_at_the_rate_of_the_posting_date(tmp_path):
    p = P(salary_min=1_535_000, salary_max=3_070_000, salary_currency="ARS", salary_period="month")
    assert monthly_usd(p, rates(tmp_path)) == (1000.0, 2000.0)


def test_usd_stays_and_yearly_becomes_monthly(tmp_path):
    p = P(salary_min=24_000, salary_max=36_000, salary_currency="USD", salary_period="year")
    assert monthly_usd(p, rates(tmp_path)) == (2000.0, 3000.0)


def test_other_currencies_and_hourly_pay_stay_unknown(tmp_path):
    assert monthly_usd(P(salary_min=10, salary_currency="EUR", salary_period="month"), rates(tmp_path)) is None
    assert monthly_usd(P(salary_min=10, salary_currency="USD", salary_period="hour"), rates(tmp_path)) is None


def test_no_salary_is_unknown(tmp_path):
    assert monthly_usd(P(), rates(tmp_path)) is None


def test_weekend_uses_the_previous_business_day(tmp_path):
    r = rates(tmp_path)
    assert r.venta(date(2026, 9, 6)) == 1550.0  # Sunday -> Friday 4


def test_rates_are_cached_between_runs(tmp_path):
    calls = []
    rates(tmp_path, calls).venta(date(2026, 9, 1))
    again = []
    assert rates(tmp_path, again).venta(date(2026, 9, 1)) == 1535.0
    assert again == []


def test_unreachable_api_gives_unknown_not_an_error(tmp_path):
    def down(url):
        raise ConnectionError("offline")
    r = ExchangeRates(casa="oficial", get_json=down, cache=tmp_path / "cot.json")
    p = P(salary_min=1_535_000, salary_currency="ARS", salary_period="month")
    assert monthly_usd(p, r) is None


def test_http_404_means_no_rate_that_day_so_it_looks_back(monkeypatch):
    import io
    import urllib.error

    import pytest

    import tools.salary as salary

    def urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO(b""))

    monkeypatch.setattr(salary.urllib.request, "urlopen", urlopen)
    with pytest.raises(LookupError):
        salary._get_json("https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial/2026/12/01")
