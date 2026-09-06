"""Guards for behaviours that were silently wrong before.

Each case here is a bug that shipped and looked fine from the outside: a config
file that was never read, a document that was indexed but only searchable by its
first page, pollers that disappeared when the assistant was paused, an MCP tool
that could take over a built-in job's name.

Run directly: python tests/test_audit_regressions.py
"""
import datetime
import os
import sys
import tempfile
import threading
import typing
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)


class TestConfigIsRepoAnchored(unittest.TestCase):
    def test_config_found_from_any_working_directory(self) -> None:
        """systemd starts the kiosk from an arbitrary directory, and
        `wony.py text` can be run from anywhere. Resolving config.yaml
        against the CWD meant both silently fell through to defaults."""
        from helpers.config import _resolve_yaml_path

        original = os.getcwd()
        with tempfile.TemporaryDirectory() as elsewhere:
            try:
                os.chdir(elsewhere)
                resolved = _resolve_yaml_path("config.example.yaml")
            finally:
                os.chdir(original)

        self.assertIsNotNone(resolved)
        self.assertEqual(
            os.path.normcase(os.path.dirname(os.path.abspath(resolved))),
            os.path.normcase(_REPO_ROOT),
        )


class TestSemanticChunking(unittest.TestCase):
    def test_long_document_becomes_many_chunks(self) -> None:
        """A whole document in one embedding row is searchable by its opening
        paragraph and nothing else — the model truncates the rest."""
        from helpers.semantic import _CHUNK_CHARS, chunk_text

        text = "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(40))
        chunks = chunk_text(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= _CHUNK_CHARS for c in chunks))
        # The tail must survive: it is what "index a 50-page PDF" is asking for.
        self.assertIn("Paragraph 39", chunks[-1])

    def test_short_document_is_one_chunk(self) -> None:
        from helpers.semantic import chunk_text

        self.assertEqual(chunk_text("just a note"), ["just a note"])
        self.assertEqual(chunk_text("   "), [])


class TestBackgroundJobSuspend(unittest.TestCase):
    def setUp(self) -> None:
        from helpers.jobs import BackgroundJobs

        self.jobs = BackgroundJobs
        self.jobs.stop_all()

    def tearDown(self) -> None:
        self.jobs.stop_all()

    def test_suspended_jobs_come_back_on_resume(self) -> None:
        """Pausing the assistant used to call stop_all(), which permanently
        dropped every poller the user had asked for."""
        ran = threading.Event()

        self.assertTrue(self.jobs.start("poller", ran.set, interval=0.05))
        self.assertTrue(ran.wait(2.0))

        self.assertEqual(self.jobs.suspend_all(), ["poller"])
        self.assertEqual(self.jobs.list_jobs(), [])

        ran.clear()
        self.assertEqual(self.jobs.resume_suspended(), ["poller"])
        self.assertTrue(ran.wait(2.0))

    def test_stop_all_is_permanent(self) -> None:
        self.jobs.start("poller", lambda: None, interval=60)
        self.jobs.stop_all()
        self.assertEqual(self.jobs.resume_suspended(), [])


class TestMcpToolNaming(unittest.TestCase):
    def test_tool_cannot_shadow_a_builtin_job(self) -> None:
        """An external server naming a tool `exit` would otherwise replace the
        built-in job — and disconnecting the server would delete it."""
        from helpers.mcp_client import _job_name_for

        taken = {"exit": "", "send_email": "gmail"}
        self.assertEqual(_job_name_for("srv", "exit", taken), "srv_exit")
        self.assertEqual(_job_name_for("srv", "send_email", taken), "srv_send_email")

    def test_own_tools_keep_their_name_across_reconnects(self) -> None:
        from helpers.mcp_client import _job_name_for

        taken = {"search": "mcp:srv"}
        self.assertEqual(_job_name_for("srv", "search", taken), "search")

    def test_provider_illegal_characters_are_stripped(self) -> None:
        """Providers reject tool names outside [A-Za-z0-9_-]."""
        from helpers.mcp_client import _job_name_for

        self.assertEqual(_job_name_for("srv", "read file!", {}), "read_file_")


