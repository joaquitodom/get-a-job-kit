import json

import pytest

from tools.aviso import linkedin_id, parse_linkedin_job, parse_linkedin_search, read
from tools.search import SearchConfig, run_search
from tools.workday import cxs_base, days_ago, fetch_site, job_api_url

SITE = "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers"
BASE = "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers"


def test_workday_urls_map_to_their_json_endpoints():
    assert cxs_base(SITE) == BASE
    assert cxs_base("https://mastercard.wd1.myworkdayjobs.com/en-US/CorporateCareers/") == BASE
    assert job_api_url(SITE + "/job/Buenos-Aires/Analyst_R-1") == BASE + "/job/Buenos-Aires/Analyst_R-1"


@pytest.mark.parametrize(
    "text, days",
    [("Posted Today", 0), ("Posted Yesterday", 1), ("Posted 3 Days Ago", 3), ("Posted 30+ Days Ago", 30), (None, None)],
)
def test_workday_relative_dates(text, days):
    assert days_ago(text) == days


def _fake_workday(listing):
    def post_json(url, body):
        assert url == BASE + "/jobs" and body["searchText"] == "Buenos Aires"
        return {"total": len(listing), "jobPostings": listing}

    def get_json(url):
        path = url.removeprefix(BASE)
        return {"jobPostingInfo": {"title": f"Rol {path}", "jobDescription": "<p>Texto</p>", "location": "Buenos Aires, Argentina", "startDate": "2026-10-02", "externalUrl": SITE + path}}

    return post_json, get_json


def test_workday_keeps_only_recent_postings_and_reads_their_text():
    post_json, get_json = _fake_workday(
        [{"externalPath": "/job/a", "postedOn": "Posted Today"}, {"externalPath": "/job/b", "postedOn": "Posted 30+ Days Ago"}]
    )
    postings = fetch_site(SITE, "Buenos Aires", 3, post_json=post_json, get_json=get_json)
    assert [(p.title, p.description, p.source, p.company) for p in postings] == [("Rol /job/a", "Texto", "workday", "Mastercard")]


def test_workday_sites_join_the_search_and_a_broken_one_is_reported():
    post_json, get_json = _fake_workday([{"externalPath": "/job/a", "postedOn": "Posted Yesterday"}])

    def post(url, body):
        if "natura" in url:
            raise ConnectionError("timeout")
        return post_json(url, body)

    config = SearchConfig(terms=[], location="Buenos Aires, Argentina", workday=[SITE, "https://natura.wd3.myworkdayjobs.com/Careers"])
    result = run_search(config, get_json=get_json, post_json=post)
    assert [p.title for p in result.postings] == ["Rol /job/a"]
    assert [e.source for e in result.errors] == ["workday:https://natura.wd3.myworkdayjobs.com/Careers"]


def test_workday_list_loads_from_the_companies_section(tmp_path):
    path = tmp_path / "b.toml"
    path.write_text(f'terms = ["x"]\n[companies]\nworkday = ["{SITE}"]\n', encoding="utf-8")
    assert SearchConfig.load(path).workday == [SITE]


@pytest.mark.parametrize(
    "url, job_id",
    [
        ("https://www.linkedin.com/jobs/view/4468023502", "4468023502"),
        ("https://ar.linkedin.com/jobs/view/treasury-analyst-at-cookunity-4468023502?trk=x", "4468023502"),
        ("https://www.linkedin.com/jobs/search/?currentJobId=4468023502&keywords=x", "4468023502"),
        ("https://jobs.lever.co/yuno/abc", None),
    ],
)
def test_linkedin_ids_from_every_link_shape(url, job_id):
    assert linkedin_id(url) == job_id


LINKEDIN_PAGE = """<h2 class="top-card-layout__title">Treasury Analyst</h2>
<a class="topcard__org-name-link" href="x">CookUnity </a><span class="topcard__flavor topcard__flavor--bullet"> Argentina </span>
<div class="show-more-less-html__markup">About us<br><br>We need &amp; want you</div>"""


def test_linkedin_guest_page_is_parsed():
    p = parse_linkedin_job(LINKEDIN_PAGE, "1")
    assert (p.title, p.company, p.location) == ("Treasury Analyst", "CookUnity", "Argentina")
    assert "We need & want you" in p.description and p.url.endswith("/1")


def test_linkedin_search_cards_are_parsed():
    page = """<li><div data-entity-urn="urn:li:jobPosting:42"><h3 class="base-search-card__title"> Partner Manager </h3>
    <h4 class="base-search-card__subtitle"><a>dLocal</a></h4><span class="job-search-card__location">Uruguay</span>
    <time datetime="2026-10-01">4 days ago</time></div></li>"""
    assert parse_linkedin_search(page) == [
        {"id": "42", "url": "https://www.linkedin.com/jobs/view/42", "title": "Partner Manager", "company": "dLocal", "location": "Uruguay", "fecha": "4 days ago"}
    ]


def test_read_goes_to_the_public_api_of_each_site():
    calls = []

    def get(url):
        calls.append(url)
        if "lever" in url:
            return json.dumps({"text": "KAM", "hostedUrl": "https://jobs.lever.co/yuno/abc", "descriptionPlain": "d"})
        return LINKEDIN_PAGE

    assert read("https://jobs.lever.co/yuno/abc", get=get).title == "KAM"
    assert read("https://www.linkedin.com/jobs/view/4468023502", get=get).company == "CookUnity"
    assert calls == ["https://api.lever.co/v0/postings/yuno/abc", "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4468023502"]


def test_unknown_sites_send_him_to_the_browser():
    with pytest.raises(ValueError, match="navegador"):
        read("https://www.bumeran.com.ar/empleos/x.html", get=lambda u: "")
