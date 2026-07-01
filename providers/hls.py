from providers.base import Provider, ResolvedStream


class HLSProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        return ResolvedStream(
            name=channel["name"],
            number=channel["number"],
            enabled=channel["enabled"],
            source=channel["source"],
            url=channel["url"],
            guide_title=channel.get("guide_title", channel["name"]),
            guide_description=channel.get(
                "guide_description",
                f"Live stream from Doodah TV: {channel['name']}",
    ),
)