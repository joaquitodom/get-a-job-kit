import pytest

from tools.postular import already_submitted, classify_field, destination_ok, plan_form, record_submission

SHEET = {
    "nombre": "Ana", "apellido": "Pérez", "email": "ana@example.com", "telefono": "+54 9 11 0000-0000",
    "linkedin": "https://linkedin.com/in/ana", "ciudad": "Buenos Aires", "disponibilidad": "Inmediata",
    "pretension": "5000000", "demograficos_prefiero_no_decir": False,
}


@pytest.mark.parametrize("label,key", [
    ("First Name", "nombre"), ("Nombre", "nombre"), ("Last name", "apellido"), ("Apellido", "apellido"),
    ("Email", "email"), ("Correo electrónico", "email"), ("Phone", "telefono"), ("Teléfono celular", "telefono"),
    ("LinkedIn Profile", "linkedin"), ("Ciudad de residencia", "ciudad"),
    ("Salary expectations", "pretension"), ("Pretensión salarial bruta", "pretension"), ("Disponibilidad para empezar", "disponibilidad"),
])
def test_common_labels_map_to_his_data(label, key):
    assert classify_field(label) == ("dato", key)


@pytest.mark.parametrize("label", ["DNI", "CUIL / CUIT", "Número de pasaporte", "Tax ID", "Password", "Contraseña"])
def test_ids_and_passwords_are_hard_stops(label):
    assert classify_field(label)[0] == "prohibido"


@pytest.mark.parametrize("label", ["Gender", "Género", "Disability status", "Veteran status", "Race / Ethnicity"])
def test_demographic_questions_are_flagged(label):
    assert classify_field(label)[0] == "demografico"


def test_unknown_questions_are_flagged():
    assert classify_field("¿Por qué querés trabajar en nosotros?") == ("pregunta", None)


def field(label, type="text", required=True):
    return {"label": label, "type": type, "required": required}


def test_a_form_with_only_known_fields_is_automatic():
    plan = plan_form([field("First Name"), field("Email"), field("Salary expectations")], SHEET)
    assert plan["modo"] == "automatico"
    assert plan["valores"] == {"First Name": "Ana", "Email": "ana@example.com", "Salary expectations": "5000000"}


def test_a_file_field_makes_it_hybrid():
    plan = plan_form([field("First Name"), field("Resume/CV", type="file")], SHEET)
    assert plan["modo"] == "hibrido" and plan["archivo"] == "Resume/CV"


def test_any_hard_stop_hands_the_posting_to_him():
    plan = plan_form([field("First Name"), field("DNI")], SHEET)
    assert plan["modo"] == "a_mano" and "DNI" in plan["motivo"]


def test_required_unknown_question_goes_back_to_him():
    plan = plan_form([field("First Name"), field("¿Por qué querés trabajar acá?")], SHEET)
    assert plan["modo"] == "preguntar" and plan["preguntas"] == ["¿Por qué querés trabajar acá?"]


def test_optional_unknown_question_is_left_empty():
    plan = plan_form([field("First Name"), field("Cover letter", required=False)], SHEET)
    assert plan["modo"] == "automatico" and "Cover letter" not in plan["valores"]


def test_demographics_are_skipped_only_if_he_said_prefer_not_to_say():
    assert plan_form([field("Gender", required=False)], SHEET)["modo"] == "preguntar"
    assert plan_form([field("Gender", required=False)], SHEET | {"demograficos_prefiero_no_decir": True})["modo"] == "automatico"


def test_missing_data_for_a_known_field_goes_back_to_him():
    plan = plan_form([field("LinkedIn Profile")], {k: v for k, v in SHEET.items() if k != "linkedin"})
    assert plan["modo"] == "preguntar"


@pytest.mark.parametrize("posting,form,ok", [
    ("https://boards.greenhouse.io/stripe/jobs/1", "https://boards.greenhouse.io/stripe/jobs/1#app", True),
    ("https://www.bumeran.com.ar/empleos/x.html", "https://bumeran.com.ar/postulacion/x", True),
    ("https://ar.indeed.com/viewjob?jk=1", "https://empresa.workday.com/apply", False),
    ("https://www.galicia.com.ar/trabaja", "https://evil.com.ar/form", False),
])
def test_form_must_be_on_the_same_site_he_approved(posting, form, ok):
    assert destination_ok(posting, form) is ok


def test_log_prevents_submitting_twice(tmp_path):
    log = tmp_path / "envios.json"
    assert not already_submitted("u1", log)
    record_submission("u1", {"Email": "ana@example.com"}, "Gracias por postularte", log)
    assert already_submitted("u1", log)
