import os
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape


OUTPUT_DIR = "output"
GUIDE_FILE = os.path.join(OUTPUT_DIR, "guide.xml")


def xmltv_time(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S %z")


def generate_xmltv(channels):
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=24)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<tv generator-info-name="Doodah TV">')

    for channel in channels:
        channel_id = str(channel["number"])
        name = escape(channel["name"])

        lines.append(f'  <channel id="{channel_id}">')
        lines.append(f"    <display-name>{name}</display-name>")
        lines.append("  </channel>")

    for channel in channels:
        channel_id = str(channel["number"])
        title = escape(channel.get("guide_title", channel["name"]))
        description = escape(
            channel.get(
                "guide_description",
                f"Live stream from Doodah TV: {channel['name']}",
            )
        )

        lines.append(
            f'  <programme start="{xmltv_time(now)}" '
            f'stop="{xmltv_time(end)}" '
            f'channel="{channel_id}">'
        )
        lines.append(f"    <title>{title}</title>")
        lines.append(f"    <desc>{description}</desc>")
        lines.append("  </programme>")

    lines.append("</tv>")

    return "\n".join(lines) + "\n"

def write_guide(streams):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    guide = generate_xmltv(streams)

    with open(GUIDE_FILE, "w", encoding="utf-8") as file:
        file.write(guide)

    return GUIDE_FILE