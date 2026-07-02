import subprocess

from providers.base import Provider, ResolvedStream


class YouTubeProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        result = subprocess.run(
            [
                "yt-dlp",
                "-g",
                "--remote-components",
                "ejs:github",
                "-f",
                "best[protocol^=m3u8]/best",
                channel["url"],
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        stream_url = result.stdout.strip().splitlines()[-1]

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