"""Turn Notion tracker rows into evaluation labels (see the corrida-diaria skill).

  uv run python -m tools.labels <rows.json>   # rows as returned by the Notion connector's rows mode

Writes data/etiquetas.json as {link: "si" | "no"}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SI = {"Aprobado", "CV listo", "Postulado", "En proceso", "Entrevista", "Oferta", "Rechazado", "Sin respuesta", "Retirado"}


def labels_from_rows(rows: list[dict]) -> dict[str, str]:
    labels = {}
    for r in rows:
        link, estado = r.get("Link") or "", r.get("Estado")
        if not link:
            continue
        if estado in SI:
            labels[link] = "si"
        elif estado == "Descartado" and r.get("Descarte automático") != "__YES__":
            # Only his own discards teach his criteria; a rule's discard is the rule's decision.
            labels[link] = "no"
    return labels


def control_labels(rows: list[dict]) -> dict[str, str]:
    """Labels of the random control sample only: the unbiased subset the ranking eval should score on."""
    return labels_from_rows([r for r in rows if r.get("Muestra control") == "__YES__"])


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    labels = labels_from_rows(data.get("results", data) if isinstance(data, dict) else data)
    out = Path("data") / "etiquetas.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(labels, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = data.get("results", data) if isinstance(data, dict) else data
    control = control_labels(rows)
    (out.parent / "etiquetas-control.json").write_text(json.dumps(control, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sum(v == 'si' for v in labels.values())} si, {sum(v == 'no' for v in labels.values())} no. Guardado en {out}")
    print(f"De la muestra de control: {len(control)} etiquetas (data/etiquetas-control.json).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
