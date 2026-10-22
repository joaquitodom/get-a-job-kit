---
name: cv-para-puesto
description: Tailors a CV for one specific job posting and records it in the Notion tracker. Use when the user pastes a job posting or a link, or says "armame el CV para este puesto", "quiero postularme a esto", "mirá este aviso", "hacé el CV para X", "prepará los aprobados", "tailor my CV for this job", and when Notion cards are in state Aprobado.
---

# cv-para-puesto

> **Tracker:** if `tracker = "sheets"` in `profile/preferences.md`, every Notion step below is done on the spreadsheet instead, with the read and write commands of the `tracker-sheets` skill (same columns and states; no file uploads, the PDF path goes in `CV`).

## Fixed-CV mode (`cv_fijos = true` in `busqueda.toml`)

The user decided to use only their ready-made CVs: one per job family in `cv/variantes/`, each in Spanish (`-es`) and English (`-en`). In this mode you do **not** write or edit any CV:
1. Read the posting (step 1 below) and pick the family whose title and emphasis fit it best, in the posting's language.
2. `uv run python -m tools.elegir_cv <familia> <Empresa_Puesto> [--en]` copies that PDF with the neutral name; `uv run python -m tools.elegir_cv` lists the families.
3. Do steps 6 to 8 below with that PDF, and write in `Próximo paso` which CV you used (family and language) so the user can see it. Mention the gaps for the interview as usual.
Never change the variants for one posting. If none fits, say so and ask them.

## Steps

1. **Get the posting.** If it is a link, first try `uv run python -m tools.aviso leer <link>` (LinkedIn, Workday, Lever, Greenhouse and Ashby, no browser needed); if it says it cannot read that site, open it in the Claude Desktop built-in browser and read the page text. Save the full posting text at the bottom of the new CV file inside an HTML comment, so the reasoning can be reviewed later.
2. **Fit check (tell them in 3 short lines):** how well it matches `profile/preferences.md` (sector, seniority, location, work mode, salary if shown; for jobs abroad, whether it clears their threshold) and PROFILE; which requirements the user meets; which the user does not. If a hard preference is violated, say so and ask before continuing.
3. **Write** `postulaciones/<empresa>-<puesto>.md` (lowercase, hyphens, no accents) starting from `cv/master-es.md` (or `master-en.md` if the posting is in English). If `cv/variantes/` has base CVs by job family (for example sales, operations, data, management), start from the variant whose family is closest to the posting and say which one you used; otherwise start from the master. Always start from the master or a variant, never by copying an older file in `postulaciones/`: the master carries their latest corrections (titles, figures, wording the user approved), and old CVs may not. If PROFILE records approved wording for a fact (in Spanish and English), use it word for word.
   - Reorder sections and bullets so the most relevant come first; adjust the tagline and summary to the role.
   - Inside each section, entries go in reverse chronological order (most recent first). Write degree and thesis names in full, never abbreviated (for example "Trabajo Final de Máster", not "TFM").
   - Use the posting's vocabulary **only for things the user actually has**.
   - Never add a skill, tool, certification or number that is not in PROFILE. Respect "No afirmar nunca" and "Confidencialidad".
4. **Render**: `uv run python -m tools.render_cv postulaciones/<file>.md --postulacion "<Empresa>_<Puesto>"` (add `--en` for an English CV). Besides the working PDF, this copies the file the user will send with the neutral name `pdf_nombre` into `pdf_carpeta/<Empresa>_<Puesto>/`, so the filename never names the company. Upload that neutral-named copy to Notion. Check the PDF has at most 2 pages; if longer, trim the least relevant bullets.
5. **Self-review** with three lenses and fix what you find:
   - Fit: are the posting's key requirements that the user meets clearly visible?
   - Honesty: every line traceable to PROFILE? Skill tiers respected?
   - Spanish and ATS: no em/en dashes, no tables, clear section names.
6. **Tracker**: create or update the posting's Notion row (state `CV listo`, score, one-line reason, link to the posting) and attach the PDF. Attach the PDF this way: call the Notion connector's `create_file_upload` with the PDF's filename, save its answer (`upload_url` and `upload_headers`) to `data/upload.json`, run `uv run python -m tools.notion_upload <pdf> < data/upload.json`, then set the row's `CV` property to that file upload id with `update-page` (`[{"type": "file_upload", "file_upload": {"id": "<id>"}}]`) and delete `data/upload.json`. For a new row, create it first without the file and attach the file in a second call: passing the upload id to `create-pages` fails with "File not found". Do not upload with curl: on Windows it fails on the certificate revocation check, and `--ssl-no-revoke` would turn that security check off.
7. **Commit** the `.md`.
8. **Report** in chat: the neutral-named PDF's location, the posting link, the salary ask for this type of role (from the salary section of `preferences.md`, as the user stated it), the 2 or 3 changes you made, and gaps the user should be ready to talk about in an interview.

Never submit the application from this skill. The posting stays in `CV listo` until the batched confirmation described in CLAUDE.md (Browser and accounts), where their explicit "sí" in chat covers the listed postings.
