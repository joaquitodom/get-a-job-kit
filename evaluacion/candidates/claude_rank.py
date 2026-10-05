"""Candidate E: Claude scores every posting in one batch (baseline and ceiling).

The context is defined here, not inherited: `--system-prompt` replaces Claude Code's default prompt with
RUBRIC, and user/plugin settings, MCP servers, tools and skills are all turned off. `--json-schema`
enforces the output shape. Runs from a temporary directory so no project CLAUDE.md or hooks load.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time

from candidates.common import RUBRIC, posting_text, read_input, write_output

MODEL = os.environ.get("CLAUDE_EVAL_MODEL", "sonnet")
SCHEMA = {
    "type": "object",
    "properties": {"scores": {"type": "array", "items": {
        "type": "object",
        "properties": {"i": {"type": "integer"}, "score": {"type": "integer", "minimum": 0, "maximum": 100}, "motivo": {"type": "string"}},
        "required": ["i", "score", "motivo"]}}},
    "required": ["scores"],
}
ISOLATION = ["--setting-sources", "project", "--strict-mcp-config", "--tools", "", "--disable-slash-commands",
             "--no-session-persistence"]

data = read_input()
postings = data["postings"]
listing = "\n\n".join(f"[{i}] {posting_text(p, 1500)}" for i, p in enumerate(postings))
message = f"PERFIL:\n{data['profile'][:1500]}\n\nAVISOS (puntuá cada uno por su número i):\n{listing}"

t0 = time.perf_counter()
with tempfile.TemporaryDirectory() as tmp:
    result = subprocess.run(
        [shutil.which("claude"), "-p", "--model", MODEL, "--output-format", "json", "--system-prompt", RUBRIC,
         "--json-schema", json.dumps(SCHEMA), *ISOLATION],
        input=message, capture_output=True, text=True, encoding="utf-8", cwd=tmp, timeout=900,
    )
if result.returncode != 0:
    raise SystemExit(result.stderr[-1000:] or "claude -p failed")
events = json.loads(result.stdout)
final = [e for e in events if e.get("type") == "result"][-1] if isinstance(events, list) else events
if final.get("is_error") or not final.get("structured_output"):
    raise SystemExit("Claude no devolvio la salida estructurada: " + str(final.get("result"))[:800])
rows = {int(x["i"]): x for x in final["structured_output"]["scores"]}
scores = {i: int(x["score"]) for i, x in rows.items()}
usage = final.get("usage", {})
order = sorted(range(len(postings)), key=lambda i: -scores.get(i, -1))
write_output(
    [postings[i]["url"] for i in order],
    {postings[i]["url"]: {"puntaje": scores[i], "motivo": str(rows[i].get("motivo", ""))[:200]} for i in order if i in rows},
    seconds=round(time.perf_counter() - t0, 2), model=MODEL,
    input_tokens=usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0),
    output_tokens=usage.get("output_tokens"), cost_usd=final.get("total_cost_usd"), scored=len(scores),
)
