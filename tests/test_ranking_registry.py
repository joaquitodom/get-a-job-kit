import pytest

from tools.ranking.registry import CANDIDATES, get


def test_every_evaluated_candidate_is_available_to_the_daily_run():
    assert {"A", "B", "C", "D", "E", "G"} <= set(CANDIDATES)


def test_unknown_candidate_names_the_valid_ones():
    with pytest.raises(ValueError, match="A"):
        get("Z")
