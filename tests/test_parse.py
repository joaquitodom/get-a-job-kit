from tools.render_cv import parse_cv

SAMPLE = """# Ana Pérez
Finanzas · Modelado financiero · Excel · SQL
Buenos Aires, Argentina | [ana@example.com](mailto:ana@example.com) | +54 9 11 0000-0000 | [LinkedIn](https://linkedin.com/in/ana-example)

## Resumen
Economista con foco en banca y fintech.

## Experiencia
### Banco Ejemplo | Mar 2024 a Dic 2025
_Analista de Riesgo Crediticio | Buenos Aires_
- Construí un modelo de scoring en Excel y SQL.
- Automaticé el reporte mensual de mora.

## Proyectos
### Valuación DCF de una fintech · Excel, Python
_Trabajo práctico de la materia Finanzas Corporativas._
- Armé un DCF con tres escenarios.

## Habilidades
**Herramientas:** Excel avanzado, Power BI, SQL
"""


def test_parses_name():
    assert parse_cv(SAMPLE).name == "Ana Pérez"


def test_parses_tagline_as_first_plain_line_after_name():
    assert parse_cv(SAMPLE).tagline == "Finanzas · Modelado financiero · Excel · SQL"


def test_contact_line_splits_segments_and_keeps_links():
    contact = parse_cv(SAMPLE).contact
    assert contact[0] == ("Buenos Aires, Argentina", None)
    assert contact[1] == ("ana@example.com", "mailto:ana@example.com")
    assert contact[3] == ("LinkedIn", "https://linkedin.com/in/ana-example")


def test_sections_are_parsed_in_order():
    titles = [s.title for s in parse_cv(SAMPLE).sections]
    assert titles == ["Resumen", "Experiencia", "Proyectos", "Habilidades"]


def test_plain_text_in_a_section_is_a_paragraph():
    block = parse_cv(SAMPLE).sections[0].blocks[0]
    assert block.kind == "paragraph"
    assert block.text == "Economista con foco en banca y fintech."


def test_entry_heading_with_pipe_has_title_dates_role_and_location():
    entry = parse_cv(SAMPLE).sections[1].blocks[0]
    assert entry.kind == "entry"
    assert (entry.title, entry.dates) == ("Banco Ejemplo", "Mar 2024 a Dic 2025")
    assert (entry.role, entry.location) == ("Analista de Riesgo Crediticio", "Buenos Aires")


def test_bullets_attach_to_the_current_entry():
    entry = parse_cv(SAMPLE).sections[1].blocks[0]
    assert entry.bullets == [
        "Construí un modelo de scoring en Excel y SQL.",
        "Automaticé el reporte mensual de mora.",
    ]


def test_heading_with_middle_dot_is_a_project_with_stack_and_context():
    project = parse_cv(SAMPLE).sections[2].blocks[0]
    assert project.kind == "project"
    assert (project.title, project.stack) == ("Valuación DCF de una fintech", "Excel, Python")
    assert project.context == "Trabajo práctico de la materia Finanzas Corporativas."
    assert project.bullets == ["Armé un DCF con tres escenarios."]


def test_bold_label_line_is_a_skill():
    skill = parse_cv(SAMPLE).sections[3].blocks[0]
    assert skill.kind == "skill"
    assert (skill.label, skill.text) == ("Herramientas:", "Excel avanzado, Power BI, SQL")


WITH_POSTING = SAMPLE + """
<!--
Aviso original:
- Requisito: Excel avanzado
Rango salarial 2025–2026
-->
"""


def test_html_comment_with_the_posting_is_not_rendered():
    cv = parse_cv(WITH_POSTING)
    assert cv.sections[-1].blocks == parse_cv(SAMPLE).sections[-1].blocks
    assert cv.sections[1].blocks[0].bullets == parse_cv(SAMPLE).sections[1].blocks[0].bullets
