"""TUI menu integration with real Urwid rendering and local JSON storage."""

from contextlib import contextmanager
import copy
import json
import signal
from pathlib import Path
import threading
import time
import types
import unittest
from unittest.mock import patch

import urwid

import test_session_cli as session_tests
from test_session_cli import FakeInteractor, main
from echoai import app as app_module
from echoai.app import MadlineApp
from echoai.tools import task_manager


class TestAI(FakeInteractor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.models = ["openai:gpt-4o", "ollama:local"]
        self.functions = [{"function": {"name": "example", "description": "Example tool", "disabled": False}}]
        self.fail = False

    def list_models(self, refresh=False):
        return self.models

    def list_functions(self):
        return copy.deepcopy(self.functions)

    def add_function(self, func, name=None, **kwargs):
        self.functions.append({"function": {"name": name or func.__name__, "description": "Memory tool"}})

    def enable_function(self, name):
        next(f["function"] for f in self.functions if f["function"]["name"] == name)["disabled"] = False
        return True

    def disable_function(self, name):
        next(f["function"] for f in self.functions if f["function"]["name"] == name)["disabled"] = True
        return True

    def messages_system(self, prompt):
        self.system = prompt

    def messages_add(self, role, content):
        self.history.append({"role": role, "content": content})

    @contextmanager
    def response_stream(self):
        if self.fail:
            raise RuntimeError("Provider unavailable")
        yield iter(["Hello", " world"])

    def interact(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        if kwargs.get("raw"):
            return self.response_stream()
        if self.fail:
            raise RuntimeError("Provider unavailable")
        return "Complete response"


class FakeMemory:
    def __init__(self, **kwargs):
        self.records = []

    def create(self, text):
        self.records.append(text)
        return "Memory successfully updated."

    def add(self, text):
        self.records.append(text)

    def search(self, query, limit=5):
        return {"results": [{"content": text, "score": 1} for text in self.records[:limit]]}


class AppTests(unittest.TestCase):
    def setUp(self):
        self.fixture = session_tests.SessionCLITests("test_startup_keeps_session_lookup")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.bot = self.fixture.bot
        self.bot.ai = TestAI(session_path=self.bot.session_directory)
        self.bot.display = types.MethodType(main.Chatbot.display, self.bot)
        patch.object(main, "print", self.bot.console.print).start()
        patch.object(main, "Memory", FakeMemory).start()
        patch.object(task_manager, "TASK_FILE", str(Path(self.fixture.temp.name) / "tasks.json")).start()
        self.app = MadlineApp(chatbot=self.bot)

    def drain(self):
        worker = self.app.worker
        if worker:
            worker.join(3)
            self.assertFalse(worker.is_alive(), "Background operation did not finish")
        self.app._poll_work()
        self.assertFalse(self.app.busy)

    def text(self):
        return "\n".join(widget.text for widget in self.app.message_log.walker)

    def render(self, width=100, height=30):
        canvas = self.app.loop.widget.render((width, height), focus=True)
        self.assertEqual(canvas.rows(), height)
        self.assertEqual(canvas.cols(), width)
        return canvas

    def action(self, label):
        panel = self.app.overlay
        # Panel exposes its action buttons through the Pile's footer.
        pile = panel._w.base_widget
        columns = pile.contents[-1][0]
        for widget, _ in columns.contents:
            button = widget.base_widget
            if button.get_label() == label:
                button._emit("click")
                return
        raise AssertionError(f"No {label} button")

    def test_every_left_menu_button_opens_real_panel_and_renders(self):
        self.render()
        for index, (label, _) in enumerate(self.app.MENU):
            with self.subTest(menu=label):
                self.app.menu_items[index].base_widget._emit("click")
                if self.app.busy:
                    self.drain()
                self.assertIsNotNone(self.app.overlay)
                self.render()
                self.render(70, 24)
                self.app.close_overlay(cancel=True)
        self.assertNotIn("dummy", self.text())
        self.assertNotIn("deck", self.text().lower())

    def test_model_selection_is_saved_and_used_by_next_message(self):
        self.app.show_model_selector()
        self.drain()
        panel = self.app.overlay
        panel.select("ollama:local")
        self.assertEqual(self.app.CONFIG["model"], "ollama:local")
        self.assertEqual(json.loads(self.bot.CONFIG_PATH.read_text())["model"], "ollama:local")
        self.app.process_user_input("Hello")
        self.drain()
        self.assertEqual(self.bot.ai.calls[-1][1]["model"], "ollama:local")
        self.assertIn("Hello world", self.text())

    def test_prompt_save_and_settings_dictionary_stay_in_sync(self):
        old_config = self.app.CONFIG
        self.app.show_prompt_manager()
        self.app.overlay.fields["system_prompt"].set_edit_text("Answer concisely.")
        self.app.overlay._save()
        self.assertIs(self.app.CONFIG, self.bot.config)
        self.assertIsNot(old_config, self.app.CONFIG)
        self.assertEqual(self.app.CONFIG["system_prompt"], "Answer concisely.")
        self.app.process_user_input("Hi")
        self.drain()
        self.assertEqual(self.bot.ai.system, "Answer concisely.")

    def test_settings_form_saves_booleans_and_nonstream_responses(self):
        self.app.show_settings()
        panel = self.app.overlay
        panel.fields["stream"].set_state(False)
        panel.fields["tools"].set_state(False)
        panel.fields["username"].set_edit_text("Tester")
        panel._save()
        self.assertFalse(self.app.CONFIG["stream"])
        self.app.process_user_input("> preserve this markdown")
        self.drain()
        prompt, options = self.bot.ai.calls[-1]
        self.assertEqual(prompt, "> preserve this markdown")
        self.assertFalse(options["raw"])
        self.assertFalse(options["stream"])
        self.assertFalse(options["tools"])
        self.assertIn("Complete response", self.text())

    def test_invalid_settings_are_rejected_before_saving(self):
        before = self.bot.CONFIG_PATH.read_text()
        self.app.show_settings()
        self.app.overlay.fields["model"].set_edit_text("invalid")
        self.app.overlay.invoke(self.app.overlay._save)
        self.assertIn("provider:model", self.app.overlay.status.text)
        self.assertEqual(self.bot.CONFIG_PATH.read_text(), before)
        self.app.handle_command("/settings stream invalid")
        self.assertIn("true or false", self.text())

    def test_memory_enable_remember_recall_disable(self):
        self.app.show_memory_manager()
        self.app.overlay.editor.set_edit_text("Remembered example")
        self.action("Remember")
        self.assertIn("Enable memory", self.app.overlay.status.text)
        self.action("Enable")
        self.drain()
        self.assertIs(self.app.MEMORY, self.bot.memory)
        self.assertTrue(self.bot.memory_enabled)
        self.assertTrue(json.loads(self.bot.CONFIG_PATH.read_text())["memory"])
        self.app.show_memory_manager()
        self.app.overlay.editor.set_edit_text("Remembered example")
        self.action("Remember")
        self.drain()
        self.assertIn("Remembered example", self.bot.memory.records)
        self.action("Recall")
        self.drain()
        self.assertIn("Memory Search Results", self.text())
        self.action("Disable")
        self.assertFalse(self.bot.memory_enabled)
        self.app.handle_command("/remember disabled")
        self.drain()
        self.assertIn("Memory is disabled", self.text())

    def test_memory_startup_failure_keeps_old_config_and_reports_error(self):
        before = self.bot.CONFIG_PATH.read_text()
        class BrokenMemory(FakeMemory):
            def __init__(self, **kwargs):
                raise RuntimeError("Cannot load embeddings")
        with patch.object(main, "Memory", BrokenMemory):
            self.app.handle_command("/settings memory true")
            self.drain()
        self.assertEqual(self.bot.CONFIG_PATH.read_text(), before)
        self.assertFalse(self.bot.config["memory"])
        self.assertIn("Cannot load embeddings", self.text())

    def test_tools_panel_updates_same_functions_as_cli(self):
        self.app.show_tool_manager()
        panel = self.app.overlay
        panel.fields["example"].set_state(False)
        panel.global_enabled.set_state(False)
        self.action("Apply")
        self.assertTrue(self.bot.ai.functions[0]["function"]["disabled"])
        self.assertFalse(self.app.CONFIG["tools"])
        self.app.handle_command("/tools example true")
        self.assertFalse(self.bot.ai.functions[0]["function"]["disabled"])
        self.app.handle_command("/tools")
        self.assertIn("Available Tools", self.text())

    def test_theme_preview_cancel_and_save(self):
        original = self.app.CONFIG["theme"]
        self.app.show_theme_manager()
        panel = self.app.overlay
        panel.preview("dark")
        self.assertEqual(self.app.theme_manager.get_current_theme_name(), "dark")
        self.app.close_overlay(cancel=True)
        self.assertEqual(self.app.theme_manager.get_current_theme_name(), original)
        self.assertEqual(self.app.CONFIG["theme"], original)
        self.app.show_theme_manager()
        self.app.overlay.select("forest")
        self.assertEqual(self.app.CONFIG["theme"], "forest")
        self.assertEqual(json.loads(self.bot.CONFIG_PATH.read_text())["theme"], "forest")
        for name, *_ in self.app.theme_manager.get_urwid_palette():
            self.assertIsInstance(name, str)

    def test_file_selection_attaches_contents_to_draft_without_sending(self):
        path = Path(self.fixture.temp.name) / "file with spaces.txt"
        path.write_text("File contents")
        self.app.edit.set_edit_text("Review this")
        self.app.show_file_explorer(start_path=path.parent)
        with patch.object(main, "extract_text", side_effect=lambda path: Path(path).read_text()):
            self.app.overlay.open(path)
            self.drain()
        self.assertIn("Review this", self.app.edit.edit_text)
        self.assertIn("File contents", self.app.edit.edit_text)
        self.assertEqual(self.bot.ai.calls, [])
        self.assertIsNone(self.app.overlay)

    def test_missing_file_keeps_draft(self):
        self.app.edit.set_edit_text("Keep draft")
        self.app.handle_command('/file "missing file"')
        self.assertEqual(self.app.edit.edit_text, "Keep draft")
        self.assertIn("File not found", self.text())

    def test_sessions_embed_and_use_cli_lookup_without_nested_loop(self):
        sid = self.fixture.existing_id
        self.fixture.store.msg_insert(sid, {"role": "user", "content": "Saved conversation"})
        self.app.show_session_manager()
        panel = self.app.overlay
        panel.keypress((90, 24), "enter")
        self.assertEqual(self.app.AI.session_id, sid)
        self.assertIsNone(self.app.overlay)
        self.assertIn("Saved conversation", self.text())
        self.app.handle_command('/session rename "Project notes" Renamed')
        self.assertEqual(self.fixture.store.load_full(sid)["name"], "Renamed")
        self.app.handle_command("/session show")
        self.assertIn("Session Details", self.text())
        self.app.handle_command("/incognito")
        self.assertIsNone(self.app.AI.session_id)
        self.app.handle_command("/session tui")
        self.assertIsNotNone(self.app.overlay)

    def test_tasks_use_shared_cli_store_and_embed_browser(self):
        self.app.handle_command("/task add A shared task")
        tasks = task_manager.task_list()["result"]
        self.assertEqual(tasks[0]["content"], "A shared task")
        self.app.show_task_manager()
        panel = self.app.overlay
        self.assertEqual(panel.controller.tasks[0]["id"], tasks[0]["id"])
        panel.keypress((90, 24), "m")
        self.assertEqual(task_manager.task_list()["result"][0]["status"], "done")
        panel.keypress((90, 24), "esc")
        self.assertIsNone(self.app.overlay)
        self.app.handle_command("/task list")
        self.assertIn("A shared task", self.text())

    def test_model_search_no_results_and_reset(self):
        self.app.show_model_selector()
        self.drain()
        panel = self.app.overlay
        panel.query.set_edit_text("missing")
        self.assertEqual(panel.filtered, [])
        self.render()
        panel.keypress((90, 24), "down")
        panel.query.set_edit_text("")
        self.assertEqual(len(panel.filtered), 2)
        self.render()

    def test_background_failure_does_not_stick_busy_or_mutate_widgets_off_thread(self):
        main_thread = threading.get_ident()
        threads = []
        original = self.app.message_log.update_stream
        def record(text):
            threads.append(threading.get_ident())
            original(text)
        self.app.message_log.update_stream = record
        self.app.process_user_input("Hi")
        self.drain()
        self.assertTrue(threads)
        self.assertEqual(set(threads), {main_thread})
        self.bot.ai.fail = True
        self.app.process_user_input("Fail")
        self.drain()
        self.assertIn("Provider unavailable", self.text())
        self.assertIsNone(self.app.message_log.current_stream_message)

    def test_busy_prevents_overlapping_model_and_settings_changes(self):
        release = threading.Event()
        self.app._background(lambda: release.wait(2))
        self.app.handle_command("/settings model ollama:local")
        self.app.process_user_input("Second request")
        self.assertEqual(self.app.CONFIG["model"], "openai:gpt-4o")
        self.assertEqual(self.bot.ai.calls, [])
        release.set()
        self.drain()

    def test_keyboard_submit_history_help_menu_and_exit(self):
        self.app.edit.set_edit_text("Hello")
        self.app.handle_key("esc")
        self.app.handle_key("enter")
        self.drain()
        self.assertEqual(self.bot.ai.calls[-1][0], "Hello")
        self.app.handle_key("ctrl p")
        self.assertEqual(self.app.edit.edit_text, "Hello")
        self.app.handle_key("ctrl n")
        self.assertEqual(self.app.edit.edit_text, "")
        self.app.handle_key("f1")
        self.render()
        self.app.overlay.keypress((90, 24), "esc")
        self.app.handle_key("f2")
        self.render()
        self.app.close_overlay(cancel=True)
        with self.assertRaises(urwid.ExitMainLoop):
            self.app.handle_command("/exit")

    def test_unknown_command_does_not_reach_provider(self):
        self.app.handle_command("/missing")
        self.assertIn("Unknown command", self.text())
        self.assertEqual(self.bot.ai.calls, [])

    def test_cli_registry_and_read_only_commands_are_available(self):
        self.assertTrue(set(self.bot.command_registry) <= set(self.app.command_registry))
        for command, expected in [("/show_model", "openai:gpt-4o"), ("/show_system", "System Prompt"),
                                  ("/tokens", "42"), ("/history", "No chat history"),
                                  ("/settings", "Current Configuration Settings"),
                                  ("/session", "Saved Sessions")]:
            with self.subTest(command=command):
                self.app.handle_command(command)
                self.assertIn(expected, self.text())
        self.assertEqual(self.bot.ai.calls, [])

    def test_inline_file_references_share_cli_extraction_and_quoted_paths(self):
        path = Path(self.fixture.temp.name) / "quoted file.txt"
        path.write_text("Inline file data")
        with patch.object(main, "extract_text", side_effect=lambda path: Path(path).read_text()):
            source = f'Review /file "{path}" please'
            expected = self.bot.replace_file_references(source, interactive=False)
            self.app.process_user_input(source)
            self.drain()
        self.assertIn("Inline file data", expected)
        self.assertEqual(self.bot.ai.calls[-1][0], expected)
        self.app.process_user_input("Missing /file not-there.txt")
        self.drain()
        self.assertIn("Choose an existing file", self.text())
        self.assertEqual(len(self.bot.ai.calls), 1)

    def test_form_keyboard_navigation_and_save(self):
        self.app.show_settings()
        panel = self.app.overlay
        selected = [index for index, widget in enumerate(panel.walker) if widget.selectable()]
        for _ in range(len(selected) + 1):
            panel.keypress((90, 24), "tab")
        self.render()
        panel.fields["username"].set_edit_text("Keyboard user")
        panel.keypress((90, 24), "ctrl s")
        self.assertEqual(self.app.CONFIG["username"], "Keyboard user")
        self.assertIsNone(self.app.overlay)

    def test_search_field_accepts_slashes_and_empty_choice_list(self):
        from echoai.tui.panels import ChoicePanel
        panel = ChoicePanel("Empty", [], lambda _: self.fail("No selection expected"), self.app.close_overlay)
        self.app.show_overlay(panel)
        panel.keypress((90, 24), "/")
        for key in ("a", "/", "b"):
            panel.keypress((90, 24), key)
        self.assertEqual(panel.query.edit_text, "a/b")
        self.render()

    def test_cancel_prompt_keeps_config_and_saved_theme_is_used_at_startup(self):
        before = self.bot.CONFIG_PATH.read_text()
        self.app.show_prompt_manager()
        self.app.overlay.fields["system_prompt"].set_edit_text("Discard me")
        self.app.overlay.keypress((90, 24), "esc")
        self.assertEqual(self.bot.CONFIG_PATH.read_text(), before)
        self.app.handle_command("/settings theme dark")
        restarted = MadlineApp(chatbot=self.bot)
        self.assertEqual(restarted.theme_manager.get_current_theme_name(), "dark")
        restarted.loop.widget.render((100, 30))

    def test_markdown_setting_changes_final_response_presentation(self):
        @contextmanager
        def stream():
            yield iter(["**Bold** response"])
        self.bot.ai.response_stream = stream
        self.app.process_user_input("Markdown")
        self.drain()
        self.assertIn("Bold response", self.text())
        self.assertNotIn("**Bold**", self.text())
        self.app.handle_command("/settings markdown false")
        self.app.process_user_input("Plain text")
        self.drain()
        self.assertIn("**Bold** response", self.text())

    def test_captured_rich_colors_do_not_leak_escape_sequences(self):
        from rich.console import Console
        self.bot.console = Console(force_terminal=True, color_system="truecolor")
        with patch.object(main, "print", self.bot.console.print):
            self.app.handle_command("/tokens")
        self.assertIn("42", self.text())
        self.assertNotIn("\x1b", self.text())

    def test_busy_form_save_is_rejected_and_closed_panel_does_not_pop_another(self):
        release = threading.Event()
        self.app.show_settings()
        panel = self.app.overlay
        self.app._background(lambda: release.wait(2))
        panel.fields["username"].set_edit_text("Should not save")
        panel.invoke(panel._save)
        self.assertIn("Wait for", panel.status.text)
        self.assertEqual(self.app.CONFIG["username"], "User")
        release.set()
        self.drain()

    def test_controller_store_error_is_reported_without_crashing_tui(self):
        self.app.show_session_manager()
        controller = self.app.overlay.controller
        with patch.object(controller, "handle_input", side_effect=OSError("Store unavailable")):
            # The loop retains a bound method; patch the bound entry point too.
            with patch.object(controller.loop, "unhandled_input", side_effect=OSError("Store unavailable")):
                self.app.overlay.keypress((90, 24), "r")
        self.assertIn("Store unavailable", controller.footer_text.text)
        self.render()

    def test_sigint_exits_cleanly_and_restores_previous_handler(self):
        previous = signal.getsignal(signal.SIGINT)
        def interrupted():
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
        with patch.object(self.app.loop, "run", side_effect=interrupted):
            self.app.run()
        self.assertIs(signal.getsignal(signal.SIGINT), previous)

    def test_direct_model_prompt_theme_commands_match_cli(self):
        for command, key, value in [("models ollama:local", "model", "ollama:local"),
                                    ("system Shared prompt", "system_prompt", "Shared prompt"),
                                    ("theme night", "theme", "night")]:
            self.bot.handle_command("/" + command)
            self.assertEqual(self.bot.config[key], value)
            self.app.handle_command("/" + command)
            self.assertEqual(self.app.CONFIG[key], value)

    def test_shell_command_uses_cli_backend_and_keeps_output_in_conversation(self):
        result = types.SimpleNamespace(stdout="Shell result", stderr="", returncode=0)
        with patch.object(main.subprocess, "run", return_value=result) as run:
            self.app.handle_command("/$ echo example")
            self.drain()
        self.assertEqual(run.call_args.args[0], "echo example")
        self.assertIn("Shell result", self.text())
        self.assertEqual(self.bot.ai.history[-1]["content"], "Shell result")

    def test_incognito_clears_displayed_history(self):
        self.app.message_log.add_message("Old conversation", "user")
        self.app.handle_command("/incognito")
        self.assertNotIn("Old conversation", self.text())
        self.assertIn("Switched to incognito", self.text())


if __name__ == "__main__":
    unittest.main()
