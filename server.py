from fileinput import filename
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from providers.ozolio import OzolioProvider
import mimetypes
import time

import yaml

from providers.hls import HLSProvider
from providers.youtube import YouTubeProvider


OUTPUT_DIR = Path("output")

LOGO_DIR = Path("assets/logos")

OFFLINE_DIR = Path("assets/offline")

PROVIDERS = {
    "hls": HLSProvider(),
    "youtube": YouTubeProvider(),
    "ozolio": OzolioProvider(),
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class DoodahRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).path
        print(f"GET {self.path}")

        if parsed_path == "/playlist.m3u":
            self.serve_file(OUTPUT_DIR / "playlist.m3u", "audio/x-mpegurl")
            return

        if parsed_path == "/guide.xml":
            self.serve_file(OUTPUT_DIR / "guide.xml", "application/xml")
            return

        if parsed_path.startswith("/channel/"):
            self.serve_channel(parsed_path)
            return
        
        if parsed_path.startswith("/logos/"):
            filename = parsed_path.replace("/logos/", "")
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            self.serve_file(LOGO_DIR / filename, content_type)
            return
        
        if parsed_path.startswith("/offline/media_") and parsed_path.endswith(".ts"):
            segment_number = int(parsed_path.replace("/offline/media_", "").replace(".ts", ""))
            real_file = f"playlist{segment_number % 30}.ts"
            self.serve_file(OFFLINE_DIR / real_file, "video/mp2t")
            return
        
        if parsed_path == "/offline/playlist.m3u8":
            self.serve_offline_playlist()
            return

        if parsed_path.startswith("/offline/"):
            filename = parsed_path.replace("/offline/", "")
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            self.serve_file(OFFLINE_DIR / filename, content_type)
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
                try:
                    provider = PROVIDERS[channel["source"]]
                    stream = provider.resolve(channel)

                    self.send_response(302)
                    self.send_header("Location", stream.url)
                    self.end_headers()
                    return

                except Exception as error:
                    print(f"Channel {channel_number} unavailable: {error}")

                    self.send_response(503)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Channel temporarily unavailable")
                    return

        self.send_error(404, "Channel not found")

    def serve_offline_playlist(self):
        segment_duration = 2
        sequence = int(time.time() // segment_duration)

        lines = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{segment_duration}",
            f"#EXT-X-MEDIA-SEQUENCE:{sequence}",
        ]

        for i in range(6):
            fake_sequence = sequence + i
            lines.extend([
                f"#EXTINF:{segment_duration}.0,",
                f"/offline/media_{fake_sequence}.ts",
            ])

        lines.append("")
        playlist = "\n".join(lines)
        content = playlist.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.apple.mpegurl")
        self.send_header("Cache-Control", "no-cache")
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
    print("  /channel/<number>")

    server.serve_forever()
    