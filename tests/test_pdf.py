import pytest

from tools.render_cv import PdfConversionError, convert_to_pdf


def _writes_pdf(calls, name):
    def convert(docx_path):
        calls.append(name)
        docx_path.with_suffix(".pdf").write_bytes(b"%PDF")
    return convert


def _fails(calls, name):
    def convert(docx_path):
        calls.append(name)
        raise RuntimeError(f"{name} unavailable")
    return convert


def test_uses_word_first_when_it_works(tmp_path):
    calls = []
    docx = tmp_path / "cv.docx"
    pdf = convert_to_pdf(docx, backends=[_writes_pdf(calls, "word"), _writes_pdf(calls, "soffice")])
    assert (pdf, calls) == (tmp_path / "cv.pdf", ["word"])


def test_falls_back_to_libreoffice_when_word_fails(tmp_path):
    calls = []
    convert_to_pdf(tmp_path / "cv.docx", backends=[_fails(calls, "word"), _writes_pdf(calls, "soffice")])
    assert calls == ["word", "soffice"]


def test_raises_plain_language_error_when_no_backend_works(tmp_path):
    with pytest.raises(PdfConversionError, match="Word"):
        convert_to_pdf(tmp_path / "cv.docx", backends=[_fails([], "word"), _fails([], "soffice")])


def test_a_backend_that_reports_success_without_a_pdf_counts_as_failure(tmp_path):
    calls = []
    convert_to_pdf(tmp_path / "cv.docx", backends=[lambda p: calls.append("word"), _writes_pdf(calls, "soffice")])
    assert calls == ["word", "soffice"]
