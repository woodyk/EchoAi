"""CLI session regressions using real Interactor JSON storage and no provider calls.

Run with: python -m unittest discover -s tests -v
Requires the normal rich, prompt_toolkit, and ai-interactor distributions.
"""

import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import shlex
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from prompt_toolkit.document import Document
from rich.console import Console

# Load storage directly, so these tests do not require provider SDKs, embeddings,
# browser dependencies, credentials, or application writes to the user's home.
storage_path = importlib.metadata.distribution("ai-interactor").locate_file("interactor/session.py")
spec = importlib.util.spec_from_file_location("session_test_storage", storage_path)
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)


class FakeInteractor:
    instances = []
    summary_response = "Summary of the selected transcript."

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.session_id = None
        self.session = storage.Session(kwargs["session_path"]) if kwargs.get("session_path") else None
        self.history = []
        self.calls = []
        self.reset_count = 0
        self.instances.append(self)

    def list_functions(self):
        return []

    def session_load(self, sid):
        self.session_id = sid
        self.history = self.session.load(sid)

    def session_reset(self):
        self.session_id = None
        self.history = []
        self.reset_count += 1

    def messages(self):
        return self.history

    def messages_length(self):
        return 42

    def interact(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return self.summary_response


interactor_stub = types.ModuleType("interactor")
interactor_stub.Interactor = FakeInteractor
interactor_stub.Session = storage.Session
mrblack_stub = types.ModuleType("mrblack")
for function in ("extract_text", "translate_text", "extract_pii_text", "extract_pii_file", "extract_pii_url"):
    setattr(mrblack_stub, function, Mock())
memory_stub = types.ModuleType("echoai.utils.memory")
memory_stub.Memory = type("UnusedMemory", (), {})
with patch.dict(sys.modules, {"interactor": interactor_stub, "mrblack": mrblack_stub,
                              "echoai.utils.memory": memory_stub}):
    from echoai.main import Chatbot, SlashCommandCompleter
    from echoai import main
    cli_modules = {name: module for name, module in sys.modules.items()
                   if name in {"echoai.main", "echoai.session_commands", "echoai.utils.themes"}}
sys.modules.update(cli_modules)


class SessionCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.console_output = io.StringIO()
        self.console = Console(file=self.console_output, width=100, color_system=None)
        self.addCleanup(patch.stopall)
        patch.object(main, "console", self.console).start()
        patch.dict(sys.modules, {"interactor": interactor_stub}).start()
        FakeInteractor.instances.clear()
        FakeInteractor.summary_response = "Summary of the selected transcript."
        # An existing session at startup must be discoverable immediately.
        self.store = storage.Session(Path(self.temp.name) / ".echoai" / "sessions")
        self.existing_id = self.store.create("Project notes")
        with patch.object(Path, "home", return_value=Path(self.temp.name)), \
                patch.object(Chatbot, "_register_tool_functions"):
            self.bot = Chatbot()
        self.events = []
        self.bot.display = lambda kind, text: self.events.append((kind, text))

    def command(self, args=""):
        result = self.bot.handle_command("/session" + (" " + args if args else ""))
        self.assertFalse(result)
        return self.events[-1] if self.events else None

    def assertError(self, text):
        self.assertEqual(self.events[-1][0], "error")
        self.assertIn(text, self.events[-1][1])

    def completions(self, text):
        return list(SlashCommandCompleter(self.bot).get_completions(Document(text), None))

    def apply_completion(self, text, completion):
        return text[:len(text) + completion.start_position] + completion.text

    def test_startup_keeps_session_lookup(self):
        self.assertEqual(list(self.bot.session_id_lookup.values()), [self.existing_id])
        self.command('load "Project notes"')
        self.assertEqual(self.bot.ai.session_id, self.existing_id)

    def test_load_by_name_id_prefix_and_legacy_label(self):
        for reference in ["Project notes", "project NOTES", self.existing_id,
                          self.existing_id[:8], f"Project notes ({self.existing_id[:8]})"]:
            with self.subTest(reference=reference):
                self.command("load " + shlex.quote(reference))
                self.assertEqual(self.bot.ai.session_id, self.existing_id)

    def test_unquoted_multiword_name_load(self):
        self.command("load Project notes")
        self.assertEqual(self.bot.ai.session_id, self.existing_id)

    def test_failed_load_preserves_conversation_and_creates_no_file(self):
        self.command("load " + self.existing_id[:8])
        self.bot.ai.history = [{"role": "user", "content": "keep me"}]
        before = sorted(self.store.path.iterdir())
        for invalid in ["missing", "../outside", "", '"unterminated']:
            self.command("load " + invalid)
            self.assertEqual(self.bot.ai.session_id, self.existing_id)
            self.assertEqual(self.bot.ai.history[0]["content"], "keep me")
            self.assertEqual(self.bot.ai.reset_count, 0)
        self.assertEqual(before, sorted(self.store.path.iterdir()))

    def test_duplicate_existing_names_are_ambiguous(self):
        duplicate = self.store.create("project NOTES")
        self.command('load "Project notes"')
        self.assertError("Ambiguous session")
        self.command("load " + duplicate[:8])
        self.assertEqual(self.bot.ai.session_id, duplicate)

    def test_colliding_prefixes_are_displayed_with_unique_ids(self):
        ids = ["12345678-aaaa", "12345678-bbbb"]
        for sid in ids:
            self.store._save_file(sid, {"id": sid, "name": "Duplicate", "created": "2026-11-05", "messages": []})
        self.command("load 12345678")
        self.assertError("Ambiguous session")
        for sid in ids:
            short = self.bot._session_short_id(sid)
            self.assertGreater(len(short), 8)
            self.assertEqual(self.bot._session_resolve(short)["id"], sid)
        self.command()
        self.assertIn("12345678-a", self.console_output.getvalue())

    def test_create_rename_and_reload_persist_names(self):
        self.command("new   Release planning  ")
        sid = self.bot.ai.session_id
        self.assertEqual(self.store.load_full(sid)["name"], "Release planning")
        self.command('rename "Release planning" Final release plan')
        self.assertEqual(self.store.load_full(sid)["name"], "Final release plan")
        self.command('load "Final release plan"')
        self.assertEqual(self.bot.ai.session_id, sid)
        self.command('load "Release planning"')
        self.assertError("Session not found")

    def test_duplicate_and_empty_names_do_not_mutate_storage(self):
        for args in ['new " project NOTES "', 'new "   "', 'new "line\nbreak"',
                     f'rename {self.existing_id[:8]} "   "']:
            with self.subTest(args=args):
                self.command(args)
                self.assertEqual(self.events[-1][0], "error")
        self.assertEqual(len(self.store.list()), 1)
        self.assertEqual(self.store.load_full(self.existing_id)["name"], "Project notes")

    def test_rename_duplicate_name_keeps_original(self):
        sid = self.store.create("Other")
        self.command(f'rename {sid[:8]} "PROJECT NOTES"')
        self.assertError("already exists")
        self.assertEqual(self.store.load_full(sid)["name"], "Other")
        self.command(f'rename {sid[:8]} OTHER')
        self.assertEqual(self.store.load_full(sid)["name"], "OTHER")

    def test_delete_only_resets_active_session(self):
        other = self.store.create("Other")
        self.command("load " + self.existing_id[:8])
        self.command("delete " + other[:8])
        self.assertEqual(self.bot.ai.session_id, self.existing_id)
        self.assertEqual(self.bot.ai.reset_count, 0)
        self.command('delete "Project notes"')
        self.assertIsNone(self.bot.ai.session_id)
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.bot.ai.reset_count, 1)

    def test_tags_trim_deduplicate_and_remove(self):
        self.command('tag "Project notes" work, release,work,,')
        self.assertEqual(self.store.load_full(self.existing_id)["tags"], ["release", "work"])
        self.command('tag --remove "Project notes" release,missing')
        self.assertEqual(self.store.load_full(self.existing_id)["tags"], ["work"])
        for args in ['tag --remove', 'tag --remove "Project notes"', 'tag "Project notes" , ,']:
            self.command(args)
            self.assertEqual(self.events[-1][0], "error")
        self.assertEqual(self.store.load_full(self.existing_id)["tags"], ["work"])

    def test_default_list_help_show_and_markup_are_readable(self):
        self.command()
        self.assertIn("Saved Sessions", self.console_output.getvalue())
        self.assertIn("Project notes", self.console_output.getvalue())
        self.command("show")
        self.assertIn("Incognito", self.console_output.getvalue())
        sid = self.store.create("[red]literal[/red]")
        self.command("show " + sid[:8])
        self.assertIn("[red]literal[/red]", self.console_output.getvalue())
        self.command("help")
        self.assertIn("/session rename", self.console_output.getvalue())
        self.assertIn("/session show", self.console_output.getvalue())
        self.assertIn("[session]", self.console_output.getvalue())

    def test_narrow_layout_keeps_ids_and_usage_without_truncation(self):
        self.bot.console = Console(file=self.console_output, width=50, color_system=None)
        self.command('tag "Project notes" release,work')
        self.command()
        self.command('show "Project notes"')
        self.command('help')
        rendered = self.console_output.getvalue()
        self.assertNotIn("…", rendered)
        self.assertIn("[session]", rendered)

    def test_show_current_and_saved_messages_without_switching(self):
        self.store.msg_insert(self.existing_id, {"role": "user", "content": "Saved content"})
        self.command('show "Project notes"')
        self.assertIsNone(self.bot.ai.session_id)
        self.assertIn("User Messages", self.console_output.getvalue())
        self.command('load "Project notes"')
        self.command("show")
        self.assertIn("Tokens", self.console_output.getvalue())

    def test_empty_list_and_search_are_friendly(self):
        self.store.delete(self.existing_id)
        for args in ["", "list", "searchmeta absent", "search absent"]:
            self.command(args)
            self.assertEqual(self.events[-1][0], "info")

    def test_search_outputs_tables_instead_of_json(self):
        message_id = self.store.msg_insert(self.existing_id, {"role": "user", "content": "Release checklist"})
        self.command("search release")
        self.assertIn("Matching Messages", self.console_output.getvalue())
        self.assertIn("Release checklist", self.console_output.getvalue())
        self.assertIn(message_id[:8], self.console_output.getvalue())
        self.command("searchmeta project")
        self.assertIn("Matching Sessions", self.console_output.getvalue())
        self.assertIsNone(self.bot.ai.session_id)

    def test_summary_uses_selected_transcript_without_touching_active_history(self):
        self.store.msg_insert(self.existing_id, {"role": "user", "content": "Selected session only"})
        other = self.store.create("Other")
        self.store.msg_insert(other, {"role": "user", "content": "Keep active history"})
        self.command("load " + other[:8])
        before = self.store.load_full(other)
        self.command('summary "Project notes"')
        worker = FakeInteractor.instances[-1]
        self.assertFalse(worker.kwargs["session_enabled"])
        prompt, options = worker.calls[-1]
        self.assertIn("Selected session only", prompt)
        self.assertNotIn("Keep active history", prompt)
        self.assertFalse(options["tools"])
        self.assertEqual(self.store.load_full(self.existing_id)["summary"], worker.summary_response)
        self.assertEqual(self.bot.ai.session_id, other)
        self.assertEqual(self.store.load_full(other), before)
        self.assertEqual(self.bot.ai.calls, [])

    def test_summary_defaults_to_current_and_keeps_old_summary_on_empty_result(self):
        self.store.msg_insert(self.existing_id, {"role": "user", "content": "Hello"})
        self.command("load " + self.existing_id[:8])
        self.store.update(self.existing_id, "summary", "Keep this")
        FakeInteractor.summary_response = " "
        self.command("summary")
        self.assertError("No summary was returned")
        self.assertEqual(self.store.load_full(self.existing_id)["summary"], "Keep this")

    def test_summary_requires_messages_and_saved_session(self):
        self.command("summary")
        self.assertError("No saved session")
        self.command('summary "Project notes"')
        self.assertError("no messages")

    def test_branch_uses_message_id_and_preserves_source(self):
        first = self.store.msg_insert(self.existing_id, {"role": "user", "content": "First"})
        self.store.msg_insert(self.existing_id, {"role": "assistant", "content": "Second"})
        source = self.store.load_full(self.existing_id)
        self.command("load " + self.existing_id[:8])
        self.command(f"branch {first[:8]} Release branch")
        branch = self.store.load_full(self.bot.ai.session_id)
        self.assertEqual(branch["name"], "Release branch")
        self.assertEqual(branch["parent"], self.existing_id)
        self.assertEqual(len(branch["messages"]), 1)
        self.assertEqual(self.store.load_full(self.existing_id), source)

    def test_invalid_branch_does_not_create_session(self):
        self.command("branch absent New branch")
        self.assertError("No saved session")
        self.command("load " + self.existing_id[:8])
        self.command("branch absent New branch")
        self.assertError("Message ID was not found")
        self.assertEqual(len(self.store.list()), 1)

    def test_tui_alias_uses_existing_browser(self):
        self.bot.session_tui_command = Mock()
        self.command("tui")
        self.bot.session_tui_command.assert_called_once_with()

    def test_invalid_input_is_reported_without_raising_or_changing_state(self):
        self.command("load " + self.existing_id[:8])
        for args in ['unknown', 'list extra', 'help extra', 'tui extra', 'new', 'rename',
                     'delete', 'tag', 'branch', 'search', 'searchmeta', 'load "unfinished']:
            with self.subTest(args=args):
                self.command(args)
                self.assertEqual(self.events[-1][0], "error")
                self.assertEqual(self.bot.ai.session_id, self.existing_id)

    def test_completion_round_trips_names_spaces_quotes_and_punctuation(self):
        for name in ["Two word name", "O'Brien notes", 'Quoted "name"', "[red] literal"]:
            sid = self.store.create(name)
            text = "/session load " + name[:2]
            matches = [c for c in self.completions(text) if shlex.split(c.text) == [name]]
            self.assertEqual(len(matches), 1)
            command = self.apply_completion(text, matches[0])
            self.bot.handle_command(command)
            self.assertEqual(self.bot.ai.session_id, sid)

    def test_completion_replaces_full_partial_reference(self):
        for text in ['/session load Project no', '/session load "Project no',
                     "/session load 'Project no", '/session rename "Project no']:
            with self.subTest(text=text):
                results = self.completions(text)
                self.assertEqual(len(results), 1)
                parsed = shlex.split(self.apply_completion(text, results[0]))
                self.assertEqual(parsed[2:], ["Project notes"])

    def test_completion_stops_after_reference_for_rename_and_tag(self):
        for text in ['/session rename "Project notes" ', '/session rename "Project notes" New',
                     '/session tag "Project notes" ', '/session tag --remove "Project notes" work']:
            self.assertEqual(self.completions(text), [])
        text = '/session tag --remove Pro'
        result = self.completions(text)[0]
        self.assertEqual(shlex.split(self.apply_completion(text, result)),
                         ["/session", "tag", "--remove", "Project notes"])

    def test_duplicate_name_completion_inserts_ids(self):
        self.store.create("Project notes")
        completions = self.completions("/session load Pro")
        self.assertEqual(len(completions), 2)
        for c in completions:
            self.assertNotIn(" ", c.text)
            self.bot._session_resolve(c.text)

    def test_branch_completion_uses_current_messages_not_sessions(self):
        mid = self.store.msg_insert(self.existing_id, {"role": "user", "content": "Branch here"})
        self.command("load " + self.existing_id[:8])
        result = self.completions("/session branch ")
        self.assertEqual([c.text for c in result], [mid])
        self.assertEqual(self.completions(f"/session branch {mid} New"), [])

    def test_command_and_subcommand_completion_remain_registry_driven(self):
        self.assertIn("/session", [c.text for c in self.completions("/ses")])
        self.assertIn("show", [c.text for c in self.completions("/session ")])
        self.assertEqual([c.text for c in self.completions("/session loa")], ["load"])
        self.assertEqual(self.completions("/session new "), [])

    def browser(self):
        from echoai.tui.session_manager import SessionManager
        return SessionManager(session_obj=self.store)

    def test_browser_empty_actions_do_not_crash(self):
        self.store.delete(self.existing_id)
        browser = self.browser()
        for key in ["down", "up", "enter", "v", "right", "r", "d"]:
            browser.handle_input(key)
        self.assertEqual(browser.current_index, 0)
        self.assertIsNone(browser.selected_sid)
        self.assertEqual(browser.mode, "main")

    def test_browser_uses_same_name_validation(self):
        browser = self.browser()
        for name in [" project NOTES ", "   ", "line\nbreak"]:
            with self.assertRaises(ValueError):
                browser.create_session(name)
        browser.rename_session("  Release plan  ")
        self.assertEqual(self.store.load_full(self.existing_id)["name"], "Release plan")
        self.command('load "Release plan"')
        self.assertEqual(self.bot.ai.session_id, self.existing_id)
        browser.create_session("  Another plan  ")
        self.assertIn("Another plan", [s["name"] for s in self.store.list()])

    def test_browser_metadata_editor_rejects_duplicates(self):
        other = self.store.create("Other")
        browser = self.browser()
        browser.current_index = next(i for i, s in enumerate(browser.filtered_sessions) if s["id"] == other)
        browser.handle_input("right")
        browser.edit_widgets["name"].set_edit_text("Project notes")
        browser.handle_input("enter")
        self.assertEqual(self.store.load_full(other)["name"], "Other")
        self.assertIn("already exists", browser.footer_text.text)

    def test_browser_selection_scroll_and_empty_preview(self):
        for i in range(25):
            self.store.create(f"Session {i}")
        browser = self.browser()
        for _ in range(20):
            browser.handle_input("down")
        self.assertEqual(browser.body_widget.focus, 20)
        browser.handle_input("v")
        browser.handle_input("page down")
        browser.handle_input("esc")
        self.assertEqual(browser.body_widget.focus, browser.current_index)
        canvas = browser.main_frame.render((100, 24))
        self.assertEqual(canvas.rows(), 24)

    def test_browser_search_with_no_matches_can_create_session(self):
        browser = self.browser()
        browser.search_sessions("no matches")
        browser.refresh_sessions()
        self.assertEqual(browser.current_index, 0)
        browser.handle_input("enter")
        browser.create_session("New from empty search")
        self.assertIn("New from empty search", [s["name"] for s in self.store.list()])
        self.assertEqual(browser.filtered_sessions[browser.current_index]["name"], "New from empty search")

    def test_browser_input_dialogs_render_and_accept_names(self):
        for key in ("n", "r", "/"):
            with self.subTest(key=key):
                browser = self.browser()
                browser.handle_input(key)
                self.assertEqual(browser.loop.widget.render((100, 24), focus=True).rows(), 24)
        browser = self.browser()
        browser.handle_input("n")
        edit = browser.loop.widget.top_w.base_widget
        edit.set_edit_text("project NOTES")
        browser.loop.unhandled_input("enter")
        self.assertEqual(browser.mode, "new")
        self.assertIn("already exists", browser.footer_text.text)
        edit.set_edit_text("  Dialog name  ")
        browser.loop.unhandled_input("enter")
        self.assertEqual(browser.mode, "main")
        self.assertIn("Dialog name", [s["name"] for s in self.store.list()])


if __name__ == "__main__":
    unittest.main()
