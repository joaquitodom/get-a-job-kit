"""Candidate C: GLiClass multilingual (Jev-class encoder) scores each posting against the profile."""

import time

from gliclass import GLiClassModel, ZeroShotClassificationPipeline
from transformers import AutoTokenizer

from candidates.common import posting_text, read_input, write_output

MODEL = "knowledgator/gliclass-multilang-mini"
FIT, NO_FIT = "encaja con el perfil del candidato", "no encaja con el perfil del candidato"

data = read_input()
postings = data["postings"]
t0 = time.perf_counter()
model = GLiClassModel.from_pretrained(MODEL)
tokenizer = AutoTokenizer.from_pretrained(MODEL)
pipe = ZeroShotClassificationPipeline(model, tokenizer, classification_type="single-label", device="cpu", progress_bar=False)
prompt = "Perfil del candidato: " + data["profile"][:1200]
results = pipe([posting_text(p, 1500) for p in postings], [FIT, NO_FIT], threshold=0.0, prompt=prompt, batch_size=4)
fit_score = [next((r["score"] for r in res if r["label"] == FIT), 0.0) for res in results]
order = sorted(range(len(postings)), key=lambda i: -fit_score[i])
write_output([postings[i]["url"] for i in order], {postings[i]["url"]: {"puntaje": round(100 * fit_score[i]), "motivo": ""} for i in order}, seconds=round(time.perf_counter() - t0, 2))
