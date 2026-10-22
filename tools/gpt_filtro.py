"""Screen the day's batch with GPT (Codex CLI, their ChatGPT plan) so the daily run spends less of their Claude plan.

  uv run python -m tools.gpt_filtro [data/diario-<fecha>.json]

Only runs if `filtro_gpt = true` in profile/busqueda.toml. Sends GPT their filtering rules (profile/preferences.md)
and their general CV (cv/master-es.md), never PROFILE.md or anything in a private folder, plus the postings in
chunks. GPT only proposes: a decision, a score and a one-line reason per posting. The result goes into the batch
file under `filtro_gpt`; the `corrida-diaria` skill loads it into Notion and spot-checks it. If Codex is missing,
times out or answers something invalid, the batch is left untouched and the skill screens as before.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

CONFIG = Path("profile/busqueda.toml")
PREFS = Path("profile/preferences.md")
MASTER = Path("cv/master-es.md")
DATA = Path("data")
CHUNK = 30
DESC_CHARS = 1500
DECISIONS = {"para_decidir", "descartado"}
DASHES = re.compile(r"\s*[–—]\s*")

PROMPT = """Sos el filtro de avisos de trabajo de un candidato. No uses herramientas: todo lo que necesitás está abajo.

Para CADA aviso de la lista devolvé su decisión según SUS reglas (sección "Reglas de filtrado", "Descartar siempre",
puestos objetivo, carriles y dirección de carrera de sus preferencias) y su CV:
- "decision": "para_decidir" si encaja con sus reglas (aunque le quede un poco grande), "descartado" si una regla lo descarta.
- "puntaje": 0 a 100, según las reglas de puntaje de sus preferencias.
- "motivo": una línea en español, máximo 150 caracteres, encaje y brecha. Si es descarte, empezá con la regla que lo descarta
  (por ejemplo "Pide mucha más experiencia", "Pide experiencia específica que no tiene", "Requiere vivir en otro país", "Otra área").
- "proximo_paso": solo si una regla lo pide (por ejemplo empresas en pausa o que van por referido); si no, "".
Si el aviso no dice algo (sueldo, modalidad), es dato desconocido: no lo penalices.
Calibración (él descarta a mano lo que pasa estos filtros, así que sé exigente):
- Aplicá literalmente las reglas de descarte, sobre todo "experiencia específica que no tiene" (cobranzas o mora, riesgo de
  crédito con modelos, costos y P&L, Product Management de varios años, seguros, marketing, tecnología o IT, auditoría,
  compliance) y "Pide mucha más experiencia" (8 años o más, Manager o Head con equipo, Director, VP en bancos globales).
- Empresas no financieras (consumo, industria, laboratorios, agro, consultoras de IT): solo finanzas corporativas con encaje
  muy alto; si no, descartá. Consultoras de selección con cliente confidencial: tratalas según el rol.
- Puntajes: 80 o más solo para multilaterales o un carril A muy claro; carril A bueno 65 a 79; carril B 55 a 70;
  carril C y empresas no financieras 35 a 55. En la duda, puntaje más bajo.
Nunca uses rayas largas ni medias. Respondé SOLO un JSON: una lista con un objeto por aviso, con las claves
"url", "decision", "puntaje", "motivo", "proximo_paso", en el mismo orden y con las mismas url que la lista.

=== PREFERENCIAS DEL CANDIDATO ===
{prefs}

=== CV GENERAL DEL CANDIDATO ===
{cv}

=== AVISOS ({n}) ===
{avisos}
"""


def enabled(config: Path = CONFIG) -> bool:
    if not config.exists():
        return False
    return bool(tomllib.loads(config.read_text(encoding="utf-8")).get("filtro_gpt", False))


def compact(aviso: dict) -> dict:
    keep = {k: aviso.get(k) for k in ("url", "title", "company", "location", "work_mode", "salary_text")}
    keep["description"] = (aviso.get("description") or "")[:DESC_CHARS]
    return {k: v for k, v in keep.items() if v not in (None, "", "None")}


def build_prompt(prefs: str, cv: str, avisos: list[dict]) -> str:
    return PROMPT.format(prefs=prefs, cv=cv, n=len(avisos), avisos=json.dumps([compact(a) for a in avisos], ensure_ascii=False, indent=1))


def run_codex(prompt: str, timeout: int = 900) -> str:
    """One non-interactive Codex call with the prompt on stdin; returns its last message."""
    codex = shutil.which("codex")  # on Windows the npm install is codex.cmd
    if codex is None:
        raise FileNotFoundError("codex")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "respuesta.md"
        subprocess.run(
            [codex, "exec", "--skip-git-repo-check", "-s", "read-only", "--output-last-message", str(out), "-"],
            input=prompt, text=True, encoding="utf-8", capture_output=True, timeout=timeout, check=False,
        )
        return out.read_text(encoding="utf-8") if out.exists() else ""


def parse(answer: str, urls: list[str]) -> list[dict]:
    """Validate GPT's answer: exactly one valid entry per posting, or ValueError."""
    match = re.search(r"\[.*\]", answer, re.S)
    if not match:
        raise ValueError("GPT no devolvió una lista JSON")
    rows = json.loads(match.group(0))
    by_url = {}
    for row in rows:
        url = row.get("url")
        if url not in urls or url in by_url:
            continue
        decision = row.get("decision")
        score = row.get("puntaje")
        if decision not in DECISIONS or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"Respuesta inválida para {url}")
        by_url[url] = {
            "url": url,
            "decision": decision,
            "puntaje": int(round(score)),
            "motivo": DASHES.sub(", ", str(row.get("motivo", ""))).strip()[:200],
            "proximo_paso": DASHES.sub(", ", str(row.get("proximo_paso") or "")).strip()[:200],
        }
    missing = [u for u in urls if u not in by_url]
    if missing:
        raise ValueError(f"Faltan {len(missing)} avisos en la respuesta")
    return [by_url[u] for u in urls]


def screen(avisos: list[dict], prefs: str, cv: str, runner=run_codex, chunk: int = CHUNK) -> list[dict]:
    results = []
    for start in range(0, len(avisos), chunk):
        part = avisos[start : start + chunk]
        results += parse(runner(build_prompt(prefs, cv, part)), [a["url"] for a in part])
    return results


def latest_batch() -> Path | None:
    files = sorted(DATA.glob("diario-*.json"))
    return files[-1] if files else None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not enabled():
        print("filtro_gpt no está activado en profile/busqueda.toml: el filtrado lo hace Claude.")
        return 0
    path = Path(args[0]) if args else latest_batch()
    if path is None or not path.exists():
        print("No hay lote diario para filtrar.")
        return 1
    batch = json.loads(path.read_text(encoding="utf-8"))
    avisos = batch.get("avisos", [])
    if not avisos:
        print("El lote no tiene avisos nuevos.")
        return 0
    try:
        results = screen(avisos, PREFS.read_text(encoding="utf-8"), MASTER.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("No encontré Codex (GPT). El filtrado lo hace Claude como siempre.", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"El filtro de GPT falló ({exc}). El filtrado lo hace Claude como siempre.", file=sys.stderr)
        return 2
    batch["filtro_gpt"] = results
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
    kept = sum(1 for r in results if r["decision"] == "para_decidir")
    print(f"GPT filtró {len(results)} avisos: {kept} a Para decidir, {len(results) - kept} descartados. Guardado en {path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
