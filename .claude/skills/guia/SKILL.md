---
name: guia
description: Explains what the kit does, what it can and cannot do, and which optional functions the person has on or off, and lets them turn each one on or off. Use at the very start (first session, before armar-perfil), and when they say "guía", "ayuda", "qué podés hacer", "cómo funciona", "qué opciones tengo", "prendé", "apagá", "activá", "desactivá", "help", "what can you do".
---

# guia

Talk in their language and register, short. This is a menu, not a manual: a few lines per part, and let them ask for more.

## 1. What the kit is (5 lines at most)

A job-search assistant that runs in Claude Desktop (Code tab):
- Builds one verified profile of their experience (`profile/PROFILE.md`) and a general CV.
- Finds postings every day and loads them into a Notion board, where they only move cards (Aprobado, Descartado, Retirado).
- Writes a tailored CV for each posting they approve, in PDF, never inventing anything.
- Reads their job emails and updates each application by itself.
- They apply and send messages themselves; Claude never submits, sends or accepts anything without their "sí" in chat.

## 2. What is always on

- Profile and general CV (`armar-perfil`), tailored CVs (`cv-para-puesto`), the Notion board (`tracker-notion`), interview prep and mock interviews (`preparar-entrevista`), reading job emails (`revisar-mails`).
- The honesty rules of CLAUDE.md: nothing in a CV that they did not do or cannot defend in an interview.

## 3. Optional functions

Read `profile/busqueda.toml` and `profile/preferences.md`, then show this table with the **current state** of each one (on, off, or not set up). Never turn one on without their answer; never assume what they want.

| Function | What it does | How it is stored | Default |
| --- | --- | --- | --- |
| Daily search (`corrida-diaria`) | Every weekday searches LinkedIn, Indeed, company career pages (Greenhouse, Lever, Ashby, Workday) and loads Notion. Needs the laptop on and Claude Desktop open at that time. | A scheduled task in Claude Desktop (`schedule` skill). | Off |
| Bumeran and ZonaJobs | Also searches these Argentine boards with the browser. Their terms forbid automated browsing: they may suspend the account; they must accept that risk. | `[portales]` in `busqueda.toml` + `Riesgo aceptado para Bumeran y ZonaJobs: <fecha>` in preferences. | Off |
| Daily report by email | Sends the day's summary **to their own address only**, or leaves it as a draft. | `mi_email` and `reporte = "enviar"` or `"borrador"`. | Off |
| Tidy the inbox | Labels every job email and takes out of the inbox the ones that ask nothing of them (confirmations, rejections, codes). Every archived email is listed in the report. Reversible, never deletes. | `gmail_etiqueta` and `archivar_sin_accion = true`. | Off (only the label) |
| Remote jobs abroad and multilateral banks (`busqueda-remota`) | Once a week, only very good fits, with their salary threshold in dollars. | `busqueda_remota = true` + the "jobs abroad" section of preferences + a weekly scheduled task. | Off |
| Contacts and follow-ups (`contactos`) | A second Notion board for referrals and headhunters; each day the report says who to follow up with. | `notion_contactos_id` in preferences. | Off |
| Assisted applying (`postular`) | Fills application forms after their "sí" (never passwords, IDs, CAPTCHAs or LinkedIn). | `postulacion_asistida = true` + `profile/datos-formularios.toml`. | Off |
| Neutral PDF name | The CV they send is always named `<pdf_nombre>.pdf`, so it does not reveal it was tailored. | `pdf_nombre` and `pdf_carpeta`. | Off |

To change one: they say it in their words ("prendé la búsqueda remota", "no archives mis mails"). Ask only what that function needs (one question at a time), write it in the file named in the table, commit, and confirm in one line. To turn one off, set it to false or remove the key (for a scheduled task, pause it with the scheduled-tasks tools).

## 4. What it never does

Never applies, sends a message or accepts terms without their "sí" in chat. Never types passwords or codes, never creates accounts, never solves CAPTCHAs. Never automates LinkedIn or "Easy Apply". Never invents experience, skills or numbers.

## 5. What it needs

- Claude Desktop with a paid Claude plan that includes Claude Code (Pro or higher; check claude.ai/pricing). The daily run uses a fair amount of the plan's usage: if they hit the limit, suggest running it fewer days a week or fewer search terms.
- Windows with Word (to make the PDFs; LibreOffice works too), a GitHub account, Notion (free) and Gmail, connected in Settings, Connectors.

## 6. Next step

If `profile/PROFILE.md` still has template placeholders: "¿Arrancamos con tu perfil?" and run `armar-perfil`. Otherwise offer the two or three functions that are off and would help most, in one line each.
