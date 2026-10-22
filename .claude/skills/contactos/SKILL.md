---
name: contactos
description: Keeps their networking board in Notion (referrals, introductions, headhunters) and tells them who to follow up with each day. Use when the user says "le escribí a X", "me contestó X", "me refirió", "a quién le tengo que escribir", "seguimientos", "headhunters", "contactos", "who should I follow up with", and in the daily run.
---

# contactos

> **Tracker:** the contacts board exists only in Notion. If they use Google Sheets for applications and want this function, offer to connect Notion just for contacts.

Referrals get far more interviews than cold applications, so every person the user asks for help is tracked like an application. The board is a second Notion database, `notion_contactos_id` in `profile/preferences.md`.

## Setup (once, only if `notion_contactos_id` is missing)

Ask them where to create it, then create a database **Contactos** with: `Contacto` (title), `Empresa` (text), `Cargo` (text), `Vínculo` (select: Fuerte, Bueno, Liviano, Amigo, Laboral jefe, Laboral amigo, Laboral Colega, Compañero colegio, Headhunter), `Vía` (select: WhatsApp, LinkedIn, Mail, En persona, Instagram), `Qué le pedí` (text), `Estado` (select: Por contactar, Mensaje enviado, Respondió, Me refirió, Sin respuesta, No puede ayudar), `Fecha contacto` (date), `Próximo seguimiento` (date), `Postulaciones relacionadas` (text), `Notas` (text). Store its id in `preferences.md`.

## When the user tells you about a contact

- New person: create the row. `Fecha contacto` is the day the user wrote. `Próximo seguimiento`: 5 business days later for someone the user knows, 7 for a headhunter or a cold contact, unless the user or the person gave a date ("hablamos el jueves").
- A reply: update `Estado`, write one line in `Notas` (date and what they said, no dashes), set the next `Próximo seguimiento` or clear it if nothing is pending.
- A referral: `Estado` = `Me refirió`, name the applications in `Postulaciones relacionadas`, and in the tracker write in `Próximo paso` of those cards that it goes through that referral (and, if the person asked them not to apply on the web, say so there too).
- Two follow-ups without an answer: `Sin respuesta`, no more reminders.

## Daily follow-ups (called from `corrida-diaria`)

Query the board for rows whose `Próximo seguimiento` is today or earlier and whose `Estado` is `Mensaje enviado` or `Respondió`. List them first in the daily message and report: name, company, what the user asked, how many days since the last contact. Offer to draft each message; **the user sends it themselves** (WhatsApp, LinkedIn) or you send it only after their "sí" in chat (email).

## Rules

- Never message anyone on their behalf, and never automate LinkedIn. You may search LinkedIn and open profiles in the built-in browser if the user asks; the user clicks Connect and sends.
- Write what the user wants to say in their own register; short, no dashes in Spanish.
- People's data stays in Notion: do not copy phone numbers or personal details into the repo.
