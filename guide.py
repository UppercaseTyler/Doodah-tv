import os
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape


OUTPUT_DIR = "output"
GUIDE_FILE = os.path.join(OUTPUT_DIR, "guide.xml")

DEFAULT_TIMEZONE = "America/New_York"
GUIDE_DAYS = 7


def xmltv_time(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S %z")


def generate_simple_programmes(channel: dict) -> list[dict]:
    channel_timezone = ZoneInfo(DEFAULT_TIMEZONE)

    now = datetime.now(channel_timezone)
    start_date = now.date()

    programmes = []

    for day_offset in range(GUIDE_DAYS):
        current_date = start_date + timedelta(days=day_offset)

        day_start = datetime.combine(
            current_date,
            time.min,
            tzinfo=channel_timezone,
        )

        for hour in range(24):
            start = day_start + timedelta(hours=hour)
            stop = start + timedelta(hours=1)

            programmes.append(
                {
                    "start": start,
                    "stop": stop,
                    "title": channel["name"],
                }
            )

    return programmes


def generate_xmltv(channels):
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

        guide_config = channel.get("guide", {})
        guide_style = guide_config.get("style", "simple")

        description = escape(
            channel.get(
                "guide_description",
                f"Live stream from Doodah TV: {channel['name']}",
            )
        )

        if guide_style == "simple":
            programmes = generate_simple_programmes(channel)
        else:
            raise ValueError(
                f"Unknown guide style '{guide_style}' "
                f"for channel {channel_id}"
            )

        for programme in programmes:
            title = escape(programme["title"])

            lines.append(
                f'  <programme '
                f'start="{xmltv_time(programme["start"])}" '
                f'stop="{xmltv_time(programme["stop"])}" '
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