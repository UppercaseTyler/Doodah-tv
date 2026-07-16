from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import atexit
import mimetypes

import yaml

from offline_manager import OfflineManager
from providers.hls import HLSProvider
from providers.ozolio import OzolioProvider
from providers.youtube import YouTubeProvider


OUTPUT_DIR = Path("output")
LOGO_DIR = Path("assets/logos")
OFFLINE_OUTPUT_DIR = Path("output/offline")


PROVIDERS = {
    "hls": HLSProvider(),
    "youtube": YouTubeProvider(),
    "ozolio": OzolioProvider(),
}

OFFLINE_MANAGER = OfflineManager()
atexit.register(OFFLINE_MANAGER.stop_all)


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"{timestamp} {message}", flush=True)


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


class DoodahRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).path
        log(f"GET {self.path}")

        if parsed_path == "/playlist.m3u":
            self.serve_file(
                OUTPUT_DIR / "playlist.m3u",
                "audio/x-mpegurl",
            )
            return

        if parsed_path == "/guide.xml":
            self.serve_file(
                OUTPUT_DIR / "guide.xml",
                "application/xml",
            )
            return

        if parsed_path.startswith("/channel/"):
            self.serve_channel(parsed_path)
            return

        if parsed_path.startswith("/logos/"):
            filename = parsed_path.replace("/logos/", "")
            content_type = (
                mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )
            self.serve_file(
                LOGO_DIR / filename,
                content_type,
            )
            return
        
        if parsed_path.startswith("/offline/"):
            self.serve_offline_file(parsed_path)
            return

    

        self.send_error(404, "Not Found")

    def serve_file(
        self,
        file_path: Path,
        content_type: str,
    ) -> None:
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_offline_file(self, path: str) -> None:
        relative_path = path.removeprefix("/offline/")
        file_path = OFFLINE_OUTPUT_DIR / relative_path

        try:
            file_path.resolve().relative_to(
                OFFLINE_OUTPUT_DIR.resolve()
            )
        except ValueError:
            self.send_error(403, "Invalid offline path")
            return

        content_type = (
            mimetypes.guess_type(file_path.name)[0]
            or "application/octet-stream"
        )

        if file_path.suffix == ".m3u8":
            content_type = "application/vnd.apple.mpegurl"

        self.serve_file(
            file_path,
            content_type,
        )

    def serve_channel(self, path: str) -> None:
        channel_number = int(
            path.replace("/channel/", "")
        )

        config = load_config()

        for channel in config["channels"]:
            if channel["number"] != channel_number:
                continue

            try:
                provider = PROVIDERS[channel["source"]]
                stream = provider.resolve(channel)

                log(
                    f"channel={channel_number} "
                    f"name={channel.get('name', 'unknown')} "
                    f"source={channel['source']} "
                    f"resolved={stream.url}"
                )

                self.send_response(302)
                self.send_header("Location", stream.url)
                self.end_headers()
                return

            except Exception as error:
                log(
                    f"channel={channel_number} "
                    f"name={channel.get('name', 'unknown')} "
                    f"unavailable "
                    f"{type(error).__name__}: {error}"
                )

                try:
                    playlist_path = OFFLINE_MANAGER.get_or_start(
                        channel_number
                    )

                    fallback_url = (
                        f"http://{config['server']['host']}:"
                        f"{config['server']['port']}"
                        f"/offline/{channel_number}/"
                        f"{playlist_path.name}"
                    )

                    log(
                        f"channel={channel_number} "
                        f"fallback={fallback_url}"
                    )

                    self.send_response(302)
                    self.send_header(
                        "Location",
                        fallback_url,
                    )
                    self.end_headers()
                    return

                except Exception as fallback_error:
                    log(
                        f"channel={channel_number} "
                        f"fallback_failed "
                        f"{type(fallback_error).__name__}: "
                        f"{fallback_error}"
                    )

                    self.send_response(503)
                    self.send_header(
                        "Content-Type",
                        "text/plain",
                    )
                    self.end_headers()
                    self.wfile.write(
                        b"Channel and fallback unavailable"
                    )
                    return

        log(
            f"channel={channel_number} "
            "not_found"
        )
        self.send_error(404, "Channel not found")


def start_server(server_config: dict) -> None:
    bind = server_config["bind"]
    port = server_config["port"]

    server = ThreadingHTTPServer(
        (bind, port),
        DoodahRequestHandler,
    )

    log(f"Serving Doodah TV on {bind}:{port}")
    log("Available routes:")
    log("  /playlist.m3u")
    log("  /guide.xml")
    log("  /channel/<number>")
    log("  /offline/<channel>/<filename>")

    server.serve_forever()