class TestKioskManifests(unittest.TestCase):
    def test_every_default_entry_names_a_real_job(self) -> None:
        """Three of the first eight tiles named jobs that did not exist
        (get_weather, check_emails, pause_song). Nothing caught it until the
        endpoint was called by hand — a tile that runs nothing looks exactly
        like a tile whose module is off."""
        import re

        from helpers.kiosk import _AMBIENT_CARDS, _DEFAULT_TILES

        # Read the module's source rather than the registry: a module only
        # registers its jobs once it is enabled AND its credentials are in
        # place, so a registry check passes or fails by local config instead of
        # by whether the name is real.
        entries = [(t["module"], t["job"]) for t in _DEFAULT_TILES if t["kind"] == "job"]
        entries += [(c["module"], c["job"]) for c in _AMBIENT_CARDS]

        sources: typing.Dict[str, str] = {}
        for module_name in {name for name, _ in entries}:
            path = os.path.join(_REPO_ROOT, "modules", f"{module_name}.py")
            with open(path, encoding="utf-8") as handle:
                sources[module_name] = handle.read()

        for module_name, job_name in entries:
            with self.subTest(module=module_name, job=job_name):
                self.assertRegex(
                    sources[module_name],
                    rf"(?m)^\s*def {re.escape(job_name)}\(",
                    f"{module_name} declares a tile/card for '{job_name}', "
                    f"which modules/{module_name}.py does not define.",
                )

        self.assertTrue(entries, "No default entries could be checked at all.")

    def test_prompt_tiles_carry_a_prompt(self) -> None:
        """A prompt tile with no prompt sends an empty message to the agent."""
        from helpers.kiosk import _DEFAULT_TILES

        for tile in _DEFAULT_TILES:
            if tile["kind"] == "prompt":
                with self.subTest(tile=tile["id"]):
                    self.assertTrue((tile.get("prompt") or "").strip())

    def test_screen_tiles_name_a_screen(self) -> None:
        """A screen tile with no screen is a tile that does nothing at all —
        there is no job to fall back on, and the failure is silent in the UI."""
        from helpers.kiosk import _DEFAULT_TILES

        for tile in _DEFAULT_TILES:
            if tile["kind"] == "screen":
                with self.subTest(tile=tile["id"]):
                    self.assertTrue((tile.get("screen") or "").strip())

    def test_screen_tiles_name_a_registered_panel(self) -> None:
        """A tile opening a screen whose data never loads is a dead end. Every
        screen tile that reads a panel must name one that exists; the screens
        that read no panel are listed here so adding another cannot pass
        unnoticed."""
        from helpers.kiosk import _DEFAULT_TILES
        from helpers.panels import _PANELS

        # notifications and commands fetch nothing; sleep has its own endpoints
        # (/api/sleep, /api/wake) because it writes device state rather than
        # reading a module's data.
        self_contained = {"notifications", "commands", "sleep"}
        checked = 0
        for tile in _DEFAULT_TILES:
            if tile["kind"] != "screen":
                continue
            screen = tile["screen"]
            if screen in self_contained:
                continue
            with self.subTest(tile=tile["id"]):
                self.assertIn(
                    screen,
                    _PANELS,
                    f"tile '{tile['id']}' opens '{screen}', which has no panel.",
                )
            checked += 1

        self.assertGreater(checked, 0, "No screen tiles were checked at all.")

    def test_panels_name_the_module_that_gates_them(self) -> None:
        """A panel gated on the wrong module either 503s while its module is
        on, or runs while its module is off."""
        from helpers.panels import _PANELS

        for key, spec in _PANELS.items():
            with self.subTest(panel=key):
                self.assertTrue(spec.module)
                # modules/<name>.py is the whole contract for a module name.
                self.assertTrue(
                    os.path.exists(
                        os.path.join(_REPO_ROOT, "modules", f"{spec.module}.py")
                    ),
                    f"panel '{key}' is gated on module '{spec.module}', "
                    "which has no modules/ file.",
                )

    def test_every_panel_loader_resolves(self) -> None:
        """A panel whose snapshot was renamed fails only when tapped, which is
        exactly where nobody is looking for it."""
        import inspect

        from helpers.panels import _PANELS

        # What each panel actually calls. Checked against the module rather
        # than the registry, which is only populated once modules have loaded.
        free_functions = {
            "weather": "snapshot",
            "home_assistant": "snapshot",
            "notes": "snapshot",
        }
        methods = {
            "calendar": "agenda_snapshot",
            "spotify": "playback_snapshot",
            "google_accounts": "accounts_snapshot",
            "scheduler": "reminders_snapshot",
        }

        checked = 0
        for key, spec in _PANELS.items():
            try:
                module = __import__(f"modules.{spec.module}", fromlist=["*"])
            except Exception:
                continue  # optional dependency missing; same as CI
            with self.subTest(panel=key):
                if spec.module in free_functions:
                    name = free_functions[spec.module]
                    self.assertTrue(
                        callable(getattr(module, name, None)),
                        f"panel '{key}' calls {spec.module}.{name}(), which is gone.",
                    )
                else:
                    name = methods[spec.module]
                    owners = [
                        cls
                        for _, cls in inspect.getmembers(module, inspect.isclass)
                        if cls.__module__ == module.__name__ and hasattr(cls, name)
                    ]
                    self.assertTrue(
                        owners,
                        f"panel '{key}' calls {spec.module}.{name}(), "
                        "which no class in that module defines.",
                    )
            checked += 1

        self.assertGreater(checked, 0, "No panels could be checked at all.")

    def test_a_loaders_keyerror_is_not_mistaken_for_an_unknown_panel(self) -> None:
        """panel() raises KeyError for a name that does not exist, and the API
        answers 404. A KeyError from inside a loader means something else
        entirely and must not read as 'no such panel'."""
        def explode() -> dict:
            raise KeyError("main")

        from helpers import panels
        from helpers.config import Config

        Config.load(os.path.join(_REPO_ROOT, "config.example.yaml"))
        assert Config._settings is not None
        original_modules = list(Config._settings.enabled_modules)
        # _Panel is a NamedTuple, so the entry is replaced rather than patched.
        original_panel = panels._PANELS["weather"]
        try:
            Config._settings.enabled_modules = ["weather"]
            panels._PANELS["weather"] = original_panel._replace(load=explode)
            with self.assertRaises(RuntimeError):
                panels.panel("weather")

            # And a genuinely unknown key still raises KeyError.
            with self.assertRaises(KeyError):
                panels.panel("nonsense")
        finally:
            panels._PANELS["weather"] = original_panel
            Config._settings.enabled_modules = original_modules

    def test_available_follows_enabled_modules(self) -> None:
        """The tile row is built from this; a panel for a module that is off is
        a button that only ever 503s."""
        from helpers.config import Config
        from helpers.panels import available

        Config.load(os.path.join(_REPO_ROOT, "config.example.yaml"))
        assert Config._settings is not None
        original = list(Config._settings.enabled_modules)
        try:
            Config._settings.enabled_modules = ["weather", "spotify"]
            keys = [p["key"] for p in available()]
            self.assertEqual(keys, ["weather", "music"])

            Config._settings.enabled_modules = []
            self.assertEqual(available(), [])
        finally:
            Config._settings.enabled_modules = original

    def test_screen_tiles_are_not_runnable(self) -> None:
        """POSTing a screen tile used to fall through to _run_job with a null
        job name, answering "'' isn't available right now." instead of saying
        the request made no sense."""
        from helpers import kiosk

        original = kiosk.tiles
        kiosk.tiles = lambda: [
            {"id": "accounts", "label": "Accounts", "icon": "", "kind": "screen",
             "job": None, "prompt": None, "screen": "accounts", "args": {}}
        ]
        try:
            with self.assertRaises(ValueError):
                kiosk.run_tile("accounts")
        finally:
            kiosk.tiles = original


