import yaml

from providers.hls import HLSProvider


PROVIDERS = {
    "hls": HLSProvider(),
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def resolve_channels(config: dict):
    resolved_streams = []

    for channel in config["channels"]:
        if not channel.get("enabled", True):
            continue

        source = channel["source"]
        provider = PROVIDERS[source]

        resolved_stream = provider.resolve(channel)
        resolved_streams.append(resolved_stream)

    return resolved_streams


def main():
    config = load_config()
    streams = resolve_channels(config)

    for stream in streams:
        print(f"{stream.number} - {stream.name}")
        print(f"Source: {stream.source}")
        print(f"URL: {stream.url}")
        print()


if __name__ == "__main__":
    main()