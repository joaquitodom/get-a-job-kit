import json
from datetime import date
from pathlib import Path

from tools.portales import parse_cards

PAGE = json.loads((Path(__file__).parent / "fixtures" / "portal_zonajobs.json").read_text(encoding="utf-8"))
TODAY = date(2026, 9, 26)


def parsed():
    return parse_cards(PAGE, source="zonajobs", today=TODAY)


def test_title_company_and_absolute_link():
    p = parsed()[0]
    assert (p.source, p.title, p.company) == ("zonajobs", "ANALISTA FINANCIERO", "VARIPLAST")
    assert p.url == "https://www.zonajobs.com.ar/empleos/analista-financiero-variplast-2189402.html"


def test_location_and_spanish_work_mode_are_mapped():
    first, second = parsed()[:2]
    assert (first.location, first.work_mode) == ("Sarandí, Buenos Aires", "onsite")
    assert second.work_mode == "hybrid"


def test_missing_work_mode_stays_unknown():
    assert parsed()[2].work_mode is None
    assert parsed()[2].location == "Capital Federal, Buenos Aires"


def test_relative_dates_become_absolute_and_vague_ones_unknown():
    a, b, c = parsed()
    assert a.published == "2026-09-15"
    assert b.published is None  # "más de 15 días" is not a date
    assert c.published == "2026-09-26"


def test_boilerplate_is_removed_from_the_description():
    assert parsed()[1].description == ""
    assert parsed()[0].description.startswith("Responsabilidad")


def test_a_challenge_page_is_refused_instead_of_parsed():
    import pytest

    from tools.portales import ChallengePage

    with pytest.raises(ChallengePage):
        parse_cards({**PAGE, "challenge": True}, source="zonajobs", today=TODAY)


def test_cross_brand_links_keep_their_site_and_lose_tracking_params():
    page = {"url": "https://www.zonajobs.com.ar/empleos-busqueda-x.html", "challenge": False, "cards": [
        {"href": "https://www.bumeran.com.ar/empleos/analista-1118450029.html?utm_source=zonajobs&utm_medium=free&utm_campaign=crossbrand",
         "description": "", "headings": [{"tag": "H2", "text": "Analista"}, {"tag": "H3", "text": "ACCIONA IT"}]}]}
    [p] = parse_cards(page, source="zonajobs", today=TODAY)
    assert p.url == "https://www.bumeran.com.ar/empleos/analista-1118450029.html"


def test_search_url_is_built_from_the_term_without_accents_or_spaces():
    from tools.portales import search_url

    assert search_url("bumeran", "Analista de Tesorería") == "https://www.bumeran.com.ar/empleos-busqueda-analista-de-tesoreria.html"
    assert search_url("zonajobs", "  FP&A  ") == "https://www.zonajobs.com.ar/empleos-busqueda-fp-a.html"


def test_unknown_site_is_rejected():
    import pytest

    from tools.portales import search_url

    with pytest.raises(ValueError):
        search_url("linkedin", "analista")