class TestKioskJobsShareTheAgentLock(unittest.TestCase):
    """A tile runs a job on the request thread. Both of these fail silently:
    the flag one makes a running turn narrate every tool call, and the idle one
    only shows up as a screen that stopped refreshing."""

    def test_a_tile_waits_for_a_turn_in_progress(self) -> None:
        from helpers import kiosk
        from helpers.decorators import agent_lock
        from helpers.registry import ServiceRegistry

        started = threading.Event()
        ServiceRegistry._jobs["_probe"] = lambda: started.set() or "done"
        try:
            with agent_lock:
                worker = threading.Thread(
                    target=lambda: kiosk._run_job("_probe", {}, source="test")
                )
                worker.start()
                # The lock is held here, so the job must not have run yet.
                self.assertFalse(started.wait(0.3))
            worker.join(timeout=5)
            self.assertTrue(started.is_set())
        finally:
            ServiceRegistry._jobs.pop("_probe", None)

    def test_the_idle_screen_gives_up_instead_of_queueing(self) -> None:
        from helpers import kiosk
        from helpers.decorators import agent_lock
        from helpers.registry import ServiceRegistry

        ServiceRegistry._jobs["_probe"] = lambda: "done"
        try:
            with agent_lock:
                result = kiosk._run_job("_probe", {}, source="ambient:x", wait=False)
            self.assertFalse(result.ok)
            self.assertEqual(result.text, "")
        finally:
            ServiceRegistry._jobs.pop("_probe", None)


class TestNotifications(unittest.TestCase):
    def test_wipe_clears_notifications(self) -> None:
        """'Erase everything you know about me' has to mean the reminders that
        already fired too, not just conversation history."""
        import inspect

        from helpers import memory_db

        source = inspect.getsource(memory_db.wipe_all)
        self.assertIn("notifications", source)

    def test_notify_survives_a_dead_database(self) -> None:
        """A poller must not die because the DB is locked — the message still
        has to reach a connected screen."""
        from unittest import mock

        from helpers import events, notify as notify_mod

        seen = []
        events.subscribe(seen.append)
        try:
            with mock.patch(
                "helpers.memory_db.insert_notification",
                side_effect=OSError("database is locked"),
            ):
                notify_mod.notify("Timer done", kind="reminder", source="scheduler")
        finally:
            events.unsubscribe(seen.append)

        self.assertEqual(len(seen), 1, seen)
        self.assertEqual(seen[0]["type"], "notification")
        self.assertEqual(seen[0]["text"], "Timer done")

    def test_several_messages_arrive_as_one(self) -> None:
        """The pollers hand over a list; passing it straight through would put
        the word 'list' on the screen."""
        from unittest import mock

        from helpers import notify as notify_mod

        with mock.patch("helpers.memory_db.insert_notification") as insert:
            insert.side_effect = lambda text, kind, source: {
                "id": 1, "ts": "", "kind": kind, "source": source,
                "text": text, "acknowledged": False,
            }
            notify_mod.notify(["You have 2 new email(s).", "From: Ada"],
                              kind="alert", source="gmail")
            self.assertEqual(
                insert.call_args.args[0], "You have 2 new email(s). From: Ada"
            )

    def test_unknown_kind_falls_back_rather_than_raising(self) -> None:
        """kind reaches the UI as a style name; an unknown one must not throw
        inside a background thread."""
        from unittest import mock

        from helpers import notify as notify_mod

        with mock.patch("helpers.memory_db.insert_notification") as insert:
            insert.side_effect = lambda text, kind, source: {
                "id": 1, "ts": "", "kind": kind, "source": source,
                "text": text, "acknowledged": False,
            }
            notify_mod.notify("hello", kind="klaxon", source="test")
            self.assertEqual(insert.call_args.kwargs["kind"], "info")

    def test_empty_message_is_dropped(self) -> None:
        """An empty list from a poller that found nothing must not become a
        blank row in the notifications screen."""
        from unittest import mock

        from helpers import notify as notify_mod

        with mock.patch("helpers.memory_db.insert_notification") as insert:
            notify_mod.notify([])
            notify_mod.notify("   ")
            insert.assert_not_called()


