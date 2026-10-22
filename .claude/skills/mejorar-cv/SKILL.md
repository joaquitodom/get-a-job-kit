---
name: mejorar-cv
description: Reviews their current CV and rewrites it stronger - clearer title, results first, the vocabulary of their target roles, ATS friendly - without inventing anything. Use when they say "mejorá mi CV", "revisá mi CV", "qué le falta a mi CV", "mi CV es malo", "armame un CV de cero", "improve my CV", and inside armar-perfil step 7.
---

# mejorar-cv

Goal: a general CV (`cv/master-es.md`, and `cv/master-en.md` if they want it) that sells everything they really did, in the format of `docs/FORMATO-CV.md`, at most 2 pages.

## Steps

1. **Get the material.** Their current CV (they drag it into the chat) or, if they have none, `profile/PROFILE.md`. If PROFILE is not built, run `armar-perfil` first: every line of the CV must come from PROFILE.
2. **Diagnose in five lines at most**, the things that cost interviews, most important first. Typical ones: a title that does not say what they want to be hired as; duties instead of results; numbers missing where they exist; the best experience buried; generic skills lists; long paragraphs; typos and dashes; a format that ATS systems cannot read (tables, columns, text in images).
3. **Ask only for what is missing to fix it**: real numbers ("¿cuánto ahorraste, a cuántos clientes atendías, en cuánto tiempo?"), the scope of each job, results they did not mention. One question at a time. If there is no number, use honest qualitative impact.
4. **Rewrite**:
   - Title and summary aimed at their target roles (`preferences.md`), with their key evidence in two or three lines.
   - Bullets: past-tense verb + what + impact, 15 to 25 words, the strongest first in each job.
   - The vocabulary of their target postings, only for things they have.
   - Respect the skill tiers, "No afirmar nunca" and "Confidencialidad" in PROFILE.
5. **Render** with `uv run python -m tools.render_cv cv/master-es.md`, check it has at most 2 pages, and show them the PDF next to a short list of what changed and why.
6. Adjust with their comments, then commit. Add any new fact they told you to PROFILE first.

## Rules

- Never invent a title, number, tool or result. If it would not survive an interview question, it does not go in.
- Sell, do not apologize: strong verbs, results first, no filler ("responsable de", "encargado de").
- Spanish without dashes; no tables.
