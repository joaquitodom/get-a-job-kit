---
name: corrida-diaria
description: The daily job-search run - find new postings, load them into Notion, check email, prepare CVs for approved cards, and end with one batched confirmation. Use on the scheduled daily task, or when he says "hacé la corrida", "buscá avisos nuevos", "qué hay hoy", "corrida diaria", "run the daily search", "any new jobs today".
---

# corrida-diaria

Order matters: nothing is marked as seen until it is safely in Notion, and nothing is submitted without his "sí" in chat.

## Steps

1. **Check the config.** If `profile/busqueda.toml` has no `terms` or no sources, stop and offer to run `armar-perfil` step 6b. Do not invent search terms.
1a. **Bumeran and ZonaJobs** (only if `profile/busqueda.toml` has `[portales]` with `sitios`, and `profile/preferences.md` records his consent with a date). Their terms forbid automated browsing and let them suspend the account; he accepted that risk. So:
   - Volume is his choice (he accepted the risk; the maintainer confirmed on 2026-09-28): use every term in `[portales] terminos` if set, else every term in `terms`, capped only if he set `max_terminos`; one results page per term and site. Days: only on the days in `[portales] dias` (for example `["martes", "viernes"]`), every day if unset. Never other sites, **never LinkedIn** in the browser.
   - For each site and term: `uv run python -m tools.portales url <sitio> "<término>"` gives the URL. Open it in the built-in browser, wait for the results, run the script in `tools/portales/extraer.js` with the browser's JavaScript tool, save its result as `data/portal-<sitio>-raw.json`, and run `uv run python -m tools.portales <sitio> data/portal-<sitio>-raw.json`.
   - If the page shows a challenge or CAPTCHA (the script returns `challenge: true`, or the tool says so), **you never solve it**: a CAPTCHA exists to check that a person is there, and only he is. Never retry with tricks, never change IP or browser.
     - If he is at the computer (an interactive session): pause and tell him "Bumeran pide verificar que sos humano. Resolvelo en el navegador de Claude y decime 'listo'." When he says so, run `extraer.js` again on the same page and continue.
     - If it is a scheduled run (nobody answering): skip that site for today and say so in the final message; the rest of the run continues.
   - Only read the results page. Do not open postings, do not click "Postular".
   - If `[portales]` is missing but he asked for these sites: ask him to confirm, record `Riesgo aceptado para Bumeran y ZonaJobs: <fecha>` in `preferences.md`, and add `[portales]\nsitios = ["bumeran", "zonajobs"]` to `busqueda.toml`.
1b. **Sources outside the code search** (browser sources, job-alert emails): each writes `data/externos/<fecha>-<fuente>.json`, a JSON list of postings with at least `source`, `title`, `url` (and `company`, `location`, `description` when known). `preparar` merges them with everything else; `confirmar` moves them to `data/externos/procesados/`.
2. **Prepare the batch:** `uv run python -m tools.daily preparar`. It searches, drops postings already seen, applies only his explicit deal-breakers (`[descartes]` in `busqueda.toml`) and writes `data/diario-<fecha>.json`. If a source failed, mention it in one line and continue.
3. **Load Notion** (batch the writes, per CLAUDE.md):
   - First make sure the database has every property listed in the `tracker-notion` skill; add any that are missing (older databases lack `Orden` and `Descarte automático`).
   - Before creating rows, read the database in the connector's `rows` mode (not SQL: on free Notion plans SQL queries have a usage limit) and skip every posting whose `Link` is already there. This keeps the load safe to repeat after a partial failure or a second run the same day.
   - A `select` value that is not already an option is rejected. If a posting's value does not match an existing option (for example a new `Sector`), leave that property empty rather than failing the batch.
   - Each posting in `avisos` becomes a row in state `Para decidir`, keeping the batch order in the `Orden` property. Postings with `control: true` also get `Muestra control` checked. If the batch has `control_archivo` instead (`muestra_control_destino = "archivo"`), the sample stays only in the batch file: nothing to mark in Notion.
   - **His filtering rules** (if `profile/preferences.md` has a `Reglas de filtrado` section): apply every rule there to each new row, whether or not the cap is reached. They say which postings go to `Descartado` (with `Descarte automático` checked and the `Motivo` the rule gives), which stay with a `Próximo paso` (for example "va por referido"), and which get a high or low `Puntaje`. Give every row in `Para decidir` a `Puntaje` (0 to 100) and a one-line `Motivo` (fit and gap). When a rule and the cap disagree, the rule wins.
   - **Cap** (only if the batch has `max_para_decidir`): after loading, if more than that many rows are in `Para decidir`, screen the ones **without** `Muestra control` using his criterion in `preferences.md` (his words: do not be picky; include roles that are a bit big for him; discard only other areas, clearly junior roles, duplicates and hard formal requirements he does not meet). Move the screened-out ones to `Descartado` with `Descarte automático` checked and a one-line `Motivo`. **Never screen out a `Muestra control` row**: that random sample is what lets the ranking evaluation measure methods without bias.
   - Each entry in `descartados` becomes a row in state `Descartado`, with its `motivo` in `Motivo` and `Descarte automático` checked, so he can see and undo it.
   - Fill `Puesto`, `Empresa`, `Link`, `Plataforma` (the `source`), `Modalidad` (only if known), `Fecha`. If the batch has `puntaje` / `motivo` (normal mode), put them in `Puntaje` and `Motivo`; in collection mode leave both empty. If it has `sueldo_usd_mes` ([min, max]), write it in `Sueldo USD/mes` as "min a max" (or just min).
   - If the batch lists an error with source `ranking`, the ranker failed and the batch is in random order: say so in one line in the final message.
