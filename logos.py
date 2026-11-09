"""Shared channel logo selection for M3U and XMLTV metadata."""

from pathlib import Path
from urllib.parse import quote, urlsplit


LOGO_DIR = Path("assets/logos")
DEFAULT_LOGO = "doodah-logo.png"
DEFAULT_LOGO_URL = (
    "https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/"
    "main/assets/logos/doodah-logo.png"
)


def channel_logo_url(channel, server_config):
    logo = (channel.get("logo") or "").strip() or DEFAULT_LOGO
    if logo == DEFAULT_LOGO:
        return DEFAULT_LOGO_URL

    parsed = urlsplit(logo)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return logo
    if parsed.scheme or parsed.netloc:
        raise ValueError("Channel logo must be a local filename or an HTTP(S) URL")

    if not (LOGO_DIR / logo).is_file():
        return DEFAULT_LOGO_URL

    host = server_config["host"]
    port = server_config["port"]
    return f"http://{host}:{port}/logos/{quote(logo, safe='/')}"
