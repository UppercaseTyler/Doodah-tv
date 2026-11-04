import subprocess
from typing import Optional

import m3u8
import requests

from providers.base import Provider, ResolvedStream


def select_hls_rendition(content: str, manifest_url: str) -> Optional[str]:
    """Keep one H.264/AAC rendition, including its separate audio playlist."""
    if not content.lstrip().startswith("#EXTM3U"):
        raise ValueError("YouTube returned an invalid HLS manifest")

    master = m3u8.loads(content, uri=manifest_url)
    if not master.is_variant:
        if not master.segments:
            raise ValueError("YouTube returned an empty HLS media playlist")
        return None  # Already a single media playlist; redirect normally.

    candidates = []
    for variant in master.playlists:
        info = variant.stream_info
        codecs = (info.codecs or "").lower().split(",")
        codecs = [codec.strip() for codec in codecs]
        if (
            any(codec.startswith(("avc1", "avc3")) for codec in codecs)
            and all(codec.startswith(("avc1", "avc3", "mp4a")) for codec in codecs)
            and info.resolution
        ):
            candidates.append(variant)

    if not candidates:
        raise ValueError("YouTube has no compatible H.264/AAC HLS rendition")

    def quality(variant):
        info = variant.stream_info
        width, height = info.resolution
        return (height, width, info.frame_rate or 0,
                info.average_bandwidth or info.bandwidth or 0)

    chosen = max(candidates, key=quality)
    selected = m3u8.M3U8()
    selected.version = master.version
    selected.is_independent_segments = master.is_independent_segments

    if chosen.stream_info.audio:
        audio_tracks = [
            media for media in master.media
            if media.type == "AUDIO" and media.group_id == chosen.stream_info.audio
        ]
        if not audio_tracks:
            raise ValueError("YouTube rendition references a missing audio group")
        audio = next((track for track in audio_tracks if track.default == "YES"),
                     audio_tracks[0])
        if audio.uri:
            audio.uri = audio.absolute_uri
        selected.add_media(audio)

    # Clients fetch these directly from YouTube, not relative to /channel/<number>.
    chosen.uri = chosen.absolute_uri
    chosen.stream_info.subtitles = None
    chosen.stream_info.video = None
    chosen.stream_info.closed_captions = "NONE"
    selected.add_playlist(chosen)
    return selected.dumps()


class YouTubeProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        selectors = [
            "best[protocol^=m3u8]",
            "bestvideo[protocol^=m3u8]",
        ]

        errors = []

        for selector in selectors:
            try:
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "--remote-components",
                        "ejs:github",
                        "-f",
                        selector,
                        "--print",
                        "%(manifest_url)s",
                        channel["url"],
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as error:
                detail = error.stderr.strip() or str(error)
                errors.append(f"{selector}: {detail}")
                continue

            output_lines = result.stdout.strip().splitlines()
            stream_url = output_lines[-1] if output_lines else ""

            if stream_url and stream_url != "NA":
                try:
                    response = requests.get(stream_url, timeout=15)
                    response.raise_for_status()
                    manifest = select_hls_rendition(response.text, response.url)
                except (requests.RequestException, ValueError) as error:
                    errors.append(f"{selector}: {error}")
                    continue

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
                    hls_manifest=manifest,
                )

            errors.append(f"{selector}: yt-dlp returned no manifest URL")

        error_detail = " | ".join(errors)

        raise RuntimeError(
            f"YouTube resolution failed for channel {channel['number']} "
            f"({channel['name']}): {error_detail}"
        )
