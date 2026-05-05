import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import config

HTML_PATH    = os.path.join(os.path.dirname(__file__), "templates", "index.html")
STATIC_DIR   = os.path.join(os.path.dirname(__file__), "static")


def get_db():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        auth_plugin="mysql_native_password",
    )


def fetch_history():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        f"SELECT `{config.COL_ID}`, `{config.COL_VALUE}` "
        f"FROM `{config.DB_TABLE}` "
        f"ORDER BY `{config.COL_ID}` ASC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/history":
            try:
                rows = fetch_history()
                self._send_json([
                    {"id": r[config.COL_ID], "value": r[config.COL_VALUE]}
                    for r in rows
                ])
            except mysql.connector.Error as e:
                print(f"[DB ERROR] {e}")
                self._send_json({"error": str(e)}, 503)

        elif self.path in ("/", "/index.html"):
            self._serve_file(HTML_PATH, "text/html; charset=utf-8")

        elif self.path.startswith("/static/"):
            filename = os.path.basename(self.path)
            filepath = os.path.join(STATIC_DIR, filename)
            if os.path.isfile(filepath):
                self._serve_file(filepath, "application/javascript")
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 5000), Handler)
    print("Running at http://localhost:5000")
    server.serve_forever()
