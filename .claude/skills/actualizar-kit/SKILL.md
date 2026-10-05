---
name: actualizar-kit
description: Brings the latest version of the kit (skills, tools, docs) from the template it was created from, without touching their data. Use when they say "traé las mejoras del kit", "actualizá el kit", "hay versión nueva?", "update the kit".
---

# actualizar-kit

Their repo was created from a template repo. Kit improvements land there; their data (`profile/`, `cv/`, `postulaciones/`, `PEDIDOS.md`) never travels in either direction.

## Steps

1. `git remote -v`. If there is no `upstream` remote:
   - If `origin` is the kit itself (they work directly on the maintainer's repo), there is nothing to do: the sync hook already brings changes.
   - Otherwise ask them for the template's address (whoever shared the kit has it) and add it: `git remote add upstream <url>`.
2. `git fetch upstream`. List what changed in kit paths: `git diff --stat HEAD upstream/main -- CLAUDE.md README.md .claude tools tests docs evaluacion pyproject.toml uv.lock .github .gitignore .python-version`. If nothing, say so and stop.
3. Tell them in 3 lines what is new (read the commit messages: `git log --oneline HEAD..upstream/main`) and ask "¿Lo traigo?".
4. After their "sí": `git checkout upstream/main -- <those paths>` (only paths that exist upstream), then `uv sync` and `uv run pytest -q`. If tests fail, undo with `git checkout HEAD -- <those paths>` and tell them in one line.
5. Commit ("kit: actualizado desde la plantilla") and push. Never merge their data folders and never force-push.
6. If the update brought new settings (check `docs/pedidos-resueltos.md` and the `guia` skill), offer the new optional functions in one line each.
7. Tell them to open a **new conversation** so Claude reads the updated instructions.
