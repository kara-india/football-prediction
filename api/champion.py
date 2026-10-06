from http.server import BaseHTTPRequestHandler
import json
from python.champion_service import decide

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"model": "CHAMPION", "version": "champion-python-v3.0", "status": "ready"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            body = json.dumps(decide(payload)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({
                "model": "CHAMPION",
                "version": "champion-python-v3.0",
                "action": "NO_BET",
                "reason": "CHAMPION_ENGINE_FAILURE",
                "error": str(exc),
            }).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
