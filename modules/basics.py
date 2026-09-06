import os
import subprocess
import typing
from datetime import datetime, timedelta

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


def _run_power_command(verb: str, systemctl_action: str) -> str:
    """The gate is a config key rather than a typed confirmation: there is no
    console on this device, and a touch screen cannot answer input(). The UI
    confirms before it ever gets here."""
    if not bool(Config.get("modules.basics.allow_power_off", False)):
        logger.log_system_event(f"{systemctl_action}_refused", "Power control is disabled.")
        return (
            f"Power control is off. Set modules.basics.allow_power_off: true in "
            f"config.yaml to let me {verb} this device."
        )

    logger.log_system_event(systemctl_action, f"Running systemctl {systemctl_action}.")
    try:
        result = subprocess.run(
            ["systemctl", systemctl_action],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return "Can't find systemctl — this job only works on a systemd Linux system."
    except subprocess.TimeoutExpired:
        # systemctl normally returns immediately and the machine goes down
        # afterwards, so a timeout means the request is stuck, not succeeding.
        return f"The {verb} request timed out."

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return f"Couldn't {verb}: {detail or f'systemctl exited {result.returncode}'}"

    return f"{verb.capitalize()}ing now. o7"


@register_job(module_name="basics", summary="Power off or restart this device", confirms=True)
@capture_response
def power_device(action: str = "off") -> str:
    """
    [SYSTEM CONTROL JOB] Shuts down or restarts this device.

    Args:
        action (str): "off" to shut down (the default), or "restart".

    Returns:
        str: Confirmation, or why it did not happen.
    """
    wanted = (action or "off").strip().lower()
    if wanted in ("restart", "reboot"):
        return _run_power_command("restart", "reboot")
    if wanted in ("off", "shutdown", "shut down", "power off"):
        return _run_power_command("shut down", "poweroff")
    return f"Unknown action '{action}'. Use off or restart."


# Reversible, but it blanks the display: worth confirming, because if the
# touchscreen does not wake it the way back is an SSH session.
@register_job(module_name="basics", summary="Send the screen to sleep, or wake it",
              confirms={"sleep", "off", "doze", "rest"})
@capture_response
def sleep_device(action: str = "sleep", wake_at: str = "") -> str:
    """
    [SYSTEM CONTROL JOB] Puts the display to sleep, or wakes it up again.

    This is not a shutdown and not a suspend — a Raspberry Pi cannot suspend to
    RAM. The screen goes dark and the pollers stop; every process keeps
    running, so timers still fire and waking up is instant.

    Args:
        action (str): "sleep" (the default) or "wake".
        wake_at (str): When to wake by itself — a clock time like "07:00", or a
            duration like "8h" or "90m". Empty means it sleeps until someone
            touches the screen.

    Returns:
        str: What happened, and when it will wake.
    """
    from helpers import lowpower

    wanted = (action or "sleep").strip().lower()

    if wanted in ("wake", "wake up", "on"):
        if not lowpower.is_asleep():
            return "The screen is already awake."
        lowpower.wake(reason="asked")
        return "Awake. 🤍"

    if wanted not in ("sleep", "off", "doze", "rest"):
        return f"Unknown action '{action}'. Use sleep or wake."

    try:
        state = lowpower.enter(wake_at=wake_at, reason="asked")
    except lowpower.WakeTimeError as e:
        return str(e)

    when = state.get("wake_at")
    if when:
        return f"Going to sleep. I'll wake at {when[11:16]} — or when you touch the screen."
    return "Going to sleep. Touch the screen when you want me back."


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
