---
name: busqueda-remota
description: Weekly search for remote jobs with companies abroad and for jobs in multilateral or development banks, loaded into Notion for him to decide. Use on the weekly scheduled task, or when he says "buscá remotos", "trabajos para afuera", "búsqueda remota", "multilaterales", "BID", "Banco Mundial", "remote jobs abroad".
---

# busqueda-remota

Separate from the daily run because these postings are few, need more judgment, and he asked to see them once a week. Only postings that fit him **very well** reach Notion.

## Before starting

0. If `busqueda_remota` is not `true` in `profile/busqueda.toml`, this function is off: say so in one line and offer to turn it on (`guia` skill). Do nothing else.
1. Read `profile/PROFILE.md` and `profile/preferences.md`: the section on jobs abroad (his threshold over the best local offer, contractor or employee, the salary he asks in dollars) and any section on multilateral or development banks. If preferences say nothing about jobs abroad, stop and ask him: never assume he wants them.
2. Read `postulaciones/vistos.json` and the Notion tracker in `rows` mode: skip every posting already there.

## Where to look

- **LinkedIn, guest pages only** (never his account, never the browser): `uv run python -m tools.aviso linkedin "<término>" --lugar "Latin America" --remoto --dias 7`, and again with `--lugar Argentina`. Terms from the roles in his preferences (for example "payments partnerships", "partner manager payments", "FP&A remote", "treasury analyst remote", "strategy operations fintech"). Read the promising ones with `uv run python -m tools.aviso leer <link>`.
- **Remote-first companies** named in his preferences: their Greenhouse, Lever, Ashby or Workday boards (read with `tools.aviso leer`, or add them to `[companies]` in `busqueda.toml` so the daily search covers them too).
- **Multilateral and development banks** named in his preferences (for example IDB Group, World Bank Group, IMF, CAF, FONPLATA): their careers and consultancy portals in the built-in browser, read only. Consultant contracts count. Check the location (his city or remote from his country) and the eligibility rules (citizenship of member countries) against PROFILE.

## What goes into Notion

- Only roles that fit very well: his target roles, at his real level (PROFILE and the lanes in preferences), remote from his country or in his city for multilaterals. No sales on commission, nothing in his "Descartar siempre" list.
- Salary: if the posting shows one, compare it in dollars with his threshold (`tools/salary.py`); if it does not, that is unknown and never discards it.
- Each one becomes a row in `Para decidir` with `Puntaje` (0 to 100), a one-line `Motivo` that starts with "Remoto exterior:" or "Multilateral:" (fit, gap, contractor or employee), `Link`, `Plataforma`, `Fecha`, `Modalidad`, and `Exterior` checked when the employer is abroad. Add the URLs to `postulaciones/vistos.json`.
- At most 10 per week. If nothing is good, load nothing and say so.
- Never tailor CVs or apply here: he decides first in Notion.

## End

One short message in his language: how many you found, the best ones with one line each, and what you skipped and why (in one line). Commit and push his data.