class TestWeatherUnits(unittest.TestCase):
    def test_configured_units_reach_the_request(self) -> None:
        """modules.weather.default_units was documented as metric|imperial but
        the job hardcoded metric and a °C suffix."""
        from helpers.config import Config
        from modules import weather

        Config.load(os.path.join(_REPO_ROOT, "config.example.yaml"))
        assert Config._settings is not None
        original = Config._settings.modules.weather.default_units
        try:
            for configured, expected_units, expected_symbol in [
                ("metric", "metric", "°C"),
                ("imperial", "imperial", "°F"),
                ("nonsense", "metric", "°C"),
            ]:
                Config._settings.modules.weather.default_units = configured
                with self.subTest(configured=configured):
                    self.assertEqual(weather.units(), expected_units)
                    self.assertEqual(weather.temperature_symbol(), expected_symbol)
        finally:
            Config._settings.modules.weather.default_units = original


class TestMcpInstallGate(unittest.TestCase):
    """manage_mcp_server starts a process of the caller's choosing with the
    user's privileges. It shipped with no gate at all, while sending an email
    had one."""

    def setUp(self) -> None:
        from helpers.config import Config

        Config.load(os.path.join(_REPO_ROOT, "config.example.yaml"))
        assert Config._settings is not None
        self.settings = Config._settings

    def test_add_refuses_and_echoes_the_command(self) -> None:
        from unittest import mock

        from modules import mcp

        self.settings.modules.mcp.allow_install = False
        with mock.patch("helpers.memory_db.get_mcp_server", return_value=None), \
                mock.patch("helpers.memory_db.upsert_mcp_server") as upsert, \
                mock.patch.object(mcp, "_client") as client:
            client.return_value.all_connected.return_value = []
            result = mcp.manage_mcp_server(
                action="add", name="evil", command="curl", args='["evil.sh"]'
            )

        upsert.assert_not_called()
        self.assertIn("disabled", result)
        self.assertIn("curl evil.sh", result)

    def test_connect_is_gated_too(self) -> None:
        """Connecting spawns the same process 'add' does; gating only 'add'
        would leave a stored server one word away from running."""
        from unittest import mock

        from modules import mcp

        self.settings.modules.mcp.allow_install = False
        record = {"name": "srv", "transport": "stdio", "command": "npx", "args": "[]"}
        with mock.patch("helpers.memory_db.get_mcp_server", return_value=record), \
                mock.patch.object(mcp, "_client") as client:
            client.return_value.all_connected.return_value = []
            result = mcp.manage_mcp_server(action="connect", name="srv")
            client.return_value.connect_server.assert_not_called()

        self.assertIn("disabled", result)

    def test_disabling_a_server_stays_ungated(self) -> None:
        """The gate guards starting processes, not stopping them."""
        from unittest import mock

        from modules import mcp

        self.settings.modules.mcp.allow_install = False
        record = {"name": "srv", "transport": "stdio", "command": "npx", "args": "[]"}
        with mock.patch("helpers.memory_db.get_mcp_server", return_value=record), \
                mock.patch("helpers.memory_db.upsert_mcp_server") as upsert, \
                mock.patch.object(mcp, "_client") as client:
            client.return_value.all_connected.return_value = []
            result = mcp.manage_mcp_server(action="edit", name="srv", enabled="false")

        upsert.assert_called_once()
        self.assertIn("Updated", result)

    def test_transport_can_return_to_stdio(self) -> None:
        """The edit branch read `transport != "stdio"` while the parameter
        defaulted to "stdio", so a server moved to http could never be moved
        back."""
        from unittest import mock

        from modules import mcp

        self.settings.modules.mcp.allow_install = True
        record = {"name": "srv", "transport": "http", "url": "http://x", "args": "[]"}
        with mock.patch("helpers.memory_db.get_mcp_server", return_value=record), \
                mock.patch("helpers.memory_db.upsert_mcp_server") as upsert, \
                mock.patch.object(mcp, "_client") as client:
            client.return_value.all_connected.return_value = []
            mcp.manage_mcp_server(action="edit", name="srv", transport="stdio")

        self.assertEqual(upsert.call_args.args[0]["transport"], "stdio")


class TestGmailWriteGate(unittest.TestCase):
    def test_every_mailbox_write_checks_the_gate(self) -> None:
        """send/reply/delete checked modules.gmail.allow_write; marking read and
        the draft delete did not, so switching the gate off still let Wony
        change the mailbox. modify_emails now checks it once for every state
        change, which is why the merge was worth doing."""
        import inspect

        from modules import gmail

        for name in ("modify_emails", "send_email", "manage_drafts"):
            with self.subTest(job=name):
                source = inspect.getsource(getattr(gmail.Gmail, name))
                self.assertIn("_write_allowed", source)


