import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from tools.portales import ChallengePage, parse_cards

from tools.portales import search_url

if len(sys.argv) == 4 and sys.argv[1] == "url":
    print(search_url(sys.argv[2], sys.argv[3]))
    sys.exit(0)
if len(sys.argv) != 3:
    sys.exit("Uso: uv run python -m tools.portales url <sitio> <termino>  |  uv run python -m tools.portales <sitio> <archivo con el resultado de extraer.js>")
source, raw = sys.argv[1], Path(sys.argv[2])
try:
    postings = parse_cards(json.loads(raw.read_text(encoding="utf-8")), source=source, today=date.today())
except ChallengePage as exc:
    sys.exit(str(exc))
out = Path("data/externos") / f"{date.today().isoformat()}-{source}.json"
out.parent.mkdir(parents=True, exist_ok=True)
existing = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
out.write_text(json.dumps(existing + [asdict(p) for p in postings], ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(postings)} avisos de {source} agregados a {out}")
