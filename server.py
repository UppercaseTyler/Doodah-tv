from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import yaml

from providers.hls import HLSProvider
from providers.youtube import YouTubeProvider


OUTPUT_DIR = Path("output")

PROVIDERS = {
    "hls": HLSProvider(),
    "youtube": YouTubeProvider(),
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class DoodahRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).path

        if parsed_path == "/playlist.m3u":
            self.serve_file(OUTPUT_DIR / "playlist.m3u", "audio/x-mpegurl")
            return

        if parsed_path == "/guide.xml":
            self.serve_file(OUTPUT_DIR / "guide.xml", "application/xml")
            return

        if parsed_path.startswith("/channel/"):
            self.serve_channel(parsed_path)
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

    def serve_channel(self, path: str):
        channel_number = int(path.replace("/channel/", ""))

        config = load_config()

        for channel in config["channels"]:
            if channel["number"] == channel_number:
                provider = PROVIDERS[channel["source"]]
                stream = provider.resolve(channel)

                self.send_response(302)
                self.send_header("Location", stream.url)
                self.end_headers()
                return

        self.send_error(404, "Channel not found")


def start_server(server_config):
    bind = server_config["bind"]
    port = server_config["port"]

    server = ThreadingHTTPServer((bind, port), DoodahRequestHandler)

    print(f"Serving Doodah TV on {bind}:{port}")
    print("Available routes:")
    print("  /playlist.m3u")
    print("  /guide.xml")
    print("  /channel/<number>")

    server.serve_forever()
    