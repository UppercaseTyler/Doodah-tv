import yt_dlp

from providers.base import Provider, ResolvedStream


class YouTubeProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        ydl_options = {
            "quiet": True,
            "no_warnings": True,
            "format": "best",
        }

        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(channel["url"], download=False)

        stream_url = info["url"]

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