"""Receptor de webhooks de laboratorio: registra en stdout cada notificación de Alertmanager."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 5001


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        for alert in payload.get("alerts", []):
            labels = alert.get("labels", {})
            print(
                f"[webhook{self.path}] status={alert.get('status')} "
                f"alertname={labels.get('alertname')} severity={labels.get('severity')} "
                f"instance={labels.get('instance')}",
                flush=True,
            )
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
