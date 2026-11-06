#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Wadih Khairallah
"""MadLine terminal UI using the same Chatbot, settings, tools, and storage as the CLI."""

import io
import json
import os
from pathlib import Path
from queue import Empty, Queue
import shlex
import signal
import threading
from contextlib import redirect_stderr, redirect_stdout

import urwid
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

from .main import Chatbot
from .tui.panels import ChoicePanel, ControllerPanel, FormPanel, Panel
from .utils.themes import THEMES


def detect_color_mode():
    value = " ".join(os.environ.get(key, "").lower() for key in ("COLORTERM", "TERM_PROGRAM"))
    if any(name in value for name in ("truecolor", "24bit", "iterm", "kitty", "wezterm", "alacritty")):
        return "truecolor"
    return "256" if "256color" in os.environ.get("TERM", "") else "16"


class ThemeManager:
    def __init__(self, default_theme_name="default"):
        self.current_theme_name = default_theme_name if default_theme_name in THEMES else "default"
        self.current_theme = THEMES[self.current_theme_name]
        self.color_mode = detect_color_mode()
        self.callbacks = []

    def register_theme_change_callback(self, callback):
        self.callbacks.append(callback)

    def get_current_theme_name(self):
        return self.current_theme_name

    def get_current_theme(self):
        return self.current_theme

    def get_theme_names(self):
        return list(THEMES)

    def set_theme(self, name):
        if name not in THEMES:
            return False
        self.current_theme_name = name
        self.current_theme = THEMES[name]
        for callback in self.callbacks:
            callback(self.current_theme)
        return True

    def get_urwid_palette(self):
        aliases = {"header": "title", "primary": "prompt", "secondary": "output", "accent": "highlight",
                   "muted": "dim", "edit": "input", "edit_focused": "highlight", "default": "text",
                   "popup_title": "title"}
        palette = []
        for name in sorted(set(self.current_theme) | set(aliases)):
            high = self.current_theme.get(aliases.get(name, name), "#ffffff")
            low = "yellow" if name in {"highlight", "button_focused", "edit_focused"} else "light gray"
            palette.append((name, low, "default", "", high, "default"))
        return palette


class CommandEdit(urwid.Edit):
    def keypress(self, size, key):
        if key in {"enter", "meta enter", "ctrl c", "ctrl p", "ctrl n"}:
            return key
        return super().keypress(size, key)


class MessageLog:
    def __init__(self):
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)
        self.current_stream_message = None
        self.stream_text = ""

    def add_message(self, message, role="system"):
        self.walker.append(urwid.Text([(role, str(message))]))
        self.listbox.set_focus(len(self.walker) - 1)

    def start_stream(self):
        self.stream_text = ""
        self.current_stream_message = urwid.Text(("assistant", ""))
        self.walker.append(self.current_stream_message)
        self.listbox.set_focus(len(self.walker) - 1)

    def update_stream(self, text):
        if self.current_stream_message is not None:
            self.stream_text += text
            self.current_stream_message.set_text(("assistant", self.stream_text))

    def end_stream(self):
        self.current_stream_message = None

    def clear(self):
        self.walker.clear()
        self.end_stream()


class FileExplorerOverlay(Panel):
    def __init__(self, select, close, start_path=None):
        self.path = Path(start_path or os.getcwd()).expanduser().resolve()
        self.select = select
        super().__init__("Files · /file", [], close)
        self.refresh()

    def refresh(self):
        entries = sorted(self.path.iterdir(), key=lambda path: (not path.is_dir(), path.name.casefold()))
        if self.path.parent != self.path:
            entries.insert(0, self.path.parent)
        self.entries = entries
        self.walker[:] = [urwid.Text(str(self.path)), urwid.Divider()]
        for path in entries:
            label = ".." if path == self.path.parent else path.name + ("/" if path.is_dir() else "")
            self.walker.append(urwid.AttrMap(urwid.Button(label, on_press=lambda _, path=path:
                self.invoke(lambda: self.open(path))), "button", "button_focused"))
        if len(self.walker) > 2:
            self.walker.set_focus(2)
        self.set_actions([("Open", self.open_selected, bool(entries)),
                          ("Up", lambda: self.open(self.path.parent), self.path.parent != self.path)])

    def open_selected(self):
        if self.entries:
            index = max(0, min(len(self.entries) - 1, (self.walker.focus or 2) - 2))
            self.open(self.entries[index])

    def open(self, path):
        if path.is_dir():
            self.path = path
            self.refresh()
        else:
            self.select(str(path))