class TestModuleRetry(unittest.TestCase):
    def test_a_missing_pip_package_is_retryable(self) -> None:
        """A missing package yields UNAVAILABLE, which the retry list left out —
        so `pip install` never took effect until the whole app restarted. That is
        nine of the optional modules."""
        from helpers.registry import ModuleStatus, ServiceRegistry

        original_pending = dict(ServiceRegistry._reinit_pending)
        original_status = dict(ServiceRegistry._module_status)
        try:
            ServiceRegistry._reinit_pending["fake_mod"] = {"kind": "jobs", "items": []}
            ServiceRegistry._module_status["fake_mod"] = (
                ModuleStatus.UNAVAILABLE, "pip module not installed: nope"
            )
            self.assertIn("fake_mod", ServiceRegistry.get_retryable_modules())
        finally:
            ServiceRegistry._reinit_pending.clear()
            ServiceRegistry._reinit_pending.update(original_pending)
            ServiceRegistry._module_status.clear()
            ServiceRegistry._module_status.update(original_status)

    def test_requirement_check_drops_stale_import_caches(self) -> None:
        """find_spec answers from cached directory listings, so a package
        installed into the running process stayed invisible and the retry was
        cosmetic."""
        import inspect

        from helpers import requirements

        self.assertIn("invalidate_caches", inspect.getsource(requirements.evaluate))


class TestMcpLiveness(unittest.TestCase):
    def test_a_dead_session_is_not_reported_as_connected(self) -> None:
        """When a server's coroutine unwound, the session stayed in _sessions:
        all_connected() kept listing it while every tool call raised "is not
        connected"."""
        from helpers import mcp_client

        alive = mcp_client.MCPServerSession("alive", {})
        dead = mcp_client.MCPServerSession("dead", {})
        dead._closed.set()

        original = dict(mcp_client._sessions)
        try:
            mcp_client._sessions.clear()
            mcp_client._sessions.update({"alive": alive, "dead": dead})
            self.assertEqual(mcp_client.all_connected(), ["alive"])
        finally:
            mcp_client._sessions.clear()
            mcp_client._sessions.update(original)


class TestMissedReminders(unittest.TestCase):
    def test_a_missed_timer_still_runs_its_action(self) -> None:
        """Restoring a due timer built a 3-tuple of (id, label, time) and deleted
        the row, so the action was destroyed before anything could run it: "turn
        the lights off at 23:00" did nothing at all if the PC had been asleep."""
        from unittest import mock

        from modules.scheduler import Scheduler

        sched = Scheduler.__new__(Scheduler)
        sched._reminders = {}
        due = datetime.datetime.now() - datetime.timedelta(minutes=5)
        meta = {
            "id": "abc",
            "text": "lights off",
            "trigger_type": "date",
            "action": {"job": "control_home_device", "args": {"target": "lamp"}},
        }

        with mock.patch.object(Scheduler, "_run_action") as run_action, \
                mock.patch("helpers.notify.notify"), \
                mock.patch("helpers.memory_db.delete_reminder"):
            sched._fire_missed_reminder(meta, due)

        run_action.assert_called_once_with(meta["action"])

    def test_a_long_stale_action_asks_instead_of_acting(self) -> None:
        """Running "lights off" ten hours late is a surprise, not a service."""
        from unittest import mock

        from modules.scheduler import Scheduler

        sched = Scheduler.__new__(Scheduler)
        sched._reminders = {}
        due = datetime.datetime.now() - datetime.timedelta(hours=10)
        meta = {
            "id": "abc",
            "text": "lights off",
            "trigger_type": "date",
            "action": {"job": "control_home_device", "args": {}},
        }

        with mock.patch.object(Scheduler, "_run_action") as run_action, \
                mock.patch("modules.scheduler.notify") as notify, \
                mock.patch("helpers.memory_db.delete_reminder"):
            sched._fire_missed_reminder(meta, due)

        run_action.assert_not_called()
        self.assertIn("Want me to do it now?", notify.call_args.args[0])


class TestSpotifyTokenPersistence(unittest.TestCase):
    def test_a_refreshed_token_is_written_back(self) -> None:
        """_refresh_access_token updated only the in-memory token, so the cached
        expiry stayed permanently in the past and every process start burned a
        refresh round-trip."""
        import inspect

        from modules import spotify

        source = inspect.getsource(spotify.Spotify._refresh_access_token)
        self.assertIn("_save_tokens", source)


class TestCalendarAmbiguity(unittest.TestCase):
    def test_edit_refuses_an_ambiguous_match_like_delete_does(self) -> None:
        """delete_event guarded on len(events) > 1; edit_event took events[0], so
        "move the standup" rewrote whichever standup came back first."""
        import inspect

        from modules import calendar as cal

        for name in ("_edit_event", "_delete_event"):
            with self.subTest(job=name):
                self.assertIn(
                    "_resolve_one_event",
                    inspect.getsource(getattr(cal.Calendar, name)),
                )

    def test_the_resolver_reports_both_failures(self) -> None:
        from unittest import mock

        from modules import calendar as cal

        service = cal.Calendar.__new__(cal.Calendar)
        two = [{"id": "1", "summary": "standup"}, {"id": "2", "summary": "standup"}]
        with mock.patch.object(cal.Calendar, "_parse_date", return_value=None), \
                mock.patch.object(cal.Calendar, "_fetch_events_range", return_value=two):
            event, problem = service._resolve_one_event("standup", "", "primary")
        self.assertIsNone(event)
        self.assertIn("Be more specific", problem)

        with mock.patch.object(cal.Calendar, "_parse_date", return_value=None), \
                mock.patch.object(cal.Calendar, "_fetch_events_range", return_value=[]):
            event, problem = service._resolve_one_event("standup", "", "primary")
        self.assertIsNone(event)
        self.assertEqual(problem, "No matching event found.")


