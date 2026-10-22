---
name: tracker-notion
description: Creates and maintains the Notion database that tracks job applications. Use once during setup, or when the user says "armá el tablero", "configurá Notion", "cómo van mis postulaciones", "qué hay nuevo", "actualizá Notion", "set up the tracker", "what's the status of my applications".
---

# tracker-notion

## One-time setup

1. Check the Notion connector is available in this session. If it is not, walk them through it in plain steps: in Claude Desktop open Settings, Connectors, add Notion, sign in to their Notion account and allow access. The user signs in themselves.
2. Ask where the user wants it (a page in their Notion). Create a database named **Postulaciones** with these properties:
   - `Puesto` (title)
   - `Empresa` (text)
   - `Estado` (select): Nuevo, Para decidir, Descartado, Aprobado, CV listo, Postulado, En proceso, Entrevista, Oferta, Rechazado, Sin respuesta, Retirado (meanings in CLAUDE.md)
   - `Puntaje` (number, 0 to 100)
   - `Motivo` (text, one line explaining the score)
   - `Sector` (select). Create it with one option per sector in `preferences.md`: Notion rejects a select value that is not already an option.
   - `Modalidad` (select): Presencial, Híbrido, Remoto
   - `Exterior` (checkbox)
   - `Link` (url)
   - `Plataforma` (text, not select: new sites keep appearing and a select would reject them)
   - `CV` (files)
   - `Próximo paso` (text)
   - `Fecha` (date, when the posting was found)
   - `Orden` (number, position in the day's batch)
   - `Descarte automático` (checkbox, set when a rule discarded it, not them)
   - `Muestra control` (checkbox, random sample that is never screened out; see corrida-diaria)
   - `Sueldo USD/mes` (text, e.g. "2000 a 3000"; empty when the posting shows no salary)
   - `Fecha postulación` (date)
   - `Confirmación recibida` (checkbox)
   - `Requiere acción` (checkbox)
   - `Email` (url, link to the latest relevant email)
   - `Última novedad` (text, one line summarizing that email)
3. Create a board view named `Tablero`, grouped by `Estado` and sorted by `Orden` ascending.
4. Store the database id in `profile/preferences.md` (`notion_database_id`) and commit.
5. Tell them: install the Notion app on their phone and turn on notifications for that page; in Notion the user only drags cards to **Aprobado** (quiero postularme), **Descartado** (no me interesa) or **Retirado** (ya no sigo). Anything that sends something on their behalf is confirmed in chat.

## Status check ("qué hay nuevo")

Query the database, then report in chat: cards moved to Aprobado since last time (and offer to prepare them with `cv-para-puesto`), upcoming next steps, and counts per state. Keep it to a few lines.