class MadlineApp:
    MENU = [("FILES", "show_file_explorer"), ("MEMORY", "show_memory_manager"),
            ("MODELS", "show_model_selector"), ("PROMPTS", "show_prompt_manager"),
            ("SESSIONS", "show_session_manager"), ("SETTINGS", "show_settings"),
            ("TASKS", "show_task_manager"), ("THEMES", "show_theme_manager"),
            ("TOOLS", "show_tool_manager")]

    def __init__(self, theme_name=None, chatbot=None):
        self.chatbot = chatbot if chatbot is not None else Chatbot()
        self.busy = False
        self.work_events = Queue()
        self.worker = None
        self.overlays = []
        self.overlay = None
        self.escape_pressed = False
        self.command_history = []
        self.history_position = 0
        self.left_is_focused = False
        self._sync_state()
        self.theme_manager = ThemeManager(theme_name or self.CONFIG.get("theme", "default"))
        self.theme_manager.register_theme_change_callback(self.on_theme_changed)
        self.message_log = MessageLog()
        self.header_text = urwid.Text("", align="center")
        self.status_text = urwid.Text("")
        self.footer = urwid.Text("Esc then Enter: send · Enter: newline · Tab: panels · F1: help · F2: menu · Ctrl+C: exit")
        self.edit = CommandEdit(("user", "> "), multiline=True)
        self.menu_items = [urwid.AttrMap(urwid.Button(label, on_press=lambda _, method=method:
            self._menu_action(method)), "button", "button_focused") for label, method in self.MENU]
        self.menu_listbox = urwid.ListBox(urwid.SimpleFocusListWalker(self.menu_items))
        self.menu_area = urwid.LineBox(self.menu_listbox, title="MENU")
        self.right_pile = urwid.Pile([
            ("weight", 1, urwid.LineBox(self.message_log.listbox, title="CONVERSATION")),
            ("pack", self.status_text),
            ("given", 6, urwid.LineBox(urwid.ListBox(urwid.SimpleFocusListWalker([
                urwid.AttrMap(self.edit, "edit", "edit_focused")])), title="INPUT")),
        ])
        self.main_columns = urwid.Columns([("given", 15, self.menu_area), ("weight", 1, self.right_pile)], dividechars=1)
        self.main_columns.focus_position = 1
        self.right_pile.focus_position = 2
        self.frame = urwid.Frame(self.main_columns, header=self.header_text, footer=self.footer)
        self.screen = urwid.display.raw.Screen()
        colors = {"truecolor": 2**24, "256": 256, "16": 16}[self.theme_manager.color_mode]
        self.screen.set_terminal_properties(colors=colors)
        self.loop = urwid.MainLoop(self.frame, self.theme_manager.get_urwid_palette(), screen=self.screen,
                                   unhandled_input=self.handle_key, handle_mouse=True)
        self._register_commands()
        self._refresh_header()
        self.message_log.add_message("Welcome to MadLine. Menu actions share the CLI's configuration and storage.")

    def _sync_state(self):
        # save_config reloads its dictionary; never keep an old copy in the TUI.
        self.AI = self.chatbot.ai
        self.MEMORY = self.chatbot.memory
        self.SESSION = self.chatbot.session
        self.CONFIG = self.chatbot.config
        self.DEFAULT_CONFIG = self.chatbot.default_config

    def _refresh_header(self):
        sid = self.AI.session_id
        session = "incognito"
        if sid:
            try:
                session = self.chatbot._session_label(self.chatbot._session_resolve(sid))
            except ValueError:
                session = sid[:8]
        self.header_text.set_text(("header", f"MADLINE · {self.CONFIG['model']} · {session}"))
        self.status_text.set_text(("info", "Working…" if self.busy else "Ready"))

    def _menu_action(self, method):
        if self.busy:
            self.message_log.add_message("Wait for the current operation to finish.", "warning")
            return
        try:
            getattr(self, method)()
        except Exception as error:
            self.message_log.add_message(str(error), "error")

    def _register_commands(self):
        self.command_registry = {name: dict(info) for name, info in self.chatbot.command_registry.items()}
        overrides = {
            "/help": self.show_help, "/exit": self.app_exit, "/clear": self.clear_messages,
            "/models": self.show_model_selector, "/theme": self.theme_command,
            "/system": self.system_command, "/file": self.file_command,
            "/session_tui": self.show_session_manager, "/memory": self.show_memory_manager,
            "/incognito": self.incognito_command,
        }
        for name, callback in overrides.items():
            self.command_registry.setdefault(name, {"description": "Open memory management."})
            self.command_registry[name]["func"] = callback
        # Keep the CLI's session actions, with an embeddable browser for /session tui.
        self.command_registry["/session"]["func"] = self.session_command

    def _capture_call(self, callback):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), self.chatbot.console.capture() as capture:
            result = callback()
        return result, capture.get() + output.getvalue()

    def _run_cli(self, command):
        self._show_captured(self._capture_call(lambda: self.chatbot.handle_command(command)))
        self._after_state_change()

    def _after_state_change(self):
        self._sync_state()
        name = self.CONFIG.get("theme", "default")
        if name != self.theme_manager.get_current_theme_name():
            self.theme_manager.set_theme(name)
        self._refresh_header()

    def handle_command(self, command_text):
        if self.busy:
            self.message_log.add_message("Wait for the current operation to finish.", "warning")
            return False
        parts = command_text.strip().split(maxsplit=1)
        name = parts[0].lower() if parts else ""
        contents = parts[1] if len(parts) > 1 else ""
        if name not in self.command_registry:
            self.message_log.add_message(f"Unknown command: {name}. Use /help.", "error")
            return False
        try:
            # The commands below can perform network, embedding, or subprocess work.
            action = contents.split(maxsplit=1)[0].lower() if contents else ""
            if name in {"/$", "/recall", "/remember"} or (name == "/session" and action == "summary"):
                self._background(lambda: self._capture_call(lambda: self.chatbot.handle_command(command_text)),
                                 self._show_captured)
            elif self.command_registry[name]["func"] == self.chatbot.command_registry.get(name, {}).get("func"):
                if name == "/settings" and contents:
                    key, value = contents.split(maxsplit=1)
                    self._save_settings({key: value})
                else:
                    self._run_cli(command_text)
            else:
                self.command_registry[name]["func"](contents)
            self._after_state_change()
        except urwid.ExitMainLoop:
            raise
        except Exception as error:
            self.message_log.add_message(str(error), "error")
        return False

    def _show_captured(self, result):
        _, text = result
        if text.strip():
            self.message_log.add_message(Text.from_ansi(text.rstrip()).plain)

    def _background(self, work, success=None):
        if self.busy:
            raise ValueError("Wait for the current operation to finish.")
        self.busy = True
        self._refresh_header()

        def run():
            try:
                result = work()
                self.work_events.put(("done", result, success))
            except Exception as error:
                self.work_events.put(("error", str(error), None))

        self.worker = threading.Thread(target=run, daemon=True)
        self.worker.start()
        self.loop.set_alarm_in(0.03, self._poll_work)

    def _poll_work(self, loop=None, data=None):
        try:
            while True:
                kind, value, callback = self.work_events.get_nowait()
                if kind == "token":
                    self.message_log.update_stream(value)
                    continue
                self.busy = False
                if kind == "error":
                    self.message_log.add_message(value, "error")
                elif callback:
                    try:
                        callback(value)
                    except Exception as error:
                        self.message_log.add_message(str(error), "error")
                self.message_log.end_stream()
                self._after_state_change()
        except Empty:
            pass
        if self.busy:
            self.loop.set_alarm_in(0.03, self._poll_work)

    def process_user_input(self, user_input):
        if not user_input or not user_input.strip():
            return
        if self.busy:
            self.message_log.add_message("Wait for the current operation to finish.", "warning")
            return
        self.command_history.append(user_input)
        self.history_position = len(self.command_history)
        if user_input.startswith("/"):
            self.handle_command(user_input)
            return
        self.message_log.add_message(user_input, "user")
        self.message_log.start_stream()

        def respond():
            # No Urwid widgets or loop APIs are touched by the worker.
            expanded = self.chatbot.replace_file_references(user_input, interactive=False)
            self.chatbot._register_memory()
            self.AI.messages_system(self.chatbot.config["system_prompt"])
            if self.chatbot.memory_enabled:
                self.chatbot.memory.add("user: " + user_input)
            if self.CONFIG["stream"]:
                response_text = ""
                with self.AI.interact(expanded, raw=True, model=self.CONFIG["model"], tools=self.CONFIG["tools"],
                                      session_id=self.AI.session_id) as chunks:
                    for chunk in chunks:
                        if chunk:
                            response_text += chunk
                            self.work_events.put(("token", chunk, None))
            else:
                response_text = self.AI.interact(expanded, raw=False, model=self.CONFIG["model"], tools=self.CONFIG["tools"],
                                                 stream=False, quiet=True, session_id=self.AI.session_id)
                if not isinstance(response_text, str):
                    raise ValueError("The model returned no response.")
                self.work_events.put(("token", response_text, None))
            if self.chatbot.memory_enabled:
                self.chatbot.memory.add("assistant: " + response_text)
            return response_text

        self._background(lambda: self._capture_call(respond), self._chat_finished)

    def _chat_finished(self, result):
        response, _ = result
        if self.CONFIG["markdown"] and self.message_log.current_stream_message is not None:
            output = io.StringIO()
            width = max(20, self.screen.get_cols_rows()[0] - 20)
            Console(file=output, width=width, color_system=None).print(Markdown(response))
            self.message_log.current_stream_message.set_text(("assistant", output.getvalue().rstrip()))
        self._show_captured(result)

    def _save_settings(self, changes, close=False):
        if self.busy:
            raise ValueError("Wait for the current operation to finish.")
        target = self.overlay
        def applied(_=None):
            self._after_state_change()
            if close and self.overlay is target:
                self.close_overlay()
            self.message_log.add_message("Settings saved.", "success")
        enabling_memory = str(changes.get("memory", False)).strip().lower() in {"true", "1", "yes"}
        if enabling_memory and not self.chatbot.memory_enabled:
            def completed(result):
                self._show_captured(result)
                applied()
            self._background(lambda: self._capture_call(lambda: self.chatbot.apply_settings(changes)), completed)
        else:
            self.chatbot.apply_settings(changes)
            applied()

    def show_settings(self, contents=None):
        panel = FormPanel("Settings · /settings", {key: self.CONFIG[key] for key in sorted(self.DEFAULT_CONFIG)},
                          lambda values: self._save_settings(values, close=True), self.close_overlay,
                          multiline={"system_prompt"})
        self.show_overlay(panel)

    def show_prompt_manager(self, contents=None):
        self.show_overlay(FormPanel("System prompt · /system", {"system_prompt": self.CONFIG["system_prompt"]},
                                   lambda values: self._save_settings(values, close=True), self.close_overlay,
                                   multiline={"system_prompt"}))

    def system_command(self, contents=None):
        if contents:
            self._save_settings({"system_prompt": contents})
        else:
            self.show_prompt_manager()

    def show_model_selector(self, contents=None):
        if contents:
            self._save_settings({"model": contents})
            return
        def show(models):
            self.show_overlay(ChoicePanel("Models · /models", sorted(models),
                lambda model: self._save_settings({"model": model}, close=True), self.close_overlay,
                current=self.CONFIG["model"]))
        def loaded(result):
            self._show_captured(result)
            show(result[0])
        self._background(lambda: self._capture_call(lambda: self.AI.list_models(
            not bool(getattr(self.AI, "models", [])))), loaded)

    def handle_model_selector_result(self, message=None, action=None):
        if action == "model_selected":
            self._save_settings({"model": message}, close=True)
        else:
            self.close_overlay(cancel=True)

    def show_theme_manager(self, contents=None):
        previous = self.CONFIG["theme"]
        panel = ChoicePanel("Themes · /theme", sorted(THEMES),
                            lambda name: self._save_settings({"theme": name}, close=True), self.close_overlay,
                            preview=self.theme_manager.set_theme, current=previous)
        self.show_overlay(panel, on_cancel=lambda: self.theme_manager.set_theme(previous))

    def theme_command(self, contents=None):
        if contents:
            self._save_settings({"theme": contents})
        else:
            self.show_theme_manager()

    def show_file_explorer(self, contents=None, start_path=None):
        self.show_overlay(FileExplorerOverlay(self._attach_file, self.close_overlay, start_path))

    def file_command(self, contents=None):
        if contents:
            args = shlex.split(contents)
            if len(args) != 1:
                raise ValueError('Usage: /file "path to file"')
            self._attach_file(args[0])
        else:
            self.show_file_explorer()

    def _attach_file(self, path):
        path = Path(path).expanduser()
        if not path.is_file():
            raise ValueError(f"File not found: {path}")
        target = self.overlay
        def attached(text):
            if self.overlay is target and target is not None:
                self.close_overlay()
            self.edit.set_edit_text(self.edit.edit_text + f"\n\nFile: {path}\n```\n{text}\n```\n")
            self.message_log.add_message(f"Attached to draft: {path}", "success")
        def extracted(result):
            self._show_captured(result)
            attached(result[0])
        self._background(lambda: self._capture_call(lambda: self.chatbot.read_file(path)), extracted)

    def handle_file_explorer_result(self, message=None, action=None):
        if action == "file_selected":
            self._attach_file(message)
        else:
            self.close_overlay(cancel=True)

    def show_memory_manager(self, contents=None):
        enabled = bool(self.chatbot.memory_enabled)
        editor = urwid.Edit("Text / query:\n", multiline=True)
        def toggle():
            self._save_settings({"memory": not enabled}, close=True)
        def memory_action(command):
            if not self.chatbot.memory_enabled:
                raise ValueError("Enable memory first.")
            if not editor.edit_text.strip():
                raise ValueError("Enter text or a search query first.")
            self.handle_command(command + " " + editor.edit_text)
        # Actions share the CLI handlers and their validation/results.
        panel = Panel("Memory · /remember /recall", [urwid.Text("Memory is " + ("enabled" if enabled else "disabled")), editor],
                      self.close_overlay, actions=[("Disable" if enabled else "Enable", toggle),
                      ("Remember", lambda: memory_action("/remember")), ("Recall", lambda: memory_action("/recall"))])
        panel.editor = editor
        self.show_overlay(panel)

    def show_tool_manager(self, contents=None):
        tools = self.AI.list_functions()
        fields = {}
        widgets = [urwid.Text("Tool availability applies to this process. Global enable is saved in settings.")]
        global_enabled = urwid.CheckBox("Tools enabled", state=self.CONFIG["tools"])
        widgets.append(global_enabled)
        for spec in tools:
            function = spec["function"]
            checkbox = urwid.CheckBox(function["name"], state=not function.get("disabled", False))
            fields[function["name"]] = checkbox
            widgets.extend([checkbox, urwid.Text(function.get("description", "")), urwid.Divider()])
        def save():
            if self.busy:
                raise ValueError("Wait for the current operation to finish.")
            self.chatbot.apply_settings({"tools": global_enabled.state})
            for name, checkbox in fields.items():
                method = self.AI.enable_function if checkbox.state else self.AI.disable_function
                if method(name) is False:
                    raise ValueError(f"Could not update tool: {name}")
            self._after_state_change()
            self.close_overlay()
            self.message_log.add_message("Tool availability updated.", "success")
        panel = Panel("Tools · /tools", widgets, self.close_overlay, actions=[("Apply", save)], close_label="Cancel")
        panel.fields = fields
        panel.global_enabled = global_enabled
        self.show_overlay(panel)

    def show_session_manager(self, contents=None):
        from .tui.session_manager import SessionManager
        controller = SessionManager(self.CONFIG["theme"], session_obj=self.SESSION)
        def closed():
            if controller.selected_sid:
                self._run_cli("/session load " + controller.selected_sid)
                self._show_history()
            elif self.AI.session_id and not any(s["id"] == self.AI.session_id for s in self.SESSION.list()):
                self.AI.session_reset()
                self._show_history()
            self.chatbot.refresh_session_lookup()
            self.close_overlay()
            self._after_state_change()
        self.show_overlay(ControllerPanel(controller, closed))

    def session_command(self, contents=None):
        if (contents or "").strip() == "tui":
            self.show_session_manager()
        else:
            before = self.AI.session_id
            self._run_cli("/session " + (contents or ""))
            if self.AI.session_id != before:
                self._show_history()

    def show_task_manager(self, contents=None):
        from .tui.task_manager import TaskManager
        controller = TaskManager(self.CONFIG["theme"])
        self.show_overlay(ControllerPanel(controller, self.close_overlay))

    def incognito_command(self, contents=None):
        result = self._capture_call(lambda: self.chatbot.incognito_command(contents))
        self._show_history()
        self._show_captured(result)

    def _show_history(self):
        self.message_log.clear()
        for message in self.AI.messages():
            role = message.get("role", "system")
            self.message_log.add_message(message.get("content") or "", role if role in THEMES["default"] else "system")
        if not self.message_log.walker:
            self.message_log.add_message("Empty conversation.")

    def show_help(self, contents=None):
        lines = [urwid.Text("Esc then Enter or Alt+Enter sends. Enter adds a newline.\n"
                            "Tab switches panels. Ctrl+P / Ctrl+N browse input history.\n"
                            "Esc closes a dialog. Ctrl+C exits. F2 opens the menu."), urwid.Divider()]
        for name, info in sorted(self.command_registry.items()):
            lines.append(urwid.Text(f"{name}: {info.get('description', '')}"))
        self.show_overlay(Panel("Help · /help", lines, self.close_overlay))

    def show_main_menu(self, contents=None):
        widgets = [urwid.Button(label.title(), on_press=lambda _, method=method:
                   self._menu_action(method)) for label, method in self.MENU]
        widgets += [urwid.Button("Help", on_press=lambda _: self.show_help()),
                    urwid.Button("Exit", on_press=lambda _: self.app_exit())]
        self.show_overlay(Panel("Menu", widgets, self.close_overlay))

    def show_overlay(self, widget, on_cancel=None):
        self.overlays.append((widget, on_cancel))
        self._render_overlay()

    def _render_overlay(self):
        self.overlay = self.overlays[-1][0] if self.overlays else None
        self.loop.widget = (urwid.Overlay(self.overlay, self.frame, "center", ("relative", 90),
                                         "middle", ("relative", 90)) if self.overlay else self.frame)

    def close_overlay(self, cancel=False):
        if self.overlays:
            _, on_cancel = self.overlays.pop()
            if cancel and on_cancel:
                on_cancel()
        self._render_overlay()

    def on_theme_changed(self, theme):
        if hasattr(self, "loop"):
            self.loop.screen.register_palette(self.theme_manager.get_urwid_palette())
            self.loop.screen.clear()

    def clear_messages(self, contents=None):
        self.message_log.clear()

    def toggle_focus(self):
        self.left_is_focused = not self.left_is_focused
        self.main_columns.focus_position = 0 if self.left_is_focused else 1
        if not self.left_is_focused:
            self.right_pile.focus_position = 2

    def app_exit(self, contents=None):
        if self.busy:
            self.message_log.add_message("Wait for the current operation to finish before exiting.", "warning")
            return
        raise urwid.ExitMainLoop()

    def handle_key(self, key):
        if key == "ctrl c":
            self.app_exit()
        elif self.overlay:
            if key == "esc":
                self.close_overlay(cancel=True)
        elif key == "f1":
            self.show_help()
        elif key == "f2":
            self.show_main_menu()
        elif key == "tab":
            self.toggle_focus()
        elif key == "esc":
            self.escape_pressed = True
        elif key in {"meta enter", "enter"} and not self.left_is_focused:
            if key == "meta enter" or self.escape_pressed:
                if not self.busy:
                    text = self.edit.edit_text
                    self.edit.set_edit_text("")
                    self.process_user_input(text)
                self.escape_pressed = False
            else:
                self.edit.insert_text("\n")
        elif key in {"ctrl p", "ctrl n"} and self.command_history:
            offset = -1 if key == "ctrl p" else 1
            self.history_position = max(0, min(len(self.command_history), self.history_position + offset))
            self.edit.set_edit_text(self.command_history[self.history_position]
                                    if self.history_position < len(self.command_history) else "")

    def run(self):
        previous = signal.getsignal(signal.SIGINT)
        def interrupt(signum, frame):
            self.app_exit()
            self.loop.draw_screen()
        signal.signal(signal.SIGINT, interrupt)
        try:
            self.loop.run()
        except (KeyboardInterrupt, urwid.ExitMainLoop):
            pass
        finally:
            signal.signal(signal.SIGINT, previous)


if __name__ == "__main__":
    MadlineApp().run()
