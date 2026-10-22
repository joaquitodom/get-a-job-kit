"""Fixed-CV mode: use one of their ready-made CVs for a posting instead of writing a new one.

  uv run python -m tools.elegir_cv                                  # list the available CVs
  uv run python -m tools.elegir_cv <familia> <Empresa_Puesto> [--en]

Only for `cv_fijos = true` in profile/busqueda.toml. The CVs live in cv/variantes/<familia>-es.pdf and
<familia>-en.pdf (one per job family the user targets) and are used exactly as they are. This copies the chosen PDF
to `pdf_carpeta/<Empresa_Puesto>/` with the neutral name `pdf_nombre` (plus `_EN` in English), like
`render_cv --postulacion` does, and prints the path to attach in Notion.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from tools.render_cv import application_copy

CONFIG = Path("profile/busqueda.toml")
VARIANTES = Path("cv/variantes")


def families(folder: Path = VARIANTES) -> list[str]:
    """Families that have both a Spanish and an English PDF."""
    es = {p.name.removesuffix("-es.pdf") for p in folder.glob("*-es.pdf")}
    en = {p.name.removesuffix("-en.pdf") for p in folder.glob("*-en.pdf")}
    return sorted(es | en)


def source_pdf(familia: str, english: bool, folder: Path = VARIANTES) -> Path:
    pdf = folder / f"{familia}-{'en' if english else 'es'}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(f"No existe {pdf}. Familias disponibles: {', '.join(families(folder)) or 'ninguna'}")
    return pdf


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    english = "--en" in args
    args = [a for a in args if a != "--en"]
    if not args:
        for f in families():
            print(f)
        return 0
    if len(args) != 2:
        print(__doc__)
        return 1
    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    if not (cfg.get("pdf_nombre") and cfg.get("pdf_carpeta")):
        print("Falta pdf_nombre o pdf_carpeta en profile/busqueda.toml.", file=sys.stderr)
        return 1
    try:
        pdf = source_pdf(args[0], english)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    copy = application_copy(pdf, Path(cfg["pdf_carpeta"]).expanduser(), args[1], cfg["pdf_nombre"], english=english)
    print(f"CV {args[0]} ({'inglés' if english else 'castellano'}) listo para postular: {copy}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