class TestRecallLimit(unittest.TestCase):
    def test_a_day_lookup_honours_the_limit(self) -> None:
        """recall(date=...) accepted a limit and then ignored it, so "what did we
        talk about on Tuesday" returned every exchange of that day."""
        import inspect

        from helpers import memory_db

        self.assertIn("limit", inspect.signature(memory_db.turns_on_date).parameters)
        self.assertIn("turns_on_date(date, limit=", inspect.getsource(__import__(
            "modules.ai", fromlist=["AI"]).AI.recall))


class TestTavilyFallbackIsVisible(unittest.TestCase):
    def test_a_failed_tavily_search_is_reported(self) -> None:
        """The fallback to DuckDuckGo swallowed the exception, so a bad
        TAVILY_API_KEY looked exactly like a working one."""
        from unittest import mock

        from modules import web

        with mock.patch.dict(os.environ, {"TAVILY_API_KEY": "bad"}), \
                mock.patch.object(web, "_tavily_search", side_effect=RuntimeError("401")), \
                mock.patch.object(web, "_ddg_search", return_value=[]) as ddg, \
                mock.patch("helpers.diagnostics.add") as diag:
            web._do_search("anything")

        ddg.assert_called_once()
        self.assertTrue(
            any("Tavily" in str(call) for call in diag.call_args_list), diag.call_args_list
        )


class TestOneTurnPath(unittest.TestCase):
    """The agent turn existed twice — helpers/web_app._run_web_turn and
    modules/employer.job_on_command — with comments cross-referencing each
    other and two different timeouts."""

    def test_every_entry_point_goes_through_run_turn(self) -> None:
        import inspect

        from helpers import kiosk, web_app
        from modules.employer import Employer

        self.assertIn("run_turn", inspect.getsource(Employer.job_on_command))
        self.assertIn("run_turn", inspect.getsource(web_app.build_app))
        self.assertIn("run_turn", inspect.getsource(kiosk))

    def test_a_failed_turn_comes_back_as_a_sentence(self) -> None:
        """run_turn never raises: a caller that only wants something to show
        the user must not have to catch."""
        from unittest import mock

        from helpers.turn import run_turn

        with mock.patch("helpers.agent.run_agent", side_effect=RuntimeError("boom")), \
                mock.patch("helpers.bootstrap.get_ai_client", return_value=None), \
                mock.patch("modules.ai.build_agent_system_prompt", return_value=""), \
                mock.patch("helpers.diagnostics.add"), \
                mock.patch("helpers.conversation.Conversation.get_messages", return_value=[]):
            result = run_turn("anything")

        self.assertTrue(result.error)
        self.assertIn("boom", result.text)
        self.assertEqual(result.calls, [])


class TestModuleNameDrift(unittest.TestCase):
    def test_every_module_name_is_a_module_a_user_can_see(self) -> None:
        """helpers/settings.MODULES had 14 entries against 18 files in modules/.
        The four absentees survived only because their jobs passed
        module_name=None — a load-bearing accident that left them with a blank
        badge in `what can you do` and in the web UI."""
        from helpers.config import ALWAYS_ON
        from helpers.registry import ServiceRegistry
        from helpers.settings import MODULES

        import modules  # noqa: F401  (import triggers discover_services)

        known = {key for key, _, _ in MODULES} | set(ALWAYS_ON)

        used = {
            module for module in ServiceRegistry.get_job_modules().values()
            # MCP tools are namespaced per server, not per modules/ file.
            if module and not module.startswith("mcp:")
        }
        self.assertFalse(
            used - known,
            "Jobs name modules nothing offers: " + ", ".join(sorted(used - known)),
        )

    def test_every_offered_module_has_a_file(self) -> None:
        from helpers.config import ALWAYS_ON
        from helpers.settings import MODULES

        for name in {key for key, _, _ in MODULES} | set(ALWAYS_ON):
            with self.subTest(module=name):
                self.assertTrue(
                    os.path.exists(os.path.join(_REPO_ROOT, "modules", f"{name}.py")),
                    f"'{name}' is offered but has no modules/{name}.py.",
                )

    def test_always_on_modules_are_enabled_whatever_the_config_says(self) -> None:
        from helpers.config import ALWAYS_ON, Config

        Config.load(os.path.join(_REPO_ROOT, "config.example.yaml"))
        assert Config._settings is not None
        original = list(Config._settings.enabled_modules)
        try:
            Config._settings.enabled_modules = []
            for name in ALWAYS_ON:
                with self.subTest(module=name):
                    self.assertTrue(Config.is_module_enabled(name))
        finally:
            Config._settings.enabled_modules = original


