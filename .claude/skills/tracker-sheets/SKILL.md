---
name: tracker-sheets
description: The Google Sheets version of the application tracker - an Excel file in their Google Drive folder that Google Sheets opens on the phone. Use during setup when they choose Google Sheets instead of Notion, or when they say "prefiero Google Sheets", "quiero una planilla", "usá Excel", "pasá el tablero a una planilla", and every time another skill updates the tracker and `tracker = "sheets"`.
---

# tracker-sheets

The tracker is one file, `Postulaciones.xlsx`, inside their **Google Drive for desktop** folder. Drive syncs it both ways, so they open it with the Google Sheets app on their phone and change the `Estado` column there; you read and write the local copy with `tools/planilla.py`. Same columns and states as the Notion database (see `tracker-notion` and CLAUDE.md).

## One-time setup

1. Ask whether they have **Google Drive for desktop** installed (the "Google Drive" drive in Windows Explorer, usually `G:\Mi unidad`). If not, walk them through it in plain steps: download from https://www.google.com/drive/download/, install, sign in with their Google account (they type their password, never you). Then find the folder: check `G:\Mi unidad`, `G:\My Drive` and the user folder for `Google Drive`.
   - If they do not want to install it, offer the local option: the same file in `postulaciones/Postulaciones.xlsx`, opened with Excel on the computer (not visible on the phone).
2. Create the file: `uv run python -m tools.planilla crear "<carpeta de Drive>/Busqueda laboral/Postulaciones.xlsx"`.
3. Store `tracker = "sheets"` and `sheets_path = "<ruta completa>"` in `profile/preferences.md` and commit.
4. Tell them, short: open the Google Sheets app, find `Postulaciones.xlsx` in Drive, and in the `Estado` column they only choose **Aprobado**, **Descartado** or **Retirado** from the dropdown. Everything else is filled by Claude. A changed state is never permission to submit: that "sí" is in chat.

## Reading and writing (every skill)

- **Read**: `uv run python -m tools.planilla leer "<sheets_path>"` prints every row as JSON. Use it wherever a skill reads the Notion database (skip postings whose `Link` is already there, find rows in `Aprobado`, and so on).
- **Write**: put the rows in `data/planilla-<fecha>.json` (a JSON list of objects with column names as keys) and run `uv run python -m tools.planilla guardar "<sheets_path>" data/planilla-<fecha>.json`. A row whose `Link` is already in the file is updated only in the columns you send, so their changes survive; anything else is appended. Batch all the rows of one step in one call.
- **CV**: write the PDF's full path in `CV` (or the CV family name in fixed-CV mode). Never upload files anywhere.
- **Email**: the Gmail link of the latest relevant email.
- Checkboxes (`Exterior`, `Descarte automático`, `Confirmación recibida`, `Requiere acción`): write `Sí` or leave empty.
- If the file is open in Excel on the computer the write can fail: tell them in one line to close it and retry.

## Status check ("qué hay nuevo")

Read the file and report in chat, in a few lines: rows moved to Aprobado since last time (offer `cv-para-puesto`), upcoming next steps, and counts per state.
