"""Things Wony notices without being asked.

A trigger is a plain Python check on one background thread — no model call at
rest, so an idle machine costs nothing. When one finds something worth saying it
does *not* show canned text: it hands the fact to the agent as a turn, so the
message is in persona and the model can offer to do something about it ("the
disk is nearly full — want me to look at what is using it?").

All of it is off until `assistant.proactive.enabled` is set. Wony starting a
conversation on its own is the kind of thing that has to be asked for.
"""

import time
import typing

from helpers.jobs import BackgroundJobs
from helpers.logger import logger

_JOB_NAME = "triggers"

# How often the thread wakes. Each trigger has its own `interval` and is only
# polled when due, so this is just the resolution, not the polling rate.
_TICK_SECONDS = 60.0

# Nothing may interrupt within this of the last proactive message, whichever
# trigger fired. Two unrelated interruptions back to back is how a helpful
# assistant turns into an annoying one.
_MIN_GAP_SECONDS = 300.0

# Free space under this counts as low; the temperature check uses
# modules.system's own threshold so the trigger and the health report agree.
_LOW_DISK_PERCENT = 10
_EVENT_SOON_MINUTES = 15

# Subjects named in one announcement. A backlog of important mail is a backlog,
# not four separate interruptions.
_EMAIL_SCAN = 5


class Trigger(typing.NamedTuple):
    name: str
    watches: str  # one line for `manage_triggers list`
    poll: typing.Callable[[], typing.Optional[str]]
    interval: float  # seconds between polls
    cooldown: float  # seconds before this trigger may fire again


_last_polled: typing.Dict[str, float] = {}
_last_fired: typing.Dict[str, float] = {}
_last_fact: typing.Dict[str, str] = {}
_last_any_fire: float = 0.0
_disabled: typing.Set[str] = set()


def enabled() -> bool:
    from helpers.config import Config

    return bool(Config.get("assistant.proactive.enabled", False))


def all_triggers() -> typing.List[Trigger]:
    return list(_TRIGGERS)


def is_on(name: str) -> bool:
    return name not in _disabled


def set_enabled(name: str, on: bool) -> None:
    """Turn one trigger off for this run. Not persisted: the config switch is
    the durable answer, and this is 'not right now'."""
    if on:
        _disabled.discard(name)
    else:
        _disabled.add(name)


def start() -> bool:
    """Begin watching. No-op when proactive mode is off."""
    if not enabled():
        return False
    return BackgroundJobs.start(_JOB_NAME, _tick, interval=_TICK_SECONDS)


def stop() -> bool:
    return BackgroundJobs.stop(_JOB_NAME)


def running() -> bool:
    return BackgroundJobs.is_running(_JOB_NAME)


def _tick() -> None:
    if not enabled():
        return

    from helpers.decorators import agent_lock

    now = time.time()
    for trigger in _TRIGGERS:
        if trigger.name in _disabled:
            continue
        if now - _last_polled.get(trigger.name, 0.0) < trigger.interval:
            continue
        _last_polled[trigger.name] = now

        try:
            fact = trigger.poll()
        except Exception as e:
            # One broken check must not end the thread and take the other
            # three with it.
            logger.log_error(str(e), f"trigger:{trigger.name}")
            continue

        if not fact:
            continue
        # Same news is not news. Without this a drive sitting at 3% free would
        # re-announce itself every time its cooldown expired.
        if fact == _last_fact.get(trigger.name):
            continue
        if now - _last_fired.get(trigger.name, 0.0) < trigger.cooldown:
            continue
        if now - _last_any_fire < _MIN_GAP_SECONDS:
            continue
        # Someone is mid-conversation. Interrupting a turn in progress is worse
        # than being a minute late; the next tick will still have the fact.
        if agent_lock.locked():
            continue

        _fire(trigger, fact)
        return  # one interruption per tick, whatever else is pending


