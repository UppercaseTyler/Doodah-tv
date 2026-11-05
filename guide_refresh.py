"""Keep the startup channel snapshot's guide fresh at local midnight."""

import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from guide import write_guide


REFRESH_TIMEZONE = ZoneInfo("America/New_York")
logger = logging.getLogger(__name__)


def seconds_until_midnight(now=None):
    now = datetime.now(REFRESH_TIMEZONE) if now is None else now.astimezone(REFRESH_TIMEZONE)
    midnight = datetime.combine(
        now.date() + timedelta(days=1), time.min, tzinfo=REFRESH_TIMEZONE,
    )
    # Subtract in UTC: a local day can be 23 or 25 hours across DST changes.
    return (midnight.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds()


def refresh_guide_at_midnight(channels, stop_event):
    while not stop_event.is_set():
        delay = seconds_until_midnight()
        logger.info(
            "Next guide refresh at midnight %s (in %.0f seconds)",
            REFRESH_TIMEZONE.key, delay,
        )
        if stop_event.wait(delay):
            return

        try:
            path = write_guide(channels)
            logger.info("Guide refresh complete: %s", path)
        except Exception:
            logger.exception(
                "Guide refresh failed; keeping previous guide and retrying next midnight"
            )
