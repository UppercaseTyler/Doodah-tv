import hashlib
import os
import warnings
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from xml.sax.saxutils import escape


OUTPUT_DIR = "output"
GUIDE_FILE = os.path.join(OUTPUT_DIR, "guide.xml")

DEFAULT_TIMEZONE = "America/New_York"
GUIDE_DAYS = 7


DAYPARTS = [
    {
        "id": "overnight",
        "start": time(22, 0),
        "stop": time(7, 0),
    },
    {
        "id": "morning",
        "start": time(7, 0),
        "stop": time(11, 0),
    },
    {
        "id": "midday",
        "start": time(11, 0),
        "stop": time(15, 0),
    },
    {
        "id": "afternoon",
        "start": time(15, 0),
        "stop": time(18, 0),
    },
    {
        "id": "evening",
        "start": time(18, 0),
        "stop": time(20, 0),
    },
    {
        "id": "twilight",
        "start": time(20, 0),
        "stop": time(22, 0),
    },
]


DAYPARTS_THEMES = {
    "standard": {
        "overnight": "Overnight at {name}",
        "morning": "Morning at {name}",
        "midday": "Midday at {name}",
        "afternoon": "Afternoon at {name}",
        "evening": "Evening at {name}",
        "twilight": "Twilight at {name}",
    },
    "fantasy": {
        "overnight": "Night watch over {name}",
        "morning": "Dawn breaks over {name}",
        "midday": "High sun over {name}",
        "afternoon": "The day turns at {name}",
        "evening": "Evening settles over {name}",
        "twilight": "The light fades at {name}",
    },
    "poetic": {
        "overnight": "A quiet night at {name}",
        "morning": "A beautiful morning at {name}",
        "midday": "A bright midday at {name}",
        "afternoon": "A peaceful afternoon at {name}",
        "evening": "A gentle evening at {name}",
        "twilight": "A soft twilight at {name}",
    },
    "aquarium": {
        "overnight": "Night beneath the surface at {name}",
        "morning": "Morning light through the water at {name}",
        "midday": "Midday beneath the waves at {name}",
        "afternoon": "Afternoon in the blue at {name}",
        "evening": "Evening glows beneath the surface at {name}",
        "twilight": "The water darkens at {name}",
    },
    "bananas": {
        "overnight": "It's banana time at {name}",
        "morning": "It's banana time at {name}",
        "midday": "It's banana time at {name}",
        "afternoon": "Time for a banana at {name}",
        "evening": "It's banana time at {name}",
        "twilight": "It's banana time at {name}",
    },
}


RANDOM_DAYPARTS_THEMES = (
    "standard",
    "fantasy",
    "poetic",
)


def xmltv_time(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S %z")


def get_channel_timezone(channel: dict) -> ZoneInfo:
    channel_id = str(channel["number"])
    timezone_name = channel.get("timezone") or DEFAULT_TIMEZONE

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        warnings.warn(
            f"Invalid timezone '{timezone_name}' for channel {channel_id}; "
            f"using '{DEFAULT_TIMEZONE}'",
            stacklevel=2,
        )
        return ZoneInfo(DEFAULT_TIMEZONE)


def get_guide_style(channel: dict) -> str:
    channel_id = str(channel["number"])
    guide_style = channel.get("guide_style") or "simple"

    if guide_style in {"simple", "dayparts"}:
        return guide_style

    warnings.warn(
        f"Unknown guide style '{guide_style}' for channel {channel_id}; "
        "using 'simple'",
        stacklevel=2,
    )
    return "simple"


def get_dayparts_theme(channel: dict) -> str:
    channel_id = str(channel["number"])
    theme = channel.get("dayparts_theme") or "standard"

    if theme == "random" or theme in DAYPARTS_THEMES:
        return theme

    warnings.warn(
        f"Unknown dayparts theme '{theme}' for channel {channel_id}; "
        "using 'standard'",
        stacklevel=2,
    )
    return "standard"


def choose_random_theme(current_date, channel_number, daypart_id) -> str:
    seed = f"{current_date.isoformat()}:{channel_number}:{daypart_id}"
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    choice_index = int.from_bytes(digest[:4], "big") % len(RANDOM_DAYPARTS_THEMES)

    return RANDOM_DAYPARTS_THEMES[choice_index]


def render_dayparts_title(
    channel: dict,
    daypart_id: str,
    current_date,
    theme: str,
) -> str:
    dayparts_name = channel.get("dayparts_name") or channel["name"]

    if theme == "random":
        theme = choose_random_theme(
            current_date=current_date,
            channel_number=channel["number"],
            daypart_id=daypart_id,
        )

    template = DAYPARTS_THEMES[theme][daypart_id]
    return template.format(name=dayparts_name)


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


def generate_dayparts_programmes(channel: dict) -> list[dict]:
    channel_timezone = get_channel_timezone(channel)
    dayparts_theme = get_dayparts_theme(channel)

    now = datetime.now(channel_timezone)
    start_date = now.date()

    window_start = datetime.combine(
        start_date,
        time.min,
        tzinfo=channel_timezone,
    )
    window_end = datetime.combine(
        start_date + timedelta(days=GUIDE_DAYS),
        time.min,
        tzinfo=channel_timezone,
    )

    programmes = []
    first_daypart_date = start_date - timedelta(days=1)

    for day_offset in range(GUIDE_DAYS + 1):
        current_date = first_daypart_date + timedelta(days=day_offset)

        for daypart in DAYPARTS:
            start = datetime.combine(
                current_date,
                daypart["start"],
                tzinfo=channel_timezone,
            )

            if daypart["stop"] <= daypart["start"]:
                stop_date = current_date + timedelta(days=1)
            else:
                stop_date = current_date

            stop = datetime.combine(
                stop_date,
                daypart["stop"],
                tzinfo=channel_timezone,
            )

            if stop <= window_start or start >= window_end:
                continue

            programmes.append(
                {
                    "start": start,
                    "stop": stop,
                    "title": render_dayparts_title(
                        channel=channel,
                        daypart_id=daypart["id"],
                        current_date=current_date,
                        theme=dayparts_theme,
                    ),
                }
            )

    programmes.sort(key=lambda programme: programme["start"])

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
        guide_style = get_guide_style(channel)

        description = escape(
            channel.get(
                "guide_description",
                f"Live stream from Doodah TV: {channel['name']}",
            )
        )

        if guide_style == "dayparts":
            programmes = generate_dayparts_programmes(channel)
        else:
            programmes = generate_simple_programmes(channel)

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
