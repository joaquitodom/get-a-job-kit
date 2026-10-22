"""Deterministic half of assisted applying (the `postular` skill drives the browser).

Decides, field by field, what can be filled from their data sheet and what must go back to them. Hard stops are
not negotiable: government IDs, passwords and account creation are always their to do, and demographic questions
are never guessed. Every submission is logged so a posting is never submitted twice.
"""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

LOG = Path("postulaciones/envios.json")

PROHIBITED = (
    "dni",
    "cuil",
    "cuit",
    "pasaporte",
    "passport",
    "tax id",
    "ssn",
    "social security",
    "documento",
    "password",
    "contrasena",
)
DEMOGRAPHIC = (
    "gender",
    "genero",
    "sexo",
    "disability",
    "discapacidad",
    "veteran",
    "race",
    "raza",
    "etnia",
    "ethnicity",
)
DATA = [
    ("linkedin", ("linkedin",)),
    ("email", ("email", "e-mail", "correo")),
    ("telefono", ("phone", "telefono", "celular", "mobile", "movil")),
    ("apellido", ("last name", "apellido", "surname", "family name")),
    ("nombre", ("first name", "nombre", "given name")),
    ("pretension", ("salary", "pretension", "remuneracion", "compensation", "sueldo")),
    (
        "disponibilidad",
        (
            "disponibilidad",
            "availability",
            "notice period",
            "start date",
            "empezar",
            "incorporacion",
        ),
    ),
    ("ciudad", ("ciudad", "city", "location", "ubicacion", "residencia", "localidad")),
]
SECOND_LEVEL = {"com", "gob", "gov", "org", "net", "edu", "co", "ac"}


def _norm(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )


def classify_field(label: str) -> tuple[str, str | None]:
    """('prohibido'|'demografico'|'dato'|'pregunta', data key or None)."""
    text = _norm(label)
    if any(p in text for p in PROHIBITED):
        return "prohibido", None
    if any(d in text for d in DEMOGRAPHIC):
        return "demografico", None
    if "nombre" in text and "apellido" in text:
        return "dato", "nombre_completo"
    for key, words in DATA:
        if any(w in text for w in words):
            return "dato", key
    return "pregunta", None


def _value(sheet: dict, key: str) -> str | None:
    if key == "nombre_completo":
        parts = [sheet.get("nombre"), sheet.get("apellido")]
        return " ".join(p for p in parts if p) or None
    value = sheet.get(key)
    return str(value) if value not in (None, "") else None


def plan_form(fields: list[dict], sheet: dict) -> dict:
    """What to do with one application form. modo: automatico | hibrido | preguntar | a_mano."""
    values, questions, stops, file_field = {}, [], [], None
    for f in fields:
        label, required = f["label"], f.get("required", False)
        if f.get("type") == "file":
            file_field = file_field or label
            continue
        kind, key = classify_field(label)
        if kind == "prohibido":
            stops.append(label)
        elif kind == "demografico":
            if not sheet.get("demograficos_prefiero_no_decir"):
                questions.append(label)
        elif kind == "dato":
            value = _value(sheet, key)
            if value is None:
                questions.append(label)
            else:
                values[label] = value
        elif required:
            questions.append(label)
    if stops:
        return {
            "modo": "a_mano",
            "motivo": "El formulario pide "
            + ", ".join(stops)
            + ": eso lo completa él.",
            "valores": values,
        }
    if questions:
        return {"modo": "preguntar", "preguntas": questions, "valores": values}
    if file_field:
        return {"modo": "hibrido", "archivo": file_field, "valores": values}
    return {"modo": "automatico", "valores": values}


def _site(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def destination_ok(posting_url: str, form_url: str) -> bool:
    """The form must be on the same site as the posting the user approved; a redirect elsewhere needs a new 'sí'."""
    return _site(posting_url) == _site(form_url) != ""


def _load(log: Path) -> list[dict]:
    return json.loads(log.read_text(encoding="utf-8")) if log.exists() else []


def already_submitted(url: str, log: Path = LOG) -> bool:
    return any(entry["url"] == url for entry in _load(log))


def submitted_today(log: Path = LOG) -> int:
    today = datetime.now().date().isoformat()
    return sum(1 for entry in _load(log) if entry["fecha"].startswith(today))


def record_submission(
    url: str, values: dict, confirmation: str, log: Path = LOG
) -> None:
    entries = _load(log)
    entries.append(
        {
            "url": url,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "campos": sorted(values),
            "confirmacion": confirmation[:300],
        }
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")


SHEET = Path("profile/datos-formularios.toml")


def main(argv: list[str] | None = None) -> int:
    """  plan <campos.json> [--pretension N]   -> JSON plan for one form (fields as read from the page)
         destino <url del aviso> <url del formulario>
         ya-enviado <url> | registrar <url> <valores.json> "<texto de confirmación>" | hoy"""
    import sys
    import tomllib

    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(main.__doc__)
        return 1
    cmd = args[0]
    if cmd == "plan":
        if not SHEET.exists():
            print("Falta profile/datos-formularios.toml: la postulación asistida no está configurada.", file=sys.stderr)
            return 2
        sheet = tomllib.loads(SHEET.read_text(encoding="utf-8"))
        if "--pretension" in args:
            sheet["pretension"] = args[args.index("--pretension") + 1]
        fields = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        print(json.dumps(plan_form(fields, sheet), ensure_ascii=False, indent=1))
    elif cmd == "destino":
        print("ok" if destination_ok(args[1], args[2]) else "otro-sitio")
    elif cmd == "ya-enviado":
        print("si" if already_submitted(args[1]) else "no")
    elif cmd == "registrar":
        record_submission(args[1], json.loads(Path(args[2]).read_text(encoding="utf-8")), args[3])
        print("registrado")
    elif cmd == "hoy":
        print(submitted_today())
    else:
        print(main.__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
