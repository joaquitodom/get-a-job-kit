import json
from pathlib import Path

import datetime

from tools.sources import Posting, dedup, parse_ashby, parse_greenhouse, parse_jobspy, parse_lever

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def test_greenhouse_maps_title_link_company_and_location():
    p = parse_greenhouse(load("greenhouse"), board="stripe")[0]
    assert (p.source, p.company, p.title) == ("greenhouse", "Stripe", "Abuse Investigator")
    assert p.url == "https://stripe.com/jobs/search?gh_jid=8172510"
    assert p.location == "Seattle, San Francisco, New York City"


def test_greenhouse_description_is_plain_text_without_html():
    p = parse_greenhouse(load("greenhouse"), board="stripe")[0]
    assert p.description.startswith("Who we are")
    assert "<" not in p.description and "&lt;" not in p.description


def test_greenhouse_work_mode_is_unknown_and_date_is_first_published():
    p = parse_greenhouse(load("greenhouse"), board="stripe")[0]
    assert p.work_mode is None
    assert p.published == "2026-09-09"


def test_lever_uses_text_as_title_and_maps_workplace_type():
    p = parse_lever(load("lever"), board="palantir")[0]
    assert (p.source, p.company, p.title) == ("lever", "palantir", "Administrative Business Partner")
    assert (p.location, p.work_mode) == ("Singapore, Singapore", "hybrid")
    assert p.published == "2026-08-11"


def test_lever_salary_range_is_structured_when_listed():
    p = parse_lever(load("lever"), board="palantir")[1]
    assert (p.salary_min, p.salary_max, p.salary_currency, p.salary_period) == (2000, 3000, "USD", "month")


def test_lever_without_salary_leaves_it_unknown():
    p = parse_lever(load("lever"), board="palantir")[0]
    assert p.salary_min is None and p.salary_text is None


def test_ashby_skips_unlisted_postings_and_trims_title():
    postings = parse_ashby(load("ashby"), board="ramp")
    assert [p.title for p in postings] == ["Security Engineer, Cloud"]


def test_ashby_maps_work_mode_and_keeps_salary_as_text():
    p = parse_ashby(load("ashby"), board="ramp")[0]
    assert p.work_mode == "hybrid"
    assert p.salary_text == "$211.4K - $290.6K"


NAN = float("nan")

JOBSPY_ROWS = [
    {"site": "linkedin", "job_url": "https://www.linkedin.com/jobs/view/1", "title": "Analista de Riesgo",
     "company": "Banco Ejemplo", "location": "Buenos Aires, AR", "date_posted": datetime.date(2026, 9, 20),
     "interval": "monthly", "min_amount": 1500.0, "max_amount": 2000.0, "currency": "USD",
     "is_remote": False, "description": "Buscamos analista."},
    {"site": "indeed", "job_url": "https://ar.indeed.com/viewjob?jk=2", "title": "Analista Financiero",
     "company": "Fintech Ejemplo", "location": NAN, "date_posted": NAN,
     "interval": NAN, "min_amount": NAN, "max_amount": NAN, "currency": NAN,
     "is_remote": True, "description": NAN},
]


def test_jobspy_maps_site_as_source_and_structured_salary():
    p = parse_jobspy(JOBSPY_ROWS)[0]
    assert (p.source, p.company, p.title, p.published) == ("linkedin", "Banco Ejemplo", "Analista de Riesgo", "2026-09-20")
    assert (p.salary_min, p.salary_max, p.salary_currency, p.salary_period) == (1500.0, 2000.0, "USD", "month")


def test_jobspy_not_remote_means_unknown_work_mode_not_onsite():
    assert parse_jobspy(JOBSPY_ROWS)[0].work_mode is None


def test_jobspy_remote_flag_maps_to_remote():
    assert parse_jobspy(JOBSPY_ROWS)[1].work_mode == "remote"


def test_jobspy_nan_values_become_unknown():
    p = parse_jobspy(JOBSPY_ROWS)[1]
    assert (p.location, p.published, p.salary_min, p.salary_currency, p.description) == (None, None, None, None, "")


def _p(title, company="Banco Ejemplo", url="https://x/1", source="linkedin"):
    return Posting(source=source, company=company, title=title, url=url)


def test_dedup_drops_same_url_keeping_the_first():
    first, second = _p("Analista"), _p("Analista (copia)", source="indeed")
    assert dedup([first, second]) == [first]


def test_dedup_matches_company_and_title_ignoring_case_accents_and_spaces():
    a = _p("Analista de Crédito", url="https://a")
    b = _p("  analista de   CREDITO ", company="banco ejemplo", url="https://b")
    c = _p("Analista de Riesgo", url="https://c")
    assert dedup([a, b, c]) == [a, c]


def test_dedup_keeps_same_title_at_different_companies():
    a, b = _p("Analista", url="https://a"), _p("Analista", company="Otro Banco", url="https://b")
    assert dedup([a, b]) == [a, b]
