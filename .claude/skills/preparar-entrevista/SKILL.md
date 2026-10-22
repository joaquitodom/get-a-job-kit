---
name: preparar-entrevista
description: Prepares them for one interview - a guide with the format, the role, their evidence for each requirement, their pitch, STAR stories, likely questions with practiced answers, salary and a checklist - and runs a mock interview if the user wants. Use when an application moves to Entrevista, or when the user says "tengo una entrevista", "preparame para la entrevista", "simulacro", "qué me van a preguntar", "prep interview".
---

# preparar-entrevista

> **Tracker:** if `tracker = "sheets"` in `profile/preferences.md`, every Notion step below is done on the spreadsheet instead, with the read and write commands of the `tracker-sheets` skill (same columns and states; no file uploads, the PDF path goes in `CV`).

## Inputs

1. The application: the Notion row, the tailored CV in `postulaciones/` (the posting text is in its HTML comment) and the emails about the interview (format, who interviews, duration, language). If something is missing (time, interviewer, language), ask them in one line.
2. `profile/PROFILE.md`: only facts from there. Respect "No afirmar nunca" and "Confidencialidad" in every answer you write for them (no internal names or exact figures of past employers the user must keep private).
3. `profile/preferences.md`: salary for this type of role (with its date; if older than 3 months, ask whether it holds) and what the user wants from the job.

## The guide

Write `<Empresa>_<Rol>.html` in the folder `entrevistas_carpeta` from `profile/busqueda.toml` (default `../entrevistas`, outside the repo because it quotes their stories at length), one self-contained page the user can read on their phone. Sections, short:

1. **Format**: who, when, how long, language, what this round usually checks.
2. **The role in 3 lines**: what they need and why it fits them.
3. **Requirements vs their evidence**: each key requirement with their strongest proof from PROFILE, and the gaps with an honest way to address them.
4. **Pitch**: 60 seconds, in the interview language (and in English if any part is in English).
5. **Stories (STAR)**: 4 to 6 from PROFILE, each tagged with the questions it answers (negotiation, conflict, failure, leadership, numbers, ambiguity).
6. **Likely questions with answers the user can say in their own words**, including "why this company", "why did you leave", and the tricky ones for their profile.
7. **Salary**: one sentence with the number for this type of role and how to say it.
8. **Questions for them**: 3 or 4 that show judgment.
9. **Checklist**: link, CV version sent, what to have open, time zone.

Mark in the guide anything you inferred rather than read (for example the format of the round) so the user can check it.

## Mock interview (if the user asks)

One question at a time, in the interview language; wait for their answer; give short feedback (what worked, what to cut, a better closing line) and move on. Push them: the user asked to be tested. Do not write their answers for them unless the user asks.

## After

Update the tracker row (`Próximo paso`, interview date). After the interview, ask how it went and write two lines in the guide: what they asked and what to improve.