class TestConfirmGate(unittest.TestCase):
    """`_DESTRUCTIVE_JOBS` was a hand-kept set of bare strings in web_app that
    nothing validated (it still listed "wipe_data", which is an endpoint, not a
    job), it only reached the UI, and the voice path — the one where a
    misrecognition picks the wrong recipient — had no confirmation at all."""

    def setUp(self) -> None:
        from helpers import confirm

        confirm.reset()

    def test_every_confirming_name_is_a_real_job(self) -> None:
        from helpers.registry import ServiceRegistry

        import modules  # noqa: F401

        jobs = ServiceRegistry.get_all_jobs()
        confirming = {n for n, v in ServiceRegistry.get_job_confirms().items() if v}
        # Only the modules this environment could load are registered, so check
        # the ones that are here rather than demanding the full set.
        self.assertTrue(confirming, "no job declares confirms=")
        for name in confirming:
            with self.subTest(job=name):
                self.assertIn(name, jobs)

    def test_a_confirming_job_is_refused_until_a_later_turn(self) -> None:
        """A model that just retries in the same turn must not be able to
        confirm on the user's behalf — that is the whole gate."""
        from unittest import mock

        from helpers import confirm

        with mock.patch(
            "helpers.registry.ServiceRegistry.get_job_confirms",
            return_value={"delete_it": True},
        ):
            confirm.begin_turn()
            first = confirm.check("delete_it", {"what": "everything"})
            self.assertIsNotNone(first)
            # Same turn: still refused.
            self.assertIsNotNone(confirm.check("delete_it", {"what": "everything"}))

            confirm.begin_turn()
            self.assertIsNone(confirm.check("delete_it", {"what": "everything"}))
            # And the confirmation is spent, not standing.
            self.assertIsNotNone(confirm.check("delete_it", {"what": "everything"}))

    def test_confirming_one_call_does_not_confirm_another(self) -> None:
        from unittest import mock

        from helpers import confirm

        with mock.patch(
            "helpers.registry.ServiceRegistry.get_job_confirms",
            return_value={"delete_it": True},
        ):
            confirm.begin_turn()
            confirm.check("delete_it", {"what": "one email"})
            confirm.begin_turn()
            self.assertIsNotNone(confirm.check("delete_it", {"what": "everything"}))

    def test_a_read_only_action_is_not_gated(self) -> None:
        """The merged jobs default to a read action — listing drafts must not
        make the user confirm a question."""
        from unittest import mock

        from helpers import confirm

        with mock.patch(
            "helpers.registry.ServiceRegistry.get_job_confirms",
            return_value={"manage_drafts": {"delete"}},
        ):
            confirm.begin_turn()
            self.assertIsNone(confirm.check("manage_drafts", {"action": "list"}))
            self.assertIsNotNone(confirm.check("manage_drafts", {"action": "delete"}))


class TestFrontendJobNames(unittest.TestCase):
    def test_every_job_the_web_ui_calls_still_exists(self) -> None:
        """The Tier 2 merges renamed jobs and swept the Python, the docs and the
        config — but not the front end. The screens went on calling
        cancel_reminder, set_like and four *_google_account jobs, and
        /api/invoke answers an unknown name with a message the tap drops on the
        floor."""
        import re

        ui = os.path.join(_REPO_ROOT, "kiosk", "src")
        if not os.path.isdir(ui):
            self.skipTest("kiosk/src is not present")

        defined = set()
        modules_dir = os.path.join(_REPO_ROOT, "modules")
        for entry in os.listdir(modules_dir):
            if not entry.endswith(".py"):
                continue
            with open(os.path.join(modules_dir, entry), encoding="utf-8") as handle:
                defined.update(re.findall(r"^\s*def (\w+)\(", handle.read(), re.MULTILINE))

        called = set()
        for folder, _dirs, files in os.walk(ui):
            for name in files:
                if not name.endswith((".ts", ".tsx")):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as handle:
                    called.update(re.findall(r"invokeJob\(\s*'([\w]+)'", handle.read()))

        self.assertTrue(called, "no invokeJob call sites found — did the pattern change?")
        self.assertFalse(
            called - defined,
            "The touch UI calls jobs that no longer exist: "
            + ", ".join(sorted(called - defined)),
        )


class TestNotes(unittest.TestCase):
    def setUp(self) -> None:
        from helpers import memory_db

        self._list = f"test_{os.getpid()}"
        memory_db.clear_notes(self._list)
        self.addCleanup(memory_db.clear_notes, self._list)

    def test_an_item_is_removed_by_part_of_its_wording(self) -> None:
        """The item was dictated ('two pints of milk') and is ticked off by
        whatever it is called now ('milk')."""
        from modules import notes

        notes.note("add", "two pints of milk", self._list)
        self.assertIn("two pints of milk", notes.note("remove", "milk", self._list))
        self.assertIn("empty", notes.note("list", "", self._list))

    def test_commas_add_several_items(self) -> None:
        from modules import notes

        notes.note("add", "milk, eggs, bread", self._list)
        self.assertIn("3 item", notes.note("list", "", self._list))

    def test_lists_do_not_leak_into_each_other(self) -> None:
        from helpers import memory_db
        from modules import notes

        other = self._list + "_other"
        self.addCleanup(memory_db.clear_notes, other)
        notes.note("add", "milk", self._list)
        self.assertIn("empty", notes.note("list", "", other))


