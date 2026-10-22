"""Candidate D: SetFit learns their own si/no from a few labeled postings, then scores the rest."""

import sys
import time

from setfit import SetFitModel, Trainer, TrainingArguments
from datasets import Dataset

from candidates.common import posting_text, read_input, write_output

BASE = "intfloat/multilingual-e5-small"
MIN_PER_CLASS = 4

data = read_input()
by_url = {p["url"]: p for p in data["train_postings"]}
rows = [(posting_text(by_url[u]), 1 if label == "si" else 0)
        for u, label in data["train_labels"].items() if u in by_url and label in ("si", "no")]
if min(sum(y == 1 for _, y in rows), sum(y == 0 for _, y in rows)) < MIN_PER_CLASS:
    sys.exit(f"SetFit necesita al menos {MIN_PER_CLASS} avisos etiquetados 'si' y {MIN_PER_CLASS} 'no' para entrenar.")

t0 = time.perf_counter()
model = SetFitModel.from_pretrained(BASE, device="cpu")
train = Dataset.from_dict({"text": [t for t, _ in rows], "label": [y for _, y in rows]})
Trainer(model=model, args=TrainingArguments(batch_size=8, num_epochs=1), train_dataset=train).train()
postings = data["postings"]
proba = model.predict_proba([posting_text(p) for p in postings])
order = sorted(range(len(postings)), key=lambda i: -float(proba[i][1]))
write_output([postings[i]["url"] for i in order], {postings[i]["url"]: {"puntaje": round(100 * float(proba[i][1])), "motivo": ""} for i in order}, seconds=round(time.perf_counter() - t0, 2), trained_on=len(rows))
