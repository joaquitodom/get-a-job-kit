# Formato de CV en markdown

`tools/render_cv.py` entiende solamente este formato. Claude escribe los CVs así; no hace falta tocarlos a mano.

```
# Nombre Apellido
Frase corta de perfil · Área · Herramienta clave
Ciudad, País | [mail@ejemplo.com](mailto:mail@ejemplo.com) | +54 9 11 0000-0000 | [LinkedIn](https://linkedin.com/in/usuario)

## Resumen
Un párrafo de tres o cuatro líneas.

## Experiencia
### Empresa | Mes Año a Mes Año
_Puesto | Ciudad_
- Verbo en pasado + qué hizo + impacto, 15 a 25 palabras.

## Proyectos
### Nombre del proyecto · Herramientas usadas
_Contexto en una línea (opcional)._
- Qué hizo y qué resultado tuvo.

## Habilidades
**Herramientas:** Excel avanzado, Power BI, SQL
**Idiomas:** Inglés B2
```

Reglas:

- `# ` es el nombre. La primera línea siguiente es la frase de perfil y la segunda son los datos de contacto separados por ` | `. Los links van como `[texto](url)`.
- `## ` abre una sección. El título se muestra centrado y subrayado.
- `### Título | Fechas` es un puesto o estudio: las fechas van alineadas a la derecha. La línea siguiente entre guiones bajos es `_Puesto | Lugar_`.
- `### Título · Herramientas` (con punto medio y sin `|`) es un proyecto. La línea siguiente entre guiones bajos es el contexto.
- `- ` es un punto de la lista.
- `**Etiqueta:** texto` es una línea de habilidades.
- Sin tablas, sin imágenes, sin rayas largas: el generador se niega a generar si encuentra una.
- Dentro de cada sección, lo más reciente primero.
- Títulos y tesis con el nombre completo, sin abreviaturas.
- Objetivo: dos páginas como máximo.
