from providers.base import Provider, ResolvedStream


class HLSProvider(Provider):
    def resolve(self, channel: dict) -> ResolvedStream:
        return ResolvedStream(
            name=channel["name"],
            number=channel["number"],
            enabled=channel["enabled"],
            source=channel["source"],
            url=channel["url"],
        )