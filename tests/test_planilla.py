import pytest

from tools import planilla


def test_crear_leer_guardar(tmp_path):
    ruta = tmp_path / "Postulaciones.xlsx"
    planilla.crear(ruta)
    assert planilla.leer(ruta) == []

    act, agr = planilla.guardar(ruta, [
        {"Puesto": "Analista", "Empresa": "A", "Estado": "Para decidir", "Link": "https://x/1"},
        {"Puesto": "Jefe", "Empresa": "B", "Estado": "Para decidir"},
    ])
    assert (act, agr) == (0, 2)

    # The user moves a card; Claude later updates another column only.
    act, agr = planilla.guardar(ruta, [{"Link": "https://x/1/", "Estado": "Aprobado"}])
    assert (act, agr) == (1, 0)
    planilla.guardar(ruta, [{"Link": "https://x/1", "Motivo": "encaja"}, {"Puesto": "jefe", "Empresa": "b", "Puntaje": 70}])

    filas = planilla.leer(ruta)
    assert len(filas) == 2
    assert filas[0]["Estado"] == "Aprobado" and filas[0]["Motivo"] == "encaja"
    assert filas[1]["Puntaje"] == 70


def test_no_pisa_y_rechaza_columnas(tmp_path):
    ruta = tmp_path / "p.xlsx"
    planilla.crear(ruta)
    with pytest.raises(SystemExit):
        planilla.crear(ruta)
    with pytest.raises(SystemExit):
        planilla.guardar(ruta, [{"Inventada": 1}])
