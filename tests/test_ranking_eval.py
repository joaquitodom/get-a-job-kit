from tools.ranking.eval import evaluate, lost_at_k, recall_at_k, split_labels
from tools.sources import Posting


def P(n):
    return Posting(source="t", company=f"C{n}", title=f"T{n}", url=f"u{n}")


LABELS = {"u1": "si", "u2": "no", "u3": "si", "u4": "tal vez", "u5": "no"}


def test_recall_counts_si_postings_inside_the_top_k():
    assert recall_at_k(["u1", "u2", "u3", "u4"], LABELS, k=2) == 0.5


def test_tal_vez_counts_neither_as_hit_nor_as_target():
    assert recall_at_k(["u4", "u1", "u3"], LABELS, k=3) == 1.0


def test_recall_is_undefined_without_si_labels():
    assert recall_at_k(["u2", "u5"], {"u2": "no", "u5": "no"}, k=1) is None


def test_lost_lists_si_postings_ranked_below_k_or_missing():
    assert lost_at_k(["u3", "u2", "u5"], LABELS, k=1) == ["u1"]


class Fixed:
    name = "fixed"
    trainable = False

    def __init__(self, order):
        self.order = order

    def rank(self, profile, postings):
        by_url = {p.url: p for p in postings}
        return [by_url[u] for u in self.order if u in by_url]


class Broken:
    name = "broken"
    trainable = False

    def rank(self, profile, postings):
        raise RuntimeError("model missing")


def test_evaluate_reports_metrics_and_time_for_each_ranker():
    postings = [P(n) for n in range(1, 6)]
    [result] = evaluate([Fixed(["u1", "u3", "u2", "u4", "u5"])], "perfil", postings, LABELS, ks=(2,))
    assert (result.name, result.error, result.recall[2]) == ("fixed", None, 1.0)
    assert result.seconds >= 0


def test_a_failing_ranker_is_reported_and_the_rest_still_run():
    postings = [P(n) for n in range(1, 6)]
    results = evaluate([Broken(), Fixed(["u1"])], "perfil", postings, LABELS, ks=(1,))
    assert results[0].error == "model missing"
    assert results[1].error is None


def test_split_is_deterministic_and_keeps_every_label_once():
    train, test = split_labels(LABELS, test_fraction=0.4, seed=7)
    assert split_labels(LABELS, test_fraction=0.4, seed=7) == (train, test)
    assert sorted(train | test) == sorted(LABELS) and not (train.keys() & test.keys())


class Learner:
    name = "learner"
    trainable = True

    def __init__(self):
        self.trained_on = None

    def fit(self, profile, postings, labels):
        self.trained_on = set(labels)

    def rank(self, profile, postings):
        return postings


def test_trainable_ranker_is_trained_on_one_split_and_scored_on_the_other():
    postings = [P(n) for n in range(1, 6)]
    learner = Learner()
    [result] = evaluate([learner], "perfil", postings, LABELS, ks=(5,), seed=7)
    assert learner.trained_on and not (learner.trained_on & set(result.ranked))


def test_without_si_no_labels_every_ranker_sees_all_postings_even_with_a_trainable_one():
    postings = [P(n) for n in range(1, 6)]
    unlabeled = {p.url: "?" for p in postings}
    results = evaluate([Learner(), Fixed(["u1", "u2", "u3", "u4", "u5"])], "perfil", postings, unlabeled, ks=(5,))
    assert [r.n for r in results] == [5, 5]


def test_result_reports_how_many_postings_were_ranked():
    postings = [P(n) for n in range(1, 6)]
    [result] = evaluate([Fixed(["u1", "u2"])], "perfil", postings, LABELS, ks=(2,))
    assert result.n == 5
