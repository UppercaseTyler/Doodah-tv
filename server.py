from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8090
OUTPUT_DIR = Path("output")


class DoodahRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/playlist.m3u":
            self.serve_file(OUTPUT_DIR / "playlist.m3u", "audio/x-mpegurl")
            return

        if self.path == "/guide.xml":
            self.serve_file(OUTPUT_DIR / "guide.xml", "application/xml")
            return

        self.send_error(404, "Not Found")

    def serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def start_server():
    server = ThreadingHTTPServer((HOST, PORT), DoodahRequestHandler)

    print(f"Serving Doodah TV at http://{HOST}:{PORT}")
    print("Available routes:")
    print("  /playlist.m3u")
    print("  /guide.xml")

    server.serve_forever()