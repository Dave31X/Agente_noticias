"""Small HTTP API for the React chat interface.

Run with:
    ./venv/bin/python api_server.py
"""

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from config import NEWS_JSON, VECTORSTORE_DIR
from llm_provider import descripcion_llm


HOST = "127.0.0.1"
PORT = 8765


def _json_response(handler, status: int, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _sse_write(handler, event: str, data: dict):
    payload = json.dumps(data, ensure_ascii=False)
    handler.wfile.write(f"event: {event}\n".encode("utf-8"))
    handler.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
    handler.wfile.flush()


def _read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body or "{}")


class NewsAgentHandler(BaseHTTPRequestHandler):
    server_version = "NewsAgentAPI/1.0"

    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path != "/api/status":
            _json_response(self, 404, {"ok": False, "error": "Ruta no encontrada"})
            return

        total = 0
        latest = None
        if NEWS_JSON.exists():
            try:
                with open(NEWS_JSON, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, list):
                    total = len(data)
                    fechas = sorted(n.get("fecha", "") for n in data if n.get("fecha"))
                    latest = fechas[-1] if fechas else None
            except Exception:
                total = 0

        _json_response(
            self,
            200,
            {
                "ok": True,
                "llm": descripcion_llm(),
                "documents": total,
                "latest": latest,
                "vectorstore": VECTORSTORE_DIR.exists() and any(VECTORSTORE_DIR.iterdir()),
            },
        )

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/chat":
            _json_response(self, 404, {"ok": False, "error": "Ruta no encontrada"})
            return

        try:
            payload = _read_json(self)
            message = " ".join(str(payload.get("message", "")).split())
            allow_web = bool(payload.get("allowWeb", True))
            if not message:
                _json_response(self, 400, {"ok": False, "error": "Mensaje vacío"})
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.close_connection = True

            _sse_write(self, "status", {"state": "thinking"})
            from chat_core import stream_respuesta

            _sse_write(self, "status", {"state": "typing"})
            for token in stream_respuesta(message, permitir_web=allow_web):
                _sse_write(self, "token", {"token": token})
            _sse_write(self, "done", {"ok": True})
            self.wfile.flush()
        except BrokenPipeError:
            return
        except Exception as exc:
            try:
                _sse_write(
                    self,
                    "error",
                    {
                        "error": str(exc),
                        "detail": traceback.format_exc(limit=3),
                    },
                )
            except Exception:
                _json_response(self, 500, {"ok": False, "error": str(exc)})


def main():
    server = ThreadingHTTPServer((HOST, PORT), NewsAgentHandler)
    print(f"NewsAgent API escuchando en http://{HOST}:{PORT}")
    print("Endpoints: GET /api/status · POST /api/chat")
    server.serve_forever()


if __name__ == "__main__":
    main()
