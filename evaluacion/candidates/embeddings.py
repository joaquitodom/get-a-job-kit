"""Candidate A: multilingual embeddings sort everything, a cross-encoder re-reads the top."""

import time

from sentence_transformers import CrossEncoder, SentenceTransformer

from candidates.common import posting_text, read_input, write_output

EMBEDDER = "intfloat/multilingual-e5-small"
RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANK_TOP = 20

data = read_input()
postings = data["postings"]
texts = [posting_text(p) for p in postings]

t0 = time.perf_counter()
embedder = SentenceTransformer(EMBEDDER, device="cpu")
query = embedder.encode("query: " + data["profile"], normalize_embeddings=True)
docs = embedder.encode(["passage: " + t for t in texts], normalize_embeddings=True, batch_size=16)
first = sorted(range(len(postings)), key=lambda i: -float(docs[i] @ query))
t1 = time.perf_counter()

top = first[:RERANK_TOP]
reranker = CrossEncoder(RERANKER, device="cpu", max_length=512)
scores = reranker.predict([(data["profile"][:1500], texts[i]) for i in top], batch_size=8)
reranked = [i for _, i in sorted(zip(scores, top), key=lambda x: -float(x[0]))]
t2 = time.perf_counter()

order = reranked + first[RERANK_TOP:]
n = len(order)
scores = {postings[i]["url"]: {"puntaje": round(100 * (1 - k / n)), "motivo": "Parecido con tu perfil (posición relativa, sin explicación)"} for k, i in enumerate(order)}
write_output([postings[i]["url"] for i in order], scores, embed_seconds=round(t1 - t0, 2), rerank_seconds=round(t2 - t1, 2))
