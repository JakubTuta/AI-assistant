import subprocess
from datetime import datetime

from helpers.config import Config
from helpers.decorators import capture_response
from helpers.logger import logger
from helpers.registry import register_job


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
