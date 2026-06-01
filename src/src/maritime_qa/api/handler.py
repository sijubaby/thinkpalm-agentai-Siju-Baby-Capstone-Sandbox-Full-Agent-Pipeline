"""HTTP handler: REST API + optional web UI."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from maritime_qa.api.service import PROJECT_ROOT, execute_pipeline, get_run_for_ui, list_runs

STATIC = Path(__file__).resolve().parents[1] / "ui" / "static"

SAMPLE_FILES = {
    "crew-cert": PROJECT_ROOT / "samples" / "description-crew-cert.txt",
    "ais": PROJECT_ROOT / "samples" / "description-ais.txt",
    "port-workflow": PROJECT_ROOT / "samples" / "description-port-workflow.txt",
}


def _load_sample(key: str) -> str:
    path = SAMPLE_FILES.get(key)
    return path.read_text(encoding="utf-8") if path and path.is_file() else ""


def _check_api_key(handler: BaseHTTPRequestHandler) -> bool:
    required = os.getenv("MARITIME_QA_API_KEY", "").strip()
    if not required:
        return True
    provided = handler.headers.get("X-API-Key", "")
    return provided == required


API_VERSION = "1.0.0"
DEFAULT_PORT = 8770


class MaritimeHTTPHandler(BaseHTTPRequestHandler):
    serve_ui: bool = True

    def log_message(self, format: str, *args) -> None:
        pass

    def _path(self) -> str:
        p = urlparse(self.path).path.rstrip("/")
        return p or "/"

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Return JSON errors for /api/* instead of HTML (fixes UI JSON parse errors)."""
        path = self._path()
        if path.startswith("/api"):
            detail = message or explain or "Error"
            self._json(code, {"error": detail, "path": path})
            return
        super().send_error(code, message, explain)

    def _send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self) -> None:
        path = self._path()

        if self.serve_ui and path in ("/", "/index.html"):
            return self._serve_file(STATIC / "index.html", "text/html; charset=utf-8")

        if path == "/api/v1":
            return self._json(
                200,
                {
                    "service": "maritime-qa-agent",
                    "version": API_VERSION,
                    "endpoints": {
                        "health": "GET /api/v1/health",
                        "runs": "GET /api/v1/runs",
                        "run_detail": "GET /api/v1/runs/{run_id}",
                        "run": "POST /api/v1/pipeline/run",
                    },
                },
            )

        if path == "/api/v1/pipeline/run":
            return self._json(
                405,
                {
                    "error": "Use POST (not GET) for /api/v1/pipeline/run",
                    "hint": "You are on the correct Maritime QA server if you see this JSON.",
                },
            )

        if path == "/api/v1/health":
            from maritime_qa.api.llm_config import llm_status

            return self._json(
                200,
                {
                    "status": "ok",
                    "service": "maritime-qa-agent",
                    **llm_status(),
                },
            )

        if path == "/api/v1/runs":
            limit = 50
            qs = parse_qs(urlparse(self.path).query)
            if qs.get("limit"):
                try:
                    limit = min(100, max(1, int(qs["limit"][0])))
                except ValueError:
                    pass
            try:
                return self._json(200, {"runs": list_runs(limit=limit)})
            except Exception as exc:
                return self._json(500, {"error": f"Failed to list runs: {exc}"})

        if path == "/api/v1/openapi":
            return self._serve_file(PROJECT_ROOT / "docs" / "openapi.json", "application/json")

        run_match = re.match(r"^/api/v1/runs/([^/]+)$", path)
        if run_match:
            if not _check_api_key(self):
                return self._json(401, {"error": "Invalid or missing X-API-Key"})
            try:
                return self._json(200, get_run_for_ui(run_match.group(1)))
            except FileNotFoundError as exc:
                return self._json(404, {"error": str(exc)})

        artifact_match = re.match(r"^/api/v1/runs/([^/]+)/artifacts/(.+)$", path)
        if artifact_match:
            run_id, name = artifact_match.group(1), artifact_match.group(2)
            run_dir = PROJECT_ROOT / "runs" / run_id
            out_dir = PROJECT_ROOT / "out" / "api-latest"
            candidates = {
                "report.html": ["coverage-report.html"],
                "report.md": ["coverage-report.md"],
                "gherkin": ["generated.feature"],
                "playwright": ["test_generated_maritime.py"],
            }
            for fname in candidates.get(name, [name]):
                for base in (out_dir, run_dir):
                    p = base / fname
                    if p.is_file():
                        return self._serve_file(p)
            return self.send_error(404, "Artifact not found")

        # Legacy UI routes
        if path in ("/api/samples", "/api/v1/samples"):
            items = [
                {"id": k, "label": k.replace("-", " ").title(), "description": _load_sample(k)}
                for k in ("crew-cert", "ais", "port-workflow")
            ]
            return self._json(200, {"samples": items})

        self.send_error(404)

    def do_POST(self) -> None:
        path = self._path()

        if path in ("/api/v1/pipeline/run", "/api/run"):
            if not _check_api_key(self):
                return self._json(401, {"error": "Invalid or missing X-API-Key"})

            body = self._read_json_body()
            if body is None:
                return self._json(400, {"error": "Invalid JSON body"})

            description = (body.get("description") or "").strip()
            if not description:
                return self._json(400, {"error": "description is required"})

            from maritime_qa.api.llm_config import is_llm_available

            use_llm = body.get("use_llm")
            if use_llm is None:
                use_llm = is_llm_available()
            else:
                use_llm = bool(use_llm)

            try:
                result = execute_pipeline(
                    description,
                    domain=body.get("domain"),
                    run_playwright=bool(body.get("run_playwright", False)),
                    use_llm=use_llm,
                    llm_provider=body.get("llm_provider") or "groq",
                    output_subdir=body.get("output_subdir", "api-latest"),
                )
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            except Exception as exc:
                return self._json(500, {"error": str(exc)})

            # UI compatibility: top-level artifact fields
            arts = result.pop("artifacts", {})
            ui_payload = {
                **result,
                "gherkin": arts.get("gherkin", ""),
                "playwright": arts.get("playwright", ""),
                "report_html": arts.get("report_html", ""),
            }
            return self._json(200, ui_payload)

        self.send_error(404)

    def _serve_file(self, file_path: Path, content_type: str | None = None) -> None:
        if not file_path.is_file():
            self.send_error(404)
            return
        data = file_path.read_bytes()
        ctype = content_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self._send_cors()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_server(
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
    serve_ui: bool = True,
) -> None:
    from maritime_qa.api.llm_config import load_env_file, llm_status

    load_env_file()
    status = llm_status()
    if status["llm_configured"]:
        print(f"  LLM: {status['llm_provider']} / {status['llm_model']}")
    else:
        print("  LLM: not configured (set GROQ_API_KEY in .env for dynamic results)")
    handler = type(
        "ConfiguredHandler",
        (MaritimeHTTPHandler,),
        {"serve_ui": serve_ui},
    )
    server = ThreadingHTTPServer((host, port), handler)
    mode = "UI + API" if serve_ui else "API only"
    url = f"http://{host}:{port}/"
    print(f"Maritime QA ({mode}) → {url}")
    print(f"  REST API: {url}api/v1/health")
    print("Press Ctrl+C to stop.")
    if open_browser and serve_ui:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    start_server()
