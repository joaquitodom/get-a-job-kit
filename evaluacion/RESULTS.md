# Ranking candidates: feasibility run (no quality numbers yet)

Date: 2026-09-25. Input: 21 real postings from Indeed AR + LinkedIn (generic query "analista financiero", Buenos Aires) and a **fictional** finance profile. Machine: the maintainer's Linux laptop, CPU only (12 threads). Times are warm (models already downloaded).

Quality (recall of their "si" in the top K) is **not measured**: it needs their own labels. No labels were invented, because labeling them here would bias the comparison toward candidate E.

| | Candidate | Warm time, 21 postings | Download | Deterministic | Notes |
|---|---|---|---|---|---|
| A | multilingual-e5-small + mmarco mMiniLM reranker | 22.9 s (~1.1 s/posting) | ~1 GB | yes (three runs identical) | An earlier "different order" was a harness bug, not the model: with a trainable candidate in the run, every candidate was scored on a 50% split. Fixed (split only with real labels). |
| B | qwen2.5:3b via Ollama, JSON schema, shared RUBRIC | 74.5 s (3.5 s/posting) | 1.9 GB + Ollama | yes (two runs, same top 5) | 0 invalid JSON out of 21. Their GTX 1060 should be faster; not measured. |
| C | GLiClass multilang-mini | 140 s (6.7 s/posting) | 590 MB | yes | Slowest. Its top 5 includes logistics routing roles for a finance profile (observation, not a metric). |
| D | SetFit on e5-small | n/a | shares A's model | n/a | Correctly refuses to train without at least 4 "si" and 4 "no". Needs their labels. |
| E | Claude (sonnet) via `claude -p`, one batch, **isolated context** | 26-39 s | none | no: across three runs the top 5 shares most postings but the order changes | Context is defined by the harness: own system prompt (the shared RUBRIC), no user settings, MCP, tools or skills; `--json-schema` enforced (2 of 2 runs valid, previously 1 of 2). Content ≈ 14k tokens (~650 per posting; Spanish tokenizes denser than estimated). Reported 30k input = 3 turns with prompt caching (one cache write, then cache reads). 2.2k of 2.8k output tokens are thinking: turning it off is an untested saving. USD 0.09-0.10 API-equivalent per run. |
| F | Jev / Fastino | not run | | | Needs an account (Jev: waitlist; Fastino: free tier). |
| G | Laya multilingual, two-option choice | 23.5 s (~1.1 s/posting) | ~680 MB | yes (same top 5 across runs) | Its model card says it ships uncalibrated and is near chance zero-shot on typed decisions; fine-tuning is where its capability comes from. Published 2026-09-19. |

## LLM context is part of the experiment

B and E receive the same written instructions (`RUBRIC` in `candidates/common.py`), so they differ only in the model. E no longer inherits the maintainer's Claude Code configuration: an earlier run did, which added ~145k tokens of overhead and leaked their personal instructions into the answers.

## Takeaways so far

- Every local option runs on CPU. A and G take about a second per posting; B about 4 s and C about 6.5 s.
- E costs ~650 content tokens per posting with an isolated context; a batch of 50 is roughly 33k tokens plus caching turns. Scoring the whole day in one call is the efficient shape.
- D and G are the options that can **learn their criteria** (SetFit trains directly; Laya is designed to be fine-tuned). Both need their labels.

## Next

1. Their onboarding finishes, the first search fills Notion "Para decidir", the user moves cards to Aprobado or Descartado: those are the labels.
2. Rerun with labels: `uv run python -m tools.ranking.run_eval <postings.json> <profile.md> <labels.json>`.
3. Measure B on their GPU if B is still in contention.
