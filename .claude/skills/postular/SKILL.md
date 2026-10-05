---
name: postular
description: Assisted applying - after his explicit "sí" in chat for a listed batch, fill and submit application forms in the built-in browser, with hard stops that always hand the posting back to him. Use only from the end of corrida-diaria or when he says "postulá a estos", "mandá las postulaciones", "apply to these". Only runs if postulacion_asistida = true in profile/busqueda.toml and profile/datos-formularios.toml exists.
---

# postular

Off by default. It runs only if `postulacion_asistida = true` in `profile/busqueda.toml` **and** `profile/datos-formularios.toml` exists (template: `docs/datos-formularios.ejemplo.toml`). Otherwise the flow stays as before: open the page, he applies.

## Before asking for his "sí"

For every card in `CV listo`, open the posting's apply button in the built-in browser and read where it lands. The batched confirmation (CLAUDE.md) must list, per posting: company and role, the **domain of the form** (for example `boards.greenhouse.io`), the neutral-named PDF, the salary ask, and whether the form has a terms or privacy checkbox. His "sí" covers exactly those postings, those forms and those checkboxes.

## For each posting he approved

1. `uv run python -m tools.postular ya-enviado <link>`: if `si`, skip it (never submit twice). Also skip if its Notion state is already `Postulado` or later.
2. `uv run python -m tools.postular hoy`: if it reached `max_postulaciones_diarias` (default 10), stop for today and say so.
3. Open the form. `uv run python -m tools.postular destino <link del aviso> <url del formulario>`: if `otro-sitio`, stop and ask him again naming the new domain.
4. Run `tools/postular_campos.js` with the browser's JavaScript tool, save the `fields` to `data/campos.json`, and run `uv run python -m tools.postular plan data/campos.json --pretension <pretensión para este tipo de puesto>`.
5. By `modo`:
   - `a_mano`: the form asks for something only he can type (DNI, CUIL, passport, tax ID, a password). Do not fill anything; tell him which posting and why.
   - `preguntar`: ask him the listed questions (one message for the whole batch). Never invent answers. With his answers, repeat from step 4.
   - `hibrido` or `automatico`: fill each field in `valores` with `form_input`, nothing else.
6. **Bumeran and ZonaJobs**: their "Postulación rápida" sends the CV stored in his profile there, not the tailored one, and his recorded consent covers browsing those sites, not applying on them. Hand those postings to him unless `postular_en_portales = true` is set (only after he confirms both points; record the date in preferences).
6. **Stops that always hand the posting to him**: the page is a login or asks to create an account; a CAPTCHA or "verify you are human" (`challenge: true`); LinkedIn or any "Easy Apply"; a terms checkbox he did not approve in the confirmation.
7. **The CV file**: `hibrido` means the form needs the CV attached. Browsers do not let a script set a file path. Default: leave the form filled, tell him the exact neutral-named PDF path to attach, and let him press the submit button himself. (Attaching it by building the file from its bytes works technically but costs about 30 to 40 thousand tokens per CV; only do it if the maintainer enabled `adjuntar_cv_por_bytes = true`.)
8. Submit (click the form's own submit button) only when `modo` was `automatico`, or `hibrido` with the file attached, and everything above passed.
9. Read the page after submitting. Save the fields you sent as `data/valores.json` and run `uv run python -m tools.postular registrar <link> data/valores.json "<texto de confirmación de la página>"`. Mark the card `Postulado` with `Fecha postulación` only when the page confirms the submission; if it does not, leave it in `CV listo` and tell him.

## Never

- Type DNI, CUIL, passport, tax ID, passwords or codes. Create accounts. Solve CAPTCHAs.
- Answer demographic or health questions (gender, disability, etc.) unless `demograficos_prefiero_no_decir = true`, and then only with the form's "prefer not to say" option.
- Automate LinkedIn or Easy Apply.
- Submit a posting that was not in the list he said "sí" to.
