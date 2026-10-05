"""Upload a local file to Notion after `create_file_upload` (Notion connector) returned an upload URL.

  uv run python -m tools.notion_upload <file> < upload.json

`upload.json` is the connector's answer: {"upload_url": "...", "upload_headers": {...}}. Prints Notion's JSON
response (it contains `markdown_source`, used to attach the file to a page).

Why not curl: on Windows, curl uses the system TLS library, which fails when it cannot reach the certificate
revocation servers (error 35). The workaround `--ssl-no-revoke` turns that security check off; Python's TLS
does not depend on it, so the kit uploads with Python instead.
"""

from __future__ import annotations

import json
import mimetypes
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

MAX_BYTES = 20 * 1024 * 1024  # single-part upload limit of the Notion connector


class UploadError(RuntimeError):
    pass


def _multipart(path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + path.read_bytes() + tail, f"multipart/form-data; boundary={boundary}"


def upload(
    path: Path, upload_url: str, upload_headers: dict[str, str], timeout: int = 60
) -> dict:
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise UploadError(
            f"{path.name} pesa {size / 1024 / 1024:.1f} MiB; Notion acepta hasta 20 MiB por archivo."
        )
    body, content_type = _multipart(path)
    request = urllib.request.Request(upload_url, data=body, method="POST")
    for key, value in upload_headers.items():
        request.add_header(key, value)
    request.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise UploadError(f"Notion rechazó la subida ({exc.code}): {detail}") from exc


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 1
    spec = json.loads(sys.stdin.read())
    try:
        result = upload(
            Path(args[0]), spec["upload_url"], spec.get("upload_headers", {})
        )
    except UploadError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
