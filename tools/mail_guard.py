"""PreToolUse hook for Gmail send_message: skip the permission prompt only when he emails himself.

His request (PEDIDOS 2026-09-27): the daily report goes from his inbox to his own inbox without asking each day.
Any other recipient, or no configured address, falls back to the normal prompt. This hook never denies and
never widens anything else: it only removes the prompt in that one safe case.

His address comes from `mi_email` in profile/busqueda.toml.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

CONFIG = Path("profile/busqueda.toml")


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def decide(tool_input: dict, own_address: str | None) -> str | None:
    """'allow' if every recipient is his own address; None means: leave it to the normal prompt."""
    if not own_address:
        return None
    to = _as_list(tool_input.get("to"))
    everyone = to + _as_list(tool_input.get("cc")) + _as_list(tool_input.get("bcc"))
    if not to:
        return None
    me = own_address.strip().lower()
    return "allow" if all(r.strip().lower() == me for r in everyone) else None


def _own_address() -> str | None:
    try:
        return tomllib.loads(CONFIG.read_text(encoding="utf-8")).get("mi_email")
    except (OSError, tomllib.TOMLDecodeError):
        return None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if decide(event.get("tool_input") or {}, _own_address()) == "allow":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": "Mail a su propia casilla (reporte diario).",
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
