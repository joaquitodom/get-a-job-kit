import pytest

from tools import elegir_cv


def make(folder, *names):
    folder.mkdir(parents=True, exist_ok=True)
    for n in names:
        (folder / n).write_bytes(b"%PDF")


def test_families_are_listed_from_the_pdfs(tmp_path):
    make(tmp_path, "banca-es.pdf", "banca-en.pdf", "pagos-es.pdf")
    assert elegir_cv.families(tmp_path) == ["banca", "pagos"]


def test_source_pdf_picks_the_language(tmp_path):
    make(tmp_path, "banca-es.pdf", "banca-en.pdf")
    assert elegir_cv.source_pdf("banca", True, tmp_path).name == "banca-en.pdf"
    assert elegir_cv.source_pdf("banca", False, tmp_path).name == "banca-es.pdf"


def test_unknown_family_says_which_exist(tmp_path):
    make(tmp_path, "banca-es.pdf")
    with pytest.raises(FileNotFoundError, match="banca"):
        elegir_cv.source_pdf("pagos", False, tmp_path)


def test_copies_with_the_neutral_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    make(tmp_path / "cv/variantes", "banca-en.pdf")
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile/busqueda.toml").write_text('pdf_nombre = "CV_Nombre"\npdf_carpeta = "salida"\n', encoding="utf-8")
    assert elegir_cv.main(["banca", "Banco_Analista", "--en"]) == 0
    assert (tmp_path / "salida/Banco_Analista/CV_Nombre_EN.pdf").exists()
