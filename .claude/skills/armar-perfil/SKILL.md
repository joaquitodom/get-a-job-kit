---
name: armar-perfil
description: First-time setup and profile interview. Builds profile/PROFILE.md, profile/preferences.md and cv/master-es.md from the user's existing CV, LinkedIn and a guided interview, then defines the job platforms and asks him to log into them in the built-in browser. Use when PROFILE.md still has template placeholders, or when he says "empecemos", "armá mi perfil", "configurá todo", "actualizá mi perfil", "agregá una experiencia", "set up my profile", "update my profile".
---

# armar-perfil

Goal: a PROFILE.md where every claim survives an interview question, plus preferences and a first master CV. He is not technical: you read and write all files; he only answers questions in chat.

## Steps

1. **Collect what already exists.** Ask him to drag his current CV (PDF or Word) into the chat, and for his LinkedIn URL. If he gives the URL, open it in the Claude Desktop built-in browser (ask him to log into LinkedIn there first if the page asks for it). Extract facts; do not copy phrasing blindly.
2. **Interview in blocks, one question at a time**, waiting for each answer: education, each job (what he actually did, tools, results with real numbers only), projects and coursework, certifications and courses, languages with evidence, tools and their level. Use the examples and vocabulary of his field, not of any field you assume.
3. **Classify skills into the three tiers** of CLAUDE.md. For each skill ask yourself: could he answer a deep technical question about it? If unsure, ask him directly: "¿Si te preguntan a fondo por X en una entrevista, lo podés defender?"
4. **Fill the hard-block sections**: ask explicitly "¿Hay algo que no hayas hecho o no sepas y que no quieras que aparezca nunca?" (goes to "No afirmar nunca") and "¿Firmaste algún acuerdo de confidencialidad o hay algo de un trabajo anterior que no se pueda contar?" (goes to "Confidencialidad").
5. **Preferences** (`profile/preferences.md`). Ask open questions, one at a time, and record only what he answers: sectors and their order, target roles and seniority, country and city, which work modes he accepts and in what order, max commute, whether he would work for companies in other countries and under what conditions, salary floor (record amount, currency, period and today's date; do not suggest a number from memory, since peso salaries go stale fast), things to always discard.
   - There are no defaults. If he does not know yet, record `a definir` and move on; help him think it through only if he asks.
   - If `profile/sugerencias.md` has content, it is someone else's reading of what he wants. Use each point only as a question ("Me anotaron que preferís X, ¿es así?") and record his answer, never the suggestion itself.
6. **Platforms**: agree on where to search. Propose options that fit his country and sectors (general boards, local boards, career pages of the companies he names or that lead his sectors) and let him choose. Record them in preferences. Then ask him to **open each platform in the built-in browser and log in himself**. Never type his passwords or codes. Confirm each login by checking the page shows him as signed in.
6b. **Search config** (`profile/busqueda.toml`): fill it only from what he confirmed.
   - `terms`: search phrases derived from his target roles; show them to him and let him adjust.
   - `location`, `country`: from his answers.
   - `jobspy_sites`: the general boards he chose among LinkedIn, Indeed and Google.
   - `[companies]`: for each company he names or that leads his sectors, open its careers page in the built-in browser and check whether the job links go to `boards.greenhouse.io/<id>`, `jobs.lever.co/<id>` or `jobs.ashbyhq.com/<id>`; if so, add `<id>` under that system. If they go to `<empresa>.wdN.myworkdayjobs.com/<sitio>`, add that careers page URL under `workday`. Companies on other systems stay for the browser flow; note them in preferences.
   - `[descartes]`: only what he confirmed as absolute ("nunca, bajo ningún concepto"). `title_terms` for words in the title, `work_modes` with any of `presencial`, `híbrido`, `remoto`. If he confirmed nothing absolute, leave it empty: everything else is a preference for ranking, not a discard.
   - `modo = "recoleccion"` until the ranking evaluation picks a method.
   - Run `uv run python -m tools.search` once and tell him how many postings came back per source.
7. **Write the master CV** `cv/master-es.md` as a curated subset of PROFILE, in the format of `docs/FORMATO-CV.md`, max 2 pages. Render it with `uv run python -m tools.render_cv cv/master-es.md` and show him the PDF.
8. **Commit** PROFILE, preferences and master with a short message in Spanish (no dashes).
9. Offer the next step: "¿Armamos el tablero en Notion para seguir las postulaciones?" (skill `tracker-notion`).
10. **Optional functions**: once the board exists, go through the table in the `guia` skill (section 3), one function at a time, explaining each in one line and asking whether they want it. Set up only the ones they accept; leave the rest off. They can change any of them later by saying so.

## Rules

- Anything uncertain gets `(?)` and a line in "Preguntas abiertas"; never guess.
- No em-dashes or en-dashes in any Spanish text.
- Keep his answers in his words where possible; rewrite only for CV bullets.
