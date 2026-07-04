import re
from urllib.parse import parse_qs, urlparse

import requests

from providers.base import Provider, ResolvedStream


class OzolioProvider(Provider):
    DEFAULT_SERVER = "https://relay.ozolio.com"

    def resolve(self, channel: dict) -> ResolvedStream:
        url = channel["url"]
        server = channel.get("server", self.DEFAULT_SERVER)

        object_id = channel.get("object") or self.resolve_object_id(url)

        init_data = self.initialize_session(server, object_id, url)
        session_id = init_data["session"]["id"]

        output = self.find_m3u8_output(init_data["outputs"])
        open_data = self.open_output(server, session_id, output["id"])

        stream_url = self.extract_stream_url(open_data)

        return ResolvedStream(
            name=channel["name"],
            number=channel["number"],
            enabled=channel["enabled"],
            source=channel["source"],
            url=stream_url,
            guide_title=channel.get("guide_title", channel["name"]),
            guide_description=channel.get(
                "guide_description",
                f"Live stream from Doodah TV: {channel['name']}",
            ),
        )

    def resolve_object_id(self, url: str) -> str:
        parsed = urlparse(url)

        if "relay.ozolio.com" in parsed.netloc and parsed.path.endswith("/pub.api"):
            object_id = self.extract_object_id_from_query(parsed.query)
            if object_id:
                return object_id

        if "ozolio.com" in parsed.netloc and parsed.path.startswith("/explore/"):
            return self.extract_object_id_from_page(url)

        return self.extract_object_id_from_page(url)

    def extract_object_id_from_query(self, query: str) -> str | None:
        params = parse_qs(query)
        values = params.get("oid")

        if not values:
            return None

        object_id = values[0]

        if not object_id.startswith("EMB_"):
            raise ValueError(f"Unexpected Ozolio object ID: {object_id}")

        return object_id

    def extract_object_id_from_page(self, url: str) -> str:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        html = response.text

        iframe_match = re.search(
            r'pub\.api\?cmd=embed&oid=(EMB_[A-Z0-9]+)',
            html,
        )
        if iframe_match:
            return iframe_match.group(1)

        player_match = re.search(
            r'object:\s*"([^"]+)"',
            html,
        )
        if player_match:
            return player_match.group(1)

        raise ValueError("Could not find Ozolio object ID")

    def initialize_session(self, server: str, object_id: str, document: str) -> dict:
        response = requests.get(
            f"{server}/ses.api",
            params={
                "cmd": "init",
                "oid": object_id,
                "ver": 5,
                "channel": 0,
                "control": 0,
                "document": document,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def find_m3u8_output(self, outputs: list) -> dict:
        for output in outputs:
            formats = output.get("formats", "")

            if "M3U8" in formats:
                return output

        raise ValueError("No M3U8 output found")

    def open_output(self, server: str, session_id: str, output_id: str) -> dict:
        response = requests.get(
            f"{server}/ses.api",
            params={
                "cmd": "open",
                "oid": session_id,
                "output": output_id,
                "format": "M3U8",
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def extract_stream_url(self, open_data: dict) -> str:
        stream_url = open_data["output"]["source"]

        if ".m3u8" not in stream_url:
            raise ValueError("Ozolio response did not contain an M3U8 stream URL")

        return stream_url