class TestWeatherForecast(unittest.TestCase):
    def test_days_are_grouped_by_the_city_s_own_clock(self) -> None:
        """The API answers in UTC. Grouping on that would file a 23:00 reading
        under tomorrow for anyone east of Greenwich."""
        from modules.weather import _group_by_day

        # 2022-08-30 22:30 UTC — already the 31st in a +02:00 city.
        data = {
            "city": {"name": "Zocca", "timezone": 7200},
            "list": [
                {"dt": 1661898600, "main": {"temp": 12.0},
                 "weather": [{"description": "clear sky"}]},
            ],
        }
        days = _group_by_day(data)
        self.assertEqual([d["date"] for d in days], ["2022-08-31"])

    def test_sunrise_reads_in_the_reported_city_s_clock(self) -> None:
        """Rendered against the machine's timezone, Tokyo's sunrise came back
        as 22:15 — a plausible-looking time, which is why nobody noticed."""
        from modules.weather import _sun_line

        # 2022-08-30 20:15 UTC = 05:15 in Tokyo (+09:00).
        line = _sun_line({"sunrise": 1661890500, "sunset": 1661936640,
                          "utc_offset": 9 * 3600})
        self.assertIn("Sunrise 05:15", line)

    def test_a_named_city_is_reported_by_the_name_that_was_asked_for(self) -> None:
        """OpenWeatherMap answers with its nearest reporting station, which for
        Tokyo is 'Japan'. Right for an IP guess, wrong for a request."""
        from unittest import mock

        from modules import weather

        with mock.patch.dict(os.environ, {"WEATHER_API_KEY": "x"}), \
                mock.patch.object(weather, "_get_coordinates_for_city_name",
                                  return_value=(35.6, 139.7)), \
                mock.patch.object(weather, "_get_weather_for_coordinates",
                                  return_value={"name": "Japan", "main": {"temp": 21},
                                                "weather": [{"description": "rain"}]}):
            self.assertEqual(weather.snapshot("Tokyo")["city"], "Tokyo")

    def test_the_headline_comes_from_the_middle_of_the_day(self) -> None:
        from modules.weather import _group_by_day

        data = {
            "city": {"name": "Zocca", "timezone": 0},
            "list": [
                # 03:00 and 12:00 on the same day.
                {"dt": 1661828400, "main": {"temp": 5.0},
                 "weather": [{"description": "night fog"}]},
                {"dt": 1661860800, "main": {"temp": 20.0},
                 "weather": [{"description": "sunny"}]},
            ],
        }
        day = _group_by_day(data)[0]
        self.assertEqual(day["description"], "sunny")
        self.assertEqual((day["low"], day["high"]), (5, 20))


class TestTriggers(unittest.TestCase):
    def setUp(self) -> None:
        from helpers import triggers

        triggers._last_polled.clear()
        triggers._last_fired.clear()
        triggers._last_fact.clear()
        triggers._last_any_fire = 0.0

    def test_nothing_fires_while_proactive_mode_is_off(self) -> None:
        """The whole feature ships off; a trigger that fired anyway would be
        the assistant talking without being asked."""
        from unittest import mock

        from helpers import triggers

        with mock.patch.object(triggers, "enabled", return_value=False), \
                mock.patch.object(triggers, "_fire") as fire:
            triggers._tick()
        fire.assert_not_called()

    def test_nothing_fires_mid_turn(self) -> None:
        from unittest import mock

        from helpers import triggers

        loud = triggers.Trigger("loud", "always", lambda: "something", 0.0, 0.0)
        with mock.patch.object(triggers, "enabled", return_value=True), \
                mock.patch.object(triggers, "_TRIGGERS", [loud]), \
                mock.patch.object(triggers, "_fire") as fire:
            from helpers.decorators import agent_lock

            with agent_lock:
                triggers._tick()
            fire.assert_not_called()
            triggers._tick()
        fire.assert_called_once()

    def test_the_same_fact_is_not_announced_twice(self) -> None:
        """A battery sitting at 12% would otherwise re-announce itself every
        time its cooldown expired."""
        from unittest import mock

        from helpers import triggers

        loud = triggers.Trigger("loud", "always", lambda: "battery at 12%", 0.0, 0.0)
        with mock.patch.object(triggers, "enabled", return_value=True), \
                mock.patch.object(triggers, "_TRIGGERS", [loud]), \
                mock.patch.object(triggers, "_MIN_GAP_SECONDS", 0.0), \
                mock.patch.object(triggers, "_fire") as fire:
            triggers._tick()
            triggers._last_fact["loud"] = "battery at 12%"
            triggers._tick()
        fire.assert_called_once()

    def test_every_trigger_is_reachable_by_name(self) -> None:
        from helpers import triggers

        for trigger in triggers.all_triggers():
            with self.subTest(trigger=trigger.name):
                triggers.set_enabled(trigger.name, False)
                self.assertFalse(triggers.is_on(trigger.name))
                triggers.set_enabled(trigger.name, True)
                self.assertTrue(triggers.is_on(trigger.name))


class TestHomeAssistantIndexCache(unittest.TestCase):
    def test_a_service_call_drops_the_cached_states(self) -> None:
        """The index carries live values — a light's brightness, a lock's
        state. Reading one back from before the change is the fabricated-value
        bug the system prompt spends a paragraph forbidding."""
        from modules import home_assistant

        home_assistant._index.entities = ["stale"]
        home_assistant._index.stamp = 10 ** 9
        home_assistant._invalidate_index()
        self.assertEqual(home_assistant._index.entities, [])


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
