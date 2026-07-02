from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path



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

def start_server(server_config):
    bind = server_config["bind"]
    port = server_config["port"]

    server = ThreadingHTTPServer((bind, port), DoodahRequestHandler)

    print(f"Serving Doodah TV on {bind}:{port}")
    print("Available routes:")
    print("  /playlist.m3u")
    print("  /guide.xml")

    server.serve_forever()

    
    