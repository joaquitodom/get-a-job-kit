---
name: armar-perfil
description: First-time setup and profile interview. Builds profile/PROFILE.md, profile/preferences.md and cv/master-es.md from the user's existing CV, LinkedIn and a guided interview, then defines the job platforms and asks them to log into them in the built-in browser. Use when PROFILE.md still has template placeholders, or when the user says "empecemos", "armá mi perfil", "configurá todo", "actualizá mi perfil", "agregá una experiencia", "set up my profile", "update my profile".
---

# armar-perfil

Goal: a PROFILE.md where every claim survives an interview question, plus preferences and a first master CV. The user is not technical: you read and write all files; the user only answers questions in chat.

## Steps

1. **Collect what already exists.** Ask them to drag their current CV (PDF or Word) into the chat, and for their LinkedIn URL. If the user gives the URL, open it in the Claude Desktop built-in browser (ask them to log into LinkedIn there first if the page asks for it). Extract facts; do not copy phrasing blindly.
2. **Interview in blocks, one question at a time**, waiting for each answer: education, each job (what the user actually did, tools, results with real numbers only), projects and coursework, certifications and courses, languages with evidence, tools and their level. Use the examples and vocabulary of their field, not of any field you assume.
3. **Classify skills into the three tiers** of CLAUDE.md. For each skill ask yourself: could the user answer a deep technical question about it? If unsure, ask them directly: "¿Si te preguntan a fondo por X en una entrevista, lo podés defender?"
4. **Fill the hard-block sections**: ask explicitly "¿Hay algo que no hayas hecho o no sepas y que no quieras que aparezca nunca?" (goes to "No afirmar nunca") and "¿Firmaste algún acuerdo de confidencialidad o hay algo de un trabajo anterior que no se pueda contar?" (goes to "Confidencialidad").
5. **What job they want.** Ask: "¿Tenés claro qué puesto buscás?" If they are not sure, or want to change field, run `definir-objetivo` now and come back.
5b. **Preferences** (`profile/preferences.md`). Ask open questions, one at a time, and record only what the user answers: sectors and their order, target roles and seniority, country and city, which work modes the user accepts and in what order, max commute, whether the user would work for companies in other countries and under what conditions, salary floor (record amount, currency, period and today's date; do not suggest a number from memory, since salaries go stale fast), things to always discard.
   - There are no defaults. If the user does not know yet, record `a definir` and move on; help them think it through only if the user asks.
   - If `profile/sugerencias.md` has content, it is someone else's reading of what the user wants. Use each point only as a question ("Me anotaron que preferís X, ¿es así?") and record their answer, never the suggestion itself.
6. **Platforms**: agree on where to search. Propose options that fit their country and sectors (general boards, local boards, career pages of the companies the user names or that lead their sectors) and let them choose. Record them in preferences. Then ask them to **open each platform in the built-in browser and log in themselves**. Never type their passwords or codes. Confirm each login by checking the page shows them as signed in.
6a. **Automatic search: ask first.** "¿Querés que busque avisos por vos automáticamente?" If no, skip 6b and the daily run. If yes, ask one at a time: how often (every weekday, some days, once a week) and at what time; how far they would travel (km or minutes) and from which neighbourhood or city; work modes; minimum salary; seniority; anything to always exclude. Their answers go to `busqueda.toml` (6b) and to the scheduled task (step 10).
6b. **Search config** (`profile/busqueda.toml`): fill it only from what the user confirmed.
   - `terms`: search phrases derived from their target roles; show them to them and let them adjust.
   - `location`, `country`: from their answers.
   - `jobspy_sites`: the general boards the user chose among LinkedIn, Indeed and Google.
   - `[companies]`: for each company the user names or that leads their sectors, open its careers page in the built-in browser and check whether the job links go to `boards.greenhouse.io/<id>`, `jobs.lever.co/<id>` or `jobs.ashbyhq.com/<id>`; if so, add `<id>` under that system. If they go to `<empresa>.wdN.myworkdayjobs.com/<sitio>`, add that careers page URL under `workday`. Companies on other systems stay for the browser flow; note them in preferences.
   - `[descartes]`: only what the user confirmed as absolute ("nunca, bajo ningún concepto"). `title_terms` for words in the title, `work_modes` with any of `presencial`, `híbrido`, `remoto`. If the user confirmed nothing absolute, leave it empty: everything else is a preference for ranking, not a discard.
   - `modo = "recoleccion"` until the ranking evaluation picks a method.
   - Run `uv run python -m tools.search` once and tell them how many postings came back per source.
7. **Write the master CV** with the `mejorar-cv` skill: `cv/master-es.md` as a curated, stronger subset of PROFILE, in the format of `docs/FORMATO-CV.md`, max 2 pages. Render it and show them the PDF with what improved compared to their old CV.
8. **Commit** PROFILE, preferences and master with a short message in Spanish (no dashes).
9. **Tracker**: "¿Dónde querés seguir tus postulaciones: Notion (un tablero con tarjetas, gratis) o Google Sheets (una planilla)?" Explain each in one line; both work on the phone. Run `tracker-notion` or `tracker-sheets` accordingly. If they do not care, Notion.
10. **Optional functions**: once the tracker exists, schedule the automatic search if they asked for it in 6a (the `schedule` skill, with the days and time they chose, prompt "Hacé la corrida diaria"), and offer the daily report by email to their own address. Then go through the table in the `guia` skill (section 3), one function at a time, explaining each in one line and asking whether they want it. Set up only the ones they accept; leave the rest off. They can change any of them later by saying so.

## Rules

- Anything uncertain gets `(?)` and a line in "Preguntas abiertas"; never guess.
- No em-dashes or en-dashes in any Spanish text.
- Keep their answers in their words where possible; rewrite only for CV bullets.
