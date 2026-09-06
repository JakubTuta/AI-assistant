import os
import typing
from datetime import datetime, timedelta

from helpers.audio import Audio
from helpers.cache import Cache
from helpers.config import Config
from helpers.decorators import capture_response
from helpers.logger import logger
from helpers.registry import ServiceRegistry, register_job
from helpers.timeutil import now_local


# --- clock ---


@register_job(module_name="basics", summary="Tell the current time and date")
@capture_response
def get_datetime(part: str = "both") -> str:
    """
    [CLOCK JOB] Tells the current local time, today's date, or both.

    Args:
        part (str): "time" for the clock, "date" for the day, "both" (the default)
            for one sentence carrying each.

    Returns:
        str: The current time and/or date.
    """
    now = datetime.now()
    wanted = (part or "both").strip().lower()
    if wanted == "time":
        return f"It's {now.strftime('%H:%M')}."
    if wanted == "date":
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    return f"It's {now.strftime('%H:%M')} on {now.strftime('%A, %B %d, %Y')}."


# --- system ---


@register_job(module_name="basics", confirms=True)
@capture_response
def close_computer() -> str:
    """
    [SYSTEM CONTROL JOB] Immediately shuts down the entire computer system.
    This is a critical system operation that forcefully terminates all processes
    and powers off the machine. Use with extreme caution as it will close all applications.

    Returns:
        str: Confirmation of shutdown, cancellation, or why it couldn't be confirmed.
    """
    try:
        confirmation = input("Shut down the computer? Type 'yes' to confirm: ").strip().lower()
    except (EOFError, RuntimeError):
        # No console attached (tray/pythonw mode) — input() can't prompt at all.
        # Refuse rather than either hanging forever or shutting down unconfirmed.
        logger.log_system_event("shutdown_refused", "No console available to confirm shutdown.")
        return "Can't confirm a shutdown without a console — run 'wony.py text' or 'wony.py voice' to do this."

    if confirmation != "yes":
        logger.log_system_event("shutdown_cancelled", "User did not confirm shutdown.")
        return "Shutdown cancelled."

    audio = Cache.get_audio()
    if audio:
        Audio.play_cached("Closing computer. o7")
    logger.log_system_event("shutdown", "Shutting down computer.")
    os.system("shutdown /s /f /t 0")
    return "Shutting down now."


# --- greeting ---


@register_job(module_name="basics", summary="Greet with daily briefing")
@capture_response
def greeting() -> str:
    """
    [GREETING JOB] Provides a personalized time-of-day greeting with a daily briefing.

    Includes owner name, full date and time, and conditionally appends current weather,
    unread email summary with deduplicated senders, and today's calendar meetings depending
    on which modules are enabled.

    Returns:
        str: Personalized greeting with time, date, and optional contextual info.
    """
    now = datetime.now()
    owner = Config.get("assistant.owner_name", "there")

    hour = now.hour
    if 5 <= hour < 12:
        phrase = "Good morning"
    elif 12 <= hour < 17:
        phrase = "Good afternoon"
    elif 17 <= hour < 21:
        phrase = "Good evening"
    else:
        phrase = "Hello"

    full_dt = now.strftime("%A, %B %d, %Y at %H:%M")
    parts: typing.List[str] = [f"{phrase}, {owner}! It's {full_dt}."]

    if Config.is_module_enabled("weather"):
        line = _weather_line()
        if line:
            parts.append(line)

    if Config.is_module_enabled("gmail"):
        line = _email_line()
        if line:
            parts.append(line)

    if Config.is_module_enabled("calendar"):
        line = _calendar_line()
        if line:
            parts.append(line)

    parts.append("What would you like me to do?")
    return "\n".join(parts)


# Each line below is built from another module's public surface — its
# snapshot() or a registered job — rather than reaching into its privates. The
# briefing used to call gmail._search, gmail._format_sender,
# cal._fetch_events_for_day and cal._format_time, so renaming any one of them
# broke the greeting and nothing said so.


def _weather_line() -> typing.Optional[str]:
    try:
        from modules.weather import snapshot

        current = snapshot()
        if current.get("error") or current.get("temperature") is None:
            return None

        line = (
            f"Weather in {current['city']}: {current['description']}, "
            f"{round(current['temperature'])}{current['unit']}"
        )
        feels = current.get("feels_like")
        if feels is not None and round(feels) != round(current["temperature"]):
            line += f", feels like {round(feels)}{current['unit']}"
        return line + "."
    except Exception as e:
        logger.log_error(str(e), "greeting.weather_line")
        return None


def _email_line() -> typing.Optional[str]:
    try:
        gmail = ServiceRegistry.get_service_instance("gmail")
        if not gmail:
            return None

        work_end = int(Config.get("modules.calendar.work_end_hour", 18))
        cutoff = (datetime.now() - timedelta(days=1)).replace(
            hour=work_end, minute=0, second=0, microsecond=0
        )
        return gmail.find_emails(
            query=f"after:{cutoff.strftime('%Y/%m/%d')}", view="overview"
        )
    except Exception as e:
        logger.log_error(str(e), "greeting.email_line")
        return None


def _calendar_line() -> typing.Optional[str]:
    try:
        cal = ServiceRegistry.get_service_instance("calendar")
        if not cal:
            return None

        today = now_local().date().isoformat()
        events = [
            event for event in cal.agenda_snapshot(days=1).get("events", [])
            if str(event.get("start", "")).startswith(today)
        ]
        if not events:
            return "You have no meetings today."

        lines = [f"You have {len(events)} meeting(s) today:"]
        for event in events:
            when = "all day" if event["all_day"] else event["start"][11:16]
            lines.append(f"  - {event['title']} at {when}")
        return "\n".join(lines)
    except Exception as e:
        logger.log_error(str(e), "greeting.calendar_line")
        return None
