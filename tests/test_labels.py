from tools.labels import labels_from_rows


def row(estado, link, auto="__NO__"):
    return {"Estado": estado, "Link": link, "Descarte automático": auto}


def test_approved_and_every_later_state_is_si():
    rows = [row(s, s) for s in ("Aprobado", "CV listo", "Postulado", "En proceso", "Entrevista", "Oferta", "Rechazado", "Sin respuesta", "Retirado")]
    assert set(labels_from_rows(rows).values()) == {"si"}


def test_his_own_discard_is_no():
    assert labels_from_rows([row("Descartado", "a")]) == {"a": "no"}


def test_rule_based_discards_are_not_labels():
    assert labels_from_rows([row("Descartado", "a", auto="__YES__")]) == {}


def test_undecided_rows_are_left_out():
    assert labels_from_rows([row("Para decidir", "a"), row("Nuevo", "b")]) == {}


def test_rows_without_a_link_are_skipped():
    assert labels_from_rows([row("Aprobado", "")]) == {}


def test_control_labels_are_the_subset_marked_as_control_sample():
    from tools.labels import control_labels

    rows = [dict(row("Aprobado", "a"), **{"Muestra control": "__YES__"}), row("Descartado", "b"), dict(row("Descartado", "c"), **{"Muestra control": "__YES__"})]
    assert control_labels(rows) == {"a": "si", "c": "no"}
