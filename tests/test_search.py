from tests.test_sources import JOBSPY_ROWS, load
from tools.search import SearchConfig, run_search

CONFIG = SearchConfig(
    terms=["analista financiero"],
    location="Buenos Aires",
    country="Argentina",
    jobspy_sites=["linkedin", "indeed"],
    greenhouse=["stripe"],
    lever=["palantir"],
    ashby=["ramp"],
)

API = {
    "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true": load("greenhouse"),
    "https://api.lever.co/v0/postings/palantir?mode=json": load("lever"),
    "https://api.ashbyhq.com/posting-api/job-board/ramp?includeCompensation=true": load("ashby"),
}


def fake_scrape(calls):
    def scrape(**kwargs):
        calls.append(kwargs)
        return JOBSPY_ROWS
    return scrape


def test_every_configured_company_board_is_fetched():
    fetched = []
    run_search(CONFIG, get_json=lambda url: fetched.append(url) or API[url], scrape=fake_scrape([]))
    assert sorted(fetched) == sorted(API)


def test_jobspy_gets_terms_location_country_and_sites_from_config():
    calls = []
    run_search(CONFIG, get_json=API.__getitem__, scrape=fake_scrape(calls))
    assert calls[0]["search_term"] == "analista financiero"
    assert (calls[0]["location"], calls[0]["country_indeed"]) == ("Buenos Aires", "Argentina")
    assert calls[0]["site_name"] == ["linkedin", "indeed"]


def test_results_from_all_sources_are_combined_and_deduplicated():
    result = run_search(CONFIG, get_json=API.__getitem__, scrape=fake_scrape([]))
    sources = {p.source for p in result.postings}
    assert sources == {"greenhouse", "lever", "ashby", "linkedin", "indeed"}
    assert len({p.url for p in result.postings}) == len(result.postings)


def test_a_failing_source_is_reported_and_the_rest_still_run():
    def get_json(url):
        if "lever" in url:
            raise ConnectionError("timeout")
        return API[url]

    result = run_search(CONFIG, get_json=get_json, scrape=fake_scrape([]))
    assert [e.source for e in result.errors] == ["lever:palantir"]
    assert "greenhouse" in {p.source for p in result.postings}


def test_config_loads_from_toml(tmp_path):
    f = tmp_path / "busqueda.toml"
    f.write_text(
        'terms = ["analista"]\nlocation = "Rosario"\ncountry = "Argentina"\n'
        'jobspy_sites = ["linkedin"]\n\n[companies]\nlever = ["lemon"]\n',
        encoding="utf-8",
    )
    cfg = SearchConfig.load(f)
    assert (cfg.terms, cfg.location, cfg.lever, cfg.greenhouse) == (["analista"], "Rosario", ["lemon"], [])


def test_linkedin_descriptions_are_requested_because_ranking_needs_them():
    calls = []
    run_search(CONFIG, get_json=API.__getitem__, scrape=fake_scrape(calls))
    assert calls[0]["linkedin_fetch_description"] is True


def test_google_gets_its_own_natural_language_query():
    calls = []
    run_search(CONFIG, get_json=API.__getitem__, scrape=fake_scrape(calls))
    assert calls[0]["google_search_term"] == "analista financiero jobs near Buenos Aires"


def test_config_ignores_daily_run_sections(tmp_path):
    f = tmp_path / "busqueda.toml"
    f.write_text('terms = ["a"]\nmodo = "recoleccion"\n\n[descartes]\ntitle_terms = ["ventas"]\n', encoding="utf-8")
    assert SearchConfig.load(f).terms == ["a"]
