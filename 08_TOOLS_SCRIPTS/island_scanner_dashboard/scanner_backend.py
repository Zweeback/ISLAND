from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PORT = int(os.environ.get("ISLAND_DASHBOARD_PORT", "8000"))
HOST = os.environ.get("ISLAND_DASHBOARD_HOST", "127.0.0.1")
GITHUB_OWNER = os.environ.get("ISLAND_GITHUB_OWNER", "Zweeback")
MAX_DEPTH = int(os.environ.get("ISLAND_SCAN_MAX_DEPTH", "3"))
MAX_FILES_PER_SOURCE = int(os.environ.get("ISLAND_SCAN_MAX_FILES", "2000"))

BASE_DIR = Path(__file__).resolve().parent
INGEST_DIR = BASE_DIR / "ingest"

SCAN_RESULTS: dict[str, dict[str, Any]] = {
    "local": {"status": "idle", "files": [], "last_run": None},
    "gdrive": {"status": "idle", "files": [], "last_run": None},
    "github": {"status": "idle", "files": [], "last_run": None},
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".ssh",
    ".gemini",
    ".continue",
    "AppData",
    "Local",
    "Roaming",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "Program Files",
    "Program Files (x86)",
    "Windows",
    "System32",
}
EXCLUDED_FILE_REGEX = re.compile(
    r"(\.env|password|secret|id_rsa|token|cookie)", re.IGNORECASE
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_. -]+", "", value).strip() or "template"
    return cleaned[:80]


