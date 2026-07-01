from dataclasses import dataclass


@dataclass
class ResolvedStream:
    name: str
    number: int
    enabled: bool
    source: str
    url: str


class Provider:
    def resolve(self, channel: dict) -> ResolvedStream:
        raise NotImplementedError("Each provider must implement resolve()")