def _fire(trigger: Trigger, fact: str) -> None:
    global _last_any_fire

    from helpers.notify import notify
    from helpers.turn import run_turn

    now = time.time()
    _last_fired[trigger.name] = now
    _last_fact[trigger.name] = fact
    _last_any_fire = now

    logger.log_system_event("trigger", f"{trigger.name}: {fact}")
    result = run_turn(
        f"[Nothing was asked. You noticed this yourself: {fact} "
        "Say it in one or two sentences, and offer to help if there is "
        "something you could do about it.]"
    )
    # The turn is deliberately not recorded into Conversation: the user did not
    # say any of it, and a history full of trigger prompts would have the model
    # answering questions nobody asked.
    notify(result.text or fact, kind="alert", source=f"trigger:{trigger.name}")


# ------------------------------------------------------------------ the checks
#
# Each one reads a module's public surface and returns a sentence or None.
# Nothing here calls a model, so the thread is free when there is no news.


def _module_on(name: str) -> bool:
    from helpers.config import Config

    return Config.is_module_enabled(name)


def _too_hot() -> typing.Optional[str]:
    """A Pi 4 throttles itself at 80 °C — by then it is already slow and the
    user has no fan noise to tell them why."""
    if not _module_on("system"):
        return None
    from modules import system

    reading = system.temperature()
    if reading is None or reading < system.HIGH_TEMPERATURE_C:
        return None
    return f"The device is running at {round(reading)} °C, hot enough to slow itself down."


def _disk_low() -> typing.Optional[str]:
    if not _module_on("system"):
        return None
    from modules import system

    for drive in system.disks():
        if drive["free_percent"] <= _LOW_DISK_PERCENT:
            return (
                f"Drive {drive['mount']} is nearly full — "
                f"{drive['free_gb']} GB free, {drive['free_percent']}% of the disk."
            )
    return None


def _event_soon() -> typing.Optional[str]:
    if not _module_on("calendar"):
        return None
    from datetime import timedelta

    from helpers.registry import ServiceRegistry
    from helpers.timeutil import now_local

    cal = ServiceRegistry.get_service_instance("calendar")
    if cal is None:
        return None

    now = now_local()
    horizon = now + timedelta(minutes=_EVENT_SOON_MINUTES)
    for event in cal.agenda_snapshot(days=1).get("events", []):
        if event.get("all_day"):
            continue
        try:
            from datetime import datetime

            start = datetime.fromisoformat(str(event["start"]))
        except (KeyError, ValueError):
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=now.tzinfo)
        if now <= start <= horizon:
            minutes = max(1, round((start - now).total_seconds() / 60))
            return f"'{event['title']}' starts in about {minutes} minutes."
    return None


def _important_email() -> typing.Optional[str]:
    if not _module_on("gmail"):
        return None
    from helpers.registry import ServiceRegistry

    gmail = ServiceRegistry.get_service_instance("gmail")
    if gmail is None:
        return None

    # Gmail's own importance markers, not a guess made here. find_emails would
    # answer in prose (and its overview counts the whole inbox); this needs the
    # subjects to tell one batch of mail from the next.
    # newer_than, or the first tick on a machine with a year of unread mail
    # announces a backlog nobody wanted to hear about.
    messages = gmail.search_messages(
        "is:unread is:important newer_than:1d", max_results=_EMAIL_SCAN
    )
    if not messages:
        return None

    subjects = [m.subject.strip() or "(no subject)" for m in messages]
    if len(subjects) == 1:
        return f"There is unread mail marked important: '{subjects[0]}'."
    return (
        f"There are {len(subjects)} unread emails marked important: "
        + ", ".join(f"'{s}'" for s in subjects)
        + "."
    )


_TRIGGERS: typing.List[Trigger] = [
    Trigger(
        "too_hot",
        "The device running hot enough to throttle.",
        _too_hot,
        interval=300.0,
        cooldown=3600.0,
    ),
    Trigger(
        "disk_low",
        "A drive nearly out of space.",
        _disk_low,
        interval=900.0,
        cooldown=21600.0,
    ),
    Trigger(
        "event_soon",
        f"A calendar event starting within {_EVENT_SOON_MINUTES} minutes.",
        _event_soon,
        interval=300.0,
        cooldown=300.0,
    ),
    Trigger(
        "important_email",
        "Unread mail Gmail marked important.",
        _important_email,
        interval=300.0,
        cooldown=900.0,
    ),
]
