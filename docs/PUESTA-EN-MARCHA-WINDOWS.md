# Puesta en marcha en Windows

Se hace una sola vez. Vos instalás dos programas; del resto se encarga Claude.

## 1. Instalar

1. **Claude Desktop:** descargalo de https://claude.ai/download, instalalo y entrá con tu cuenta de Claude.
2. **Git para Windows:** descargalo de https://git-scm.com/download/win e instalalo con las opciones que vienen marcadas.

Word ya lo tenés: se usa para generar los PDF.

## 2. Que Claude baje el kit

Antes necesitás una cuenta de GitHub (gratis, en https://github.com).

1. En tu carpeta **Documentos**, creá una carpeta vacía llamada `busqueda-laboral`.
2. Abrí Claude Desktop, andá a la pestaña **Code** y elegí esa carpeta.
3. Pegá este mensaje tal cual:

   > Instalá con winget GitHub CLI y uv. Después iniciá sesión en GitHub con `gh auth login --web`, configurá git con `gh auth setup-git` y configurá mi nombre y mail en git (`git config --global user.name` y `user.email`, preguntámelos). Creá mi repositorio privado a partir de la plantilla con `gh repo create mi-busqueda-laboral --private --template joaquitodom/get-a-job-kit --clone`, entrá a esa carpeta y agregá la plantilla como remoto `upstream` (`git remote add upstream https://github.com/joaquitodom/get-a-job-kit.git`). Cuando termines, abrí el kit y revisá que todo funcione.

4. Claude te va a pedir permiso antes de instalar cada cosa. Cuando abra el navegador para GitHub, copiá el código que te muestra y aprobá. Tu contraseña la escribís vos, Claude no la ve.
5. Cuando Claude termine, abrí una **conversación nueva** en la pestaña Code, eligiendo la carpeta `mi-busqueda-laboral`. Hace falta para que Claude lea las instrucciones del kit que acaba de bajar.

Tu repositorio es privado y es tuyo: tu perfil y tus postulaciones se guardan ahí y no los ve nadie más. Cuando haya mejoras del kit, pedile a Claude *"traé las mejoras del kit"*.

## 3. Conectar Gmail y tu tablero

1. En Claude Desktop: **Settings**, **Connectors**. Agregá **Gmail** y entrá con tu cuenta de Google.
2. Elegí dónde seguir tus postulaciones (lo podés decidir después, en la entrevista):
   - **Notion:** creá una cuenta gratis en https://www.notion.so, agregá **Notion** en Connectors e instalá la app en el celular.
   - **Google Sheets:** instalá Google Drive para escritorio (https://www.google.com/drive/download/) y la app de Google Sheets en el celular. Claude te guía.

Claude solamente busca mails de las empresas a las que te postulaste, y te pregunta antes de mandar cualquier cosa.

## 4. Arrancar

En la pestaña Code, con la carpeta del kit abierta, escribí *"empecemos"* (o *"guía"* si primero querés ver todo lo que hace). Claude te va a:

1. Pedir tu CV actual y tu LinkedIn.
2. Hacerte preguntas sobre tu experiencia y lo que buscás.
3. Preguntarte en qué plataformas buscar trabajo y pedirte que entres a cada una con tu usuario en el navegador que trae Claude Desktop.
4. Ayudarte a definir qué puesto buscar, si no lo tenés claro, y mejorar tu CV.
5. Preguntarte si querés búsqueda automática: qué días, a qué hora, a qué distancia, qué sueldo y qué filtros.
6. Armar tu tablero en Notion o tu planilla en Google Sheets.
7. Ofrecerte el reporte por mail y las demás funciones opcionales.

## Qué plan de Claude necesitás

Un plan pago que incluya Claude Code (Pro o superior; precios en https://claude.ai/pricing). Con el plan gratis no funciona. La búsqueda diaria consume bastante: si llegás al límite de uso, pedile a Claude que la corra menos días o con menos términos.

## Si algo falla

Contale a Claude qué pasó con tus palabras, por ejemplo: *"me salió un error al generar el PDF"*. Si no se resuelve, lo anota en `PEDIDOS.md` para que se lo pases a quien te compartió el kit.
