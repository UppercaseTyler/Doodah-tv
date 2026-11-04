from dataclasses import dataclass
from typing import Optional


@dataclass
class ResolvedStream:
    name: str
    number: int
    enabled: bool
    source: str
    url: str
    guide_title: str
    guide_description: str
    hls_manifest: Optional[str] = None


class Provider:
    def resolve(self, channel: dict) -> ResolvedStream:
        raise NotImplementedError("Each provider must implement resolve()")
