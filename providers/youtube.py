import subprocess

from providers.base import Provider, ResolvedStream


class YouTubeProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        selectors = [
            "best[protocol^=m3u8]/best",
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

            errors.append(f"{selector}: yt-dlp returned no manifest URL")

        error_detail = " | ".join(errors)

        raise RuntimeError(
            f"YouTube resolution failed for channel {channel['number']} "
            f"({channel['name']}): {error_detail}"
        )
