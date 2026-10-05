---
name: contactos
description: Keeps his networking board in Notion (referrals, introductions, headhunters) and tells him who to follow up with each day. Use when he says "le escribí a X", "me contestó X", "me refirió", "a quién le tengo que escribir", "seguimientos", "headhunters", "contactos", "who should I follow up with", and in the daily run.
---

# contactos

Referrals get far more interviews than cold applications, so every person he asks for help is tracked like an application. The board is a second Notion database, `notion_contactos_id` in `profile/preferences.md`.

## Setup (once, only if `notion_contactos_id` is missing)

Ask him where to create it, then create a database **Contactos** with: `Contacto` (title), `Empresa` (text), `Cargo` (text), `Vínculo` (select: Fuerte, Bueno, Liviano, Amigo, Laboral jefe, Laboral amigo, Laboral Colega, Compañero colegio, Headhunter), `Vía` (select: WhatsApp, LinkedIn, Mail, En persona, Instagram), `Qué le pedí` (text), `Estado` (select: Por contactar, Mensaje enviado, Respondió, Me refirió, Sin respuesta, No puede ayudar), `Fecha contacto` (date), `Próximo seguimiento` (date), `Postulaciones relacionadas` (text), `Notas` (text). Store its id in `preferences.md`.

## When he tells you about a contact

- New person: create the row. `Fecha contacto` is the day he wrote. `Próximo seguimiento`: 5 business days later for someone he knows, 7 for a headhunter or a cold contact, unless he or the person gave a date ("hablamos el jueves").
- A reply: update `Estado`, write one line in `Notas` (date and what they said, no dashes), set the next `Próximo seguimiento` or clear it if nothing is pending.
- A referral: `Estado` = `Me refirió`, name the applications in `Postulaciones relacionadas`, and in the tracker write in `Próximo paso` of those cards that it goes through that referral (and, if the person asked him not to apply on the web, say so there too).
- Two follow-ups without an answer: `Sin respuesta`, no more reminders.

## Daily follow-ups (called from `corrida-diaria`)

Query the board for rows whose `Próximo seguimiento` is today or earlier and whose `Estado` is `Mensaje enviado` or `Respondió`. List them first in the daily message and report: name, company, what he asked, how many days since the last contact. Offer to draft each message; **he sends it himself** (WhatsApp, LinkedIn) or you send it only after his "sí" in chat (email).

## Rules

- Never message anyone on his behalf, and never automate LinkedIn. You may search LinkedIn and open profiles in the built-in browser if he asks; he clicks Connect and sends.
- Write what he wants to say in his own register; short, no dashes in Spanish.
- People's data stays in Notion: do not copy phone numbers or personal details into the repo.
