import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tools.notion_upload import MAX_BYTES, UploadError, upload


@pytest.fixture
def server():
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received["headers"] = dict(self.headers)
            received["body"] = self.rfile.read(int(self.headers["Content-Length"]))
            status = 400 if self.path == "/fail" else 200
            payload = {"message": "bad upload"} if status == 400 else {"id": "fu_1", "status": "uploaded", "markdown_source": "file://fu_1"}
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", received
    httpd.shutdown()


@pytest.fixture
def pdf(tmp_path):
    f = tmp_path / "cv banco.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    return f


def test_sends_the_file_as_multipart_field_named_file(server, pdf):
    url, received = server
    upload(pdf, url + "/send", {})
    assert received["headers"]["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="file"; filename="cv banco.pdf"' in received["body"]
    assert b"Content-Type: application/pdf" in received["body"]
    assert b"%PDF-1.4 fake" in received["body"]


def test_forwards_every_upload_header(server, pdf):
    url, received = server
    upload(pdf, url + "/send", {"Authorization": "Bearer short-lived", "Notion-Version": "2025-09-03"})
    assert received["headers"]["Authorization"] == "Bearer short-lived"
    assert received["headers"]["Notion-Version"] == "2025-09-03"


def test_returns_notions_response(server, pdf):
    url, _ = server
    assert upload(pdf, url + "/send", {})["markdown_source"] == "file://fu_1"


def test_error_response_raises_with_its_text(server, pdf):
    url, _ = server
    with pytest.raises(UploadError, match="bad upload"):
        upload(pdf, url + "/fail", {})


def test_files_over_the_limit_are_rejected_before_sending(tmp_path):
    big = tmp_path / "big.pdf"
    with open(big, "wb") as f:
        f.truncate(MAX_BYTES + 1)
    with pytest.raises(UploadError, match="20 MiB"):
        upload(big, "http://127.0.0.1:9/never", {})
