# Kit de búsqueda laboral

Un asistente que arma un CV a medida para cada aviso de trabajo y lleva el seguimiento de tus postulaciones en Notion. Vos hablás con Claude en la app de escritorio; Claude hace el resto.

## Cómo se usa

1. **Puesta en marcha (una sola vez):** seguí [docs/PUESTA-EN-MARCHA-WINDOWS.md](docs/PUESTA-EN-MARCHA-WINDOWS.md).
2. **Armar tu perfil:** abrí esta carpeta en Claude Desktop (pestaña Code) y escribí *"empecemos"*. Claude te va a hacer preguntas sobre tu experiencia, una por vez, y arma tu perfil y tu CV general.
3. **Para cada aviso:** pegá el texto o el link del aviso y escribí *"armame el CV para este puesto"*. Claude te dice qué tan bien encaja, arma el CV en PDF y lo carga en Notion.
4. **Seguimiento:** mirá el tablero **Postulaciones** en Notion (también desde el celular). Ahí solamente movés tarjetas: a **Aprobado** si te querés postular, a **Descartado** si no te interesa, o a **Retirado** si ya no seguís. Cuando una empresa te escribe, la tarjeta se actualiza sola con un link al mail, y se marca **Requiere acción** si te piden algo.
5. **Antes de mandar algo:** Claude te pregunta en el chat y espera tu "sí". Nunca se postula ni responde mails sin eso.

## Qué cosas le podés pedir

- "Guía": te explica todo lo que hace el kit y qué funciones opcionales podés prender o apagar (búsqueda diaria, reporte por mail, ordenar la bandeja, remotos, contactos y más).
- "¿Qué hay nuevo en mis postulaciones?"
- "Agregá a mi perfil que terminé el curso X."
- "Prepará los aprobados."
- "Revisá mis mails."
- "Pasame el CV en inglés para este aviso."

## Reglas que Claude respeta siempre

- Nunca pone en el CV algo que no hiciste o no sabés.
- Nunca se postula ni manda mensajes sin que le digas que sí para ese aviso puntual.
- Nunca escribe tus contraseñas: cuando haga falta entrar a una cuenta, entrás vos.

## Si algo no te gusta o no funciona

Decíselo a Claude con tus palabras. Lo anota en `PEDIDOS.md` y le llega a quien mantiene el kit.

## Dónde queda cada cosa

- `profile/`: tu perfil completo y tus preferencias (no se envían a nadie).
- `cv/`: tu CV general.
- `postulaciones/`: un CV por cada aviso. Se guardan todas las versiones.