def within(base: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


class FileScanner:
    @staticmethod
    def _walk(root_path: Path, label: str, max_depth: int) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if not root_path.exists() or not root_path.is_dir():
            return found

        for root, dirs, files in os.walk(root_path):
            root_obj = Path(root)
            if not within(root_path, root_obj):
                dirs.clear()
                continue

            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
            depth = len(root_obj.relative_to(root_path).parts)
            if depth > max_depth:
                dirs.clear()
                continue

            for filename in files:
                if len(found) >= MAX_FILES_PER_SOURCE:
                    return found
                if EXCLUDED_FILE_REGEX.search(filename):
                    continue

                file_path = root_obj / filename
                if not within(root_path, file_path):
                    continue
                try:
                    stat = file_path.stat()
                except OSError:
                    continue

                found.append(
                    {
                        "name": filename,
                        "path": file_path.as_posix(),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(
                            stat.st_mtime, timezone.utc
                        ).isoformat(),
                        "type": file_path.suffix.lower() or "file",
                        "source": label,
                    }
                )
        return found

    @staticmethod
    def scan_local() -> list[dict[str, Any]]:
        roots = [
            Path.home() / "Desktop",
            Path.home() / "Downloads",
            Path.home() / "Documents" / "Codex",
        ]
        results: list[dict[str, Any]] = []
        for root in roots:
            results.extend(FileScanner._walk(root, "local", MAX_DEPTH))
            if len(results) >= MAX_FILES_PER_SOURCE:
                break
        return results[:MAX_FILES_PER_SOURCE]

    @staticmethod
    def scan_gdrive() -> list[dict[str, Any]]:
        roots = [
            Path("G:/Meine Ablage"),
            Path("G:/My Drive"),
            Path.home() / "Google Drive",
        ]
        results: list[dict[str, Any]] = []
        for root in roots:
            results.extend(FileScanner._walk(root, "google-drive-local-mount", 2))
            if len(results) >= MAX_FILES_PER_SOURCE:
                break
        return results[:MAX_FILES_PER_SOURCE]

    @staticmethod
    def scan_github() -> list[dict[str, Any]]:
        request = urllib.request.Request(
            f"https://api.github.com/users/{urllib.parse.quote(GITHUB_OWNER)}/repos?per_page=100",
            headers={"User-Agent": "ISLAND-Scanner-Dashboard"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            repos = json.loads(response.read().decode("utf-8"))

        results: list[dict[str, Any]] = []
        for repo in repos[:100]:
            results.append(
                {
                    "name": repo.get("name", "unknown"),
                    "path": repo.get("html_url", ""),
                    "size_bytes": int(repo.get("size") or 0) * 1024,
                    "modified": repo.get("updated_at") or "",
                    "type": "repository",
                    "source": "github-public-api",
                }
            )
        return results


class TemplateGenerator:
    @staticmethod
    def generate(template_type: str, name: str) -> tuple[str, str, bytes]:
        name = safe_name(name)
        escaped = html.escape(name)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        slug = re.sub(r"\s+", "_", name)

        if template_type == "document":
            content = f"# Project Brief: {escaped}\n\nCreated: {now}\n\n## Goal\n\n## Scope\n\n## Tasks\n- [ ] Define next step\n- [ ] Verify output\n\n## Notes\n"
            return f"{slug}.md", "text/markdown; charset=utf-8", content.encode("utf-8")

        if template_type == "spreadsheet":
            content = "ID,Task,Owner,Status,Priority\n1,Define next step,Jules,planned,high\n2,Verify output,Codex,planned,medium\n"
            return (
                f"{slug}_tracker.csv",
                "text/csv; charset=utf-8",
                content.encode("utf-8"),
            )

        if template_type in {"pdf", "presentation"}:
            title = (
                "Autonomous Scan Report"
                if template_type == "pdf"
                else "ISLAND Autonomy Slides"
            )
            body = f"""<!doctype html>
<html lang=\"en\">
<head><meta charset=\"utf-8\"><title>{title}: {escaped}</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:40px;color:#1f2937;line-height:1.5}}
main{{max-width:900px;margin:auto}} h1{{color:#0f766e}} section{{border-top:1px solid #d1d5db;margin-top:24px;padding-top:16px}}
@media print{{body{{margin:18mm}}}}
</style></head>
<body><main><h1>{title}</h1><p><strong>Name:</strong> {escaped}<br><strong>Created:</strong> {now}</p>
<section><h2>Purpose</h2><p>Starter artifact generated by the ISLAND Scanner Dashboard.</p></section>
<section><h2>Next Steps</h2><ol><li>Review content.</li><li>Connect to the correct ISLAND lane.</li><li>Record final status.</li></ol></section>
</main></body></html>
"""
            suffix = "report.html" if template_type == "pdf" else "slides.html"
            return f"{slug}_{suffix}", "text/html; charset=utf-8", body.encode("utf-8")

        content = f"Template: {escaped}\nCreated: {now}\n"
        return f"{slug}.txt", "text/plain; charset=utf-8", content.encode("utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(
            f"{self.client_address[0]} - - [{self.log_date_time_string()}] {fmt % args}\n"
        )

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/api/status":
            self._json(200, SCAN_RESULTS)
            return

        route = self.path.split("?", 1)[0]
        if route == "/":
            route = "/index.html"
        candidate = (BASE_DIR / route.lstrip("/")).resolve()
        if not within(BASE_DIR, candidate) or not candidate.is_file():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        content = candidate.read_bytes()
        mime, _ = mimetypes.guess_type(str(candidate))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if self.path == "/api/scan":
            self._handle_scan()
            return
        if self.path == "/api/template":
            self._handle_template()
            return
        self._json(404, {"error": "not_found"})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 65536:
            raise ValueError("payload_too_large")
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def _handle_scan(self) -> None:
        try:
            source = self._read_json().get("source")
            if source not in SCAN_RESULTS:
                raise ValueError("invalid_source")
            SCAN_RESULTS[source].update({"status": "scanning", "last_run": utc_now()})
            if source == "local":
                files = FileScanner.scan_local()
            elif source == "gdrive":
                files = FileScanner.scan_gdrive()
            else:
                files = FileScanner.scan_github()
            SCAN_RESULTS[source].update(
                {"status": "success", "files": files, "last_run": utc_now()}
            )
            INGEST_DIR.mkdir(parents=True, exist_ok=True)
            (INGEST_DIR / f"scan_{source}_index.json").write_text(
                json.dumps(SCAN_RESULTS[source], indent=2), encoding="utf-8"
            )
            self._json(
                200, {"status": "success", "source": source, "file_count": len(files)}
            )
        except Exception as exc:  # keep API resilient for dashboard use
            if "source" in locals() and source in SCAN_RESULTS:
                SCAN_RESULTS[source].update(
                    {"status": "error", "error": str(exc), "last_run": utc_now()}
                )
            self._json(400, {"status": "error", "error": str(exc)})

    def _handle_template(self) -> None:
        try:
            data = self._read_json()
            filename, content_type, content = TemplateGenerator.generate(
                str(data.get("type", "document")), str(data.get("name", "New Template"))
            )
            INGEST_DIR.mkdir(parents=True, exist_ok=True)
            (INGEST_DIR / filename).write_bytes(content)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self._json(400, {"status": "error", "error": str(exc)})


def main() -> None:
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"ISLAND Scanner Dashboard running at http://{HOST}:{PORT}/", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping dashboard", file=sys.stderr)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
