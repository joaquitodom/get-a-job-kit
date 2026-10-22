"""Keep the shared repo in sync. Run by Claude Code hooks (see .claude/settings.json), never by hand.

  uv run python -m tools.sync pull   # on every message: bring in kit changes
  uv run python -m tools.sync push   # when Claude finishes a turn: save their data and push

Both always exit 0 so a sync problem never blocks the conversation; problems are reported as text.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DATA_PATHS = ["profile", "cv", "postulaciones", "PEDIDOS.md"]
TIMEOUT = 20


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT,
    )


def _is_data(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") for p in DATA_PATHS)


AUTH = (
    "Sincronización: GitHub rechazó el acceso (la sesión venció o nunca se inició), así que sus avances no se subieron. "
    "Explicale en una frase, pedile permiso y corré `gh auth login --web` y después `gh auth setup-git`; él aprueba en el navegador."
)
IDENTITY = (
    "Sincronización: git no tiene nombre y mail configurados, así que no pude guardar sus avances. "
    "Preguntale su nombre y el mail de su cuenta de GitHub y configuralos con "
    "`git config --global user.name` y `git config --global user.email`."
)
ACTIONABLE = (AUTH, IDENTITY)


def classify_git_error(stderr: str) -> str:
    text = stderr.lower()
    if "author identity unknown" in text or "please tell me who you are" in text:
        return "identity"
    if any(m in text for m in ("authentication failed", "could not read username", "permission to", "403")):
        return "auth"
    return "offline"


def _blocking_files(stderr: str) -> list[str]:
    """Files named by git's 'untracked working tree files would be overwritten' error."""
    if "would be overwritten" not in stderr:
        return []
    lines = stderr.splitlines()
    start = next(i for i, line in enumerate(lines) if "would be overwritten" in line) + 1
    return [line.strip() for line in lines[start:] if line.startswith(("\t", "    "))]


def _explain(stderr: str) -> str:
    if files := _blocking_files(stderr):
        return (
            "Sincronización: no pude traer cambios porque estos archivos suyos, sin guardar en git, "
            "tienen el mismo nombre que archivos nuevos del repositorio: " + ", ".join(files) + ". "
            "No borres nada: renombrá los suyos (por ejemplo agregando -mio al nombre) y se sincroniza en el próximo mensaje. "
            "Si no es obvio qué hacer, anotalo en PEDIDOS.md."
        )
    return {"identity": IDENTITY, "auth": AUTH}.get(classify_git_error(stderr), "")


CONFLICT = (
    "Sincronización: hubo un conflicto al traer cambios del repositorio y no se aplicó nada. "
    "Sus archivos quedaron como estaban. Avisale en una frase y anotalo en PEDIDOS.md."
)


def _pull(repo: Path) -> tuple[bool, str]:
    """Returns (conflict, message)."""
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    try:
        result = _git(repo, "pull", "--rebase", "--autostash", "-q")
    except subprocess.TimeoutExpired:
        return False, ""
    if result.returncode != 0:
        if (repo / ".git" / "rebase-merge").exists() or (
            repo / ".git" / "rebase-apply"
        ).exists():
            _git(repo, "rebase", "--abort")
            return True, CONFLICT
        return False, _explain(result.stderr)  # offline stays silent: the next message retries
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    if before == after:
        return False, ""
    changed = _git(repo, "diff", "--name-only", before, after).stdout.split()
    kit = [f for f in changed if not _is_data(f)]
    if not kit:
        return False, ""
    return False, (
        "Sincronización: se actualizaron archivos del kit: "
        + ", ".join(kit)
        + ". Volvé a leer los que afecten lo que estás haciendo (CLAUDE.md y skills) antes de seguir."
    )


def pull(repo: Path) -> str:
    return _pull(repo)[1]


def push(repo: Path) -> str:
    existing = [p for p in DATA_PATHS if (repo / p).exists()]
    if existing:
        _git(repo, "add", "-A", "--", *existing)
        if _git(repo, "diff", "--cached", "--quiet").returncode != 0:
            commit = _git(repo, "commit", "-q", "-m", "chore: guardar avances")
            if commit.returncode != 0:
                return _explain(commit.stderr) or "No pude guardar los cambios en git: " + commit.stderr.strip()
    ahead = _git(repo, "rev-list", "--count", "@{u}..HEAD")
    if ahead.returncode != 0 or ahead.stdout.strip() == "0":
        return ""
    try:
        result = _git(repo, "push", "-q")
        if result.returncode != 0:
            if classify_git_error(result.stderr) != "offline":
                return _explain(result.stderr)
            conflict, message = _pull(repo)
            if conflict or message in ACTIONABLE:
                return message
            result = _git(repo, "push", "-q")
            if result.returncode != 0:
                return _explain(result.stderr)
    except subprocess.TimeoutExpired:
        return ""
    return ""  # pushed, or offline: the next turn retries


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip() or ".")
    if args[:1] == ["pull"]:
        message = pull(repo)
        if message:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": message,
                        }
                    }
                )
            )
    elif args[:1] == ["push"]:
        message = push(repo)
        try:
            already_continued = json.loads(sys.stdin.read() or "{}").get("stop_hook_active", False)
        except ValueError:
            already_continued = False
        if message in ACTIONABLE and not already_continued:
            # Make Claude act on it (ask them, run the fix) instead of only showing them a notice.
            print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
        elif message:
            print(json.dumps({"systemMessage": message}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