4. **Only after every row is in Notion:** `uv run python -m tools.daily confirmar` (it confirms the most recent pending batch, even after midnight). If Notion failed partway, do not confirm: the next run retries, and step 3 skips the rows already created.
5. **Email:** run the `revisar-mails` skill.
6. **Approved cards:** for each card he moved to `Aprobado`, run `cv-para-puesto`. If there are more than 5, prepare the 5 with the highest `Puntaje` (the oldest if there are no scores) and tell him the rest wait for the next run (usage budget). If the database has a salary ask column (for example `Pretensión bruta ARS/mes`), fill it from the salary section of `preferences.md` for that type of role.
7. **One message at the end**, in this order, short:
   - What needs him (`Requiere acción`), first.
   - Follow-ups due today from the `contactos` skill (if `notion_contactos_id` is set): who, what he asked, days since the last contact.
   - Emails archived by `revisar-mails` (if any): sender, subject and one line of what each said. Always, even if it is a long list.
   - How many new postings are in `Para decidir`.
   - For every card in `CV listo`: company and role, posting link, the neutral-named PDF, and the salary ask for that type of role. He applies personally; when he says he did, mark `Postulado`.
   - If `mi_email` is set, send that same summary (CVs ready, doubtful ones, counts of the rest) as the daily report **to his own address only**; the kit lets that one send through without a prompt. Never add other recipients. If `reporte = "borrador"` in `busqueda.toml`, leave it as a Gmail draft to that address instead of sending it.
8. **After his "sí":** if `postulacion_asistida = true`, run the `postular` skill for the listed postings. Otherwise open each application page in the built-in browser, submit nothing, and let him apply; when he says he did, mark `Postulado` with the date. Never automate LinkedIn or any "Easy Apply" flow in either case.

## Normal mode (after the ranking evaluation)

`modo = "normal"` plus `ranking = "<A|B|C|D|E|G>"` in `busqueda.toml` orders the batch with that candidate (the same code that was evaluated, see `evaluacion/RESULTS.md`) and writes `puntaje` and `motivo` per posting. Only switch to it when the maintainer says which candidate won; until then keep collection mode.

## Label collection mode

When `max_para_decidir` caps the list, only the `Muestra control` rows are unbiased labels: export them too (`tools.labels` writes `data/etiquetas-control.json`) and tell the maintainer which file to evaluate on.

`modo = "recoleccion"` (the default while the ranking evaluation runs) shows him every new posting in random order, so no ranking method decides what he sees. Remind him, once per run and in one line, that moving each `Para decidir` card to `Aprobado` or `Descartado` is what teaches the system his criteria.

When asked for the labels ("exportá las etiquetas"), read the whole database in `rows` mode, save the result to `data/notion-filas.json`, and run `uv run python -m tools.labels data/notion-filas.json`. It writes `data/etiquetas.json` with these rules (do not apply them by hand):
   - `si`: `Aprobado` and every state after it (`CV listo`, `Postulado`, `En proceso`, `Entrevista`, `Oferta`, `Rechazado`, `Sin respuesta`, `Retirado`). Retirado happens after applying, so he wanted it.
   - `no`: `Descartado` **only if `Descarte automático` is unchecked** (he discarded it himself). Rule-based discards are the rules' decision, not his, and must not become labels.
   - Leave `Para decidir` and `Nuevo` out.

## Scheduling

Once his profile and search config are done, offer to schedule this as a daily task in Claude Desktop with the prompt "Hacé la corrida diaria". His laptop must be on and the app open at that time; a missed run is caught up when the laptop wakes.
