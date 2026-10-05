"""Candidate B: a small local LLM (via Ollama) scores each posting 0-100 with a reason, as fixed-schema JSON."""

import json
import os
import time
import urllib.request

from candidates.common import RUBRIC, posting_text, read_input, write_output

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/chat"
SCHEMA = {
    "type": "object",
    "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 100}, "motivo": {"type": "string"}},
    "required": ["score", "motivo"],
}

data = read_input()
postings = data["postings"]
t0 = time.perf_counter()
scores, reasons, invalid = [], [], 0
for p in postings:
    body = {
        "model": MODEL, "stream": False, "format": SCHEMA, "options": {"temperature": 0},
        "messages": [{"role": "system", "content": RUBRIC + "\nFormato: JSON con score (0 a 100) y motivo (una línea)."},
                     {"role": "user", "content": f"PERFIL:\n{data['profile'][:1500]}\n\nAVISO:\n{posting_text(p, 1500)}"}],
    }
    request = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        content = json.load(response)["message"]["content"]
    try:
        parsed = json.loads(content)
        scores.append(int(parsed["score"]))
        reasons.append(str(parsed.get("motivo", ""))[:200])
    except (ValueError, KeyError, TypeError):
        scores.append(-1)
        reasons.append("")
        invalid += 1
order = sorted(range(len(postings)), key=lambda i: -scores[i])
out = {postings[i]["url"]: {"puntaje": max(scores[i], 0), "motivo": reasons[i]} for i in order}
write_output([postings[i]["url"] for i in order], out, seconds=round(time.perf_counter() - t0, 2), model=MODEL,
             invalid_json=invalid, seconds_per_posting=round((time.perf_counter() - t0) / max(1, len(postings)), 2))
