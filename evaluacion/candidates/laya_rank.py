"""Candidate G: Laya multilingual (Jev-class "System 1" decision model).

Uses a two-option `choice` with neutral keys, as its model card recommends over `noul`.
The card also warns it ships uncalibrated, so P(A) is used only for ordering, not as a probability.
"""

import time

import laya

from candidates.common import posting_text, read_input, write_output

MODEL = "convaiinnovations/laya-multilingual"
QUESTION = {
    "fit": {
        "type": "choice",
        "instructions": "¿El `aviso` encaja con el `perfil` y las preferencias del candidato?",
        "criteria": {"A": "sí, encaja con el perfil", "B": "no encaja con el perfil"},
    }
}

data = read_input()
postings = data["postings"]
t0 = time.perf_counter()
agent = laya.load(MODEL)
scores = []
for p in postings:
    result = agent.predict({"perfil": data["profile"][:1500], "aviso": posting_text(p, 1500)}, QUESTION)
    scores.append(float(result["answers"]["fit"]["probabilities"].get("A", 0.0)))
order = sorted(range(len(postings)), key=lambda i: -scores[i])
write_output([postings[i]["url"] for i in order], {postings[i]["url"]: {"puntaje": round(100 * scores[i]), "motivo": ""} for i in order}, seconds=round(time.perf_counter() - t0, 2),
             score_spread=round(max(scores) - min(scores), 4))
