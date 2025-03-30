#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-28 16:21:59
# Modified: 2025-03-30 18:19:18

import sys
import os
import re
import json
import subprocess
import platform
import signal
import datetime
import getpass
from pathlib import Path

import pytz
from openai import OpenAI

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.prompt import Confirm
from rich.rule import Rule

console = Console()

# Local module imports
from .interactor import Interactor
from .themes import themes
from .textextract import extract_text
from .functions import (
    run_python_code,
    run_bash_command,
    get_weather,
    create_qr_code,
    get_website_data,
    check_system_health,
    duckduckgo_search,
    google_search,
    slashdot_search,
)

class Chatbot:
    def __init__(self):
        self.console = Console()
        self.command_registry = {}
        self.messages = []
        self.config = {}
        self.default_config = {
            "model": "openai:gpt-4o",
            "system_prompt": "You are a helpful assistant.",
            "username": "User",
            "markdown": True,
            "theme": "default",
            "stream": True,
            "tools": True,
            "memory": False
        }
        self.ECHOAI_DIR = Path.home() / ".echoai"
        self.CONFIG_PATH = self.ECHOAI_DIR / "config"
        self.memory_db_path = self.ECHOAI_DIR / "echoai_db"
        self._initialize_directories()
        self.load_config()
        self.ai = Interactor(model=self.config.get("model"))
        self._setup_theme()
        self._register_tool_functions()
        self._register_commands()

    def _initialize_directories(self):
        if not self.ECHOAI_DIR.exists():
            self.ECHOAI_DIR.mkdir(exist_ok=True)

    def load_config(self):
        if self.CONFIG_PATH.exists():
            with self.CONFIG_PATH.open("r") as file_object:
                config_from_file = json.load(file_object)
            self.config = self.default_config.copy()
            self.config.update(config_from_file)
        else:
            self.config = self.default_config.copy()
            self.save_config(self.config)

    def save_config(self, new_config):
        current_config = self.default_config.copy()
        if self.CONFIG_PATH.exists():
            with self.CONFIG_PATH.open("r") as file_object:
                current_config.update(json.load(file_object))
        current_config.update(new_config)
        with self.CONFIG_PATH.open("w") as file_object:
            json.dump(current_config, file_object, indent=4)
        self.load_config()

    def _setup_theme(self):
        selected_theme = self.config.get("theme", self.default_config["theme"])
        if selected_theme in themes:
            self.style_dict = themes[selected_theme]
        else:
            self.style_dict = themes["default"]

    def get_prompt_style(self):
        return Style.from_dict({
            'prompt': self.style_dict["prompt"],
            '': self.style_dict["input"]
        })

    def _register_tool_functions(self):
        tool_functions = [
            run_bash_command,
            run_python_code,
            get_website_data,
            google_search,
            duckduckgo_search,
            check_system_health,
            create_qr_code,
            get_weather,
            extract_text,
            slashdot_search
        ]
        for function in tool_functions:
            self.ai.add_function(function)

    def _register_commands(self):
        self.register_command("/show_model", self.show_model_command,
                              "Show the currently configured AI model.")
        self.register_command("/theme", self.theme_command,
                              "Select the theme to use for the application.")
        self.register_command("/file", self.file_command,
                              "Insert the contents of a file for analysis.")
        self.register_command("/system", self.system_command,
                              "Set a new system prompt.")
        self.register_command("/show_system", self.show_system_command,
                              "Show the current system prompt.")
        self.register_command("/history", self.history_command,
                              "Show the chat history.")
        self.register_command("/models", self.models_command,
                              "Select the AI model to use.")
        self.register_command("/settings", self.settings_command,
                              "Display or modify the current configuration settings.")
        self.register_command("/flush", self.flush_command,
                              "Clear the chat history.")
        self.register_command("/exit", self.exit_command,
                              "Exit the chatbot.")
        self.register_command("/help", self.help_command,
                              "Display help with available commands.")
        self.register_command("/$", self.run_system_command,
                              "Run shell command.")

    def register_command(self, name, function, description="No description provided."):
        lower_name = name.lower()
        self.command_registry[lower_name] = {"func": function, "description": description}

    def display(self, inform, text):
        self.console.print(f"[{self.style_dict[inform]}]{text}[/{self.style_dict[inform]}]")
        return False

    def prompt_file_selection(self):
        current_path = Path.cwd()
        selected_index = 0
        scroll_offset = 0
        show_hidden = False

        terminal_height = os.get_terminal_size().lines
        max_display_lines = terminal_height - 4

        files = []

        def update_file_list():
            nonlocal files, selected_index, scroll_offset
            all_entries = [Path("..")] + sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            files = []
            for entry in all_entries:
                if show_hidden is False and entry.name.startswith('.') and entry != Path(".."):
                    continue
                files.append(entry)
            selected_index = 0
            scroll_offset = 0
            return files

        files = update_file_list()

        def get_display_text():
            text_lines = []
            visible_files = files[scroll_offset:scroll_offset + max_display_lines]
            for idx, file_entry in enumerate(visible_files):
                real_idx = scroll_offset + idx
                if real_idx == selected_index:
                    prefix = "> "
                else:
                    prefix = "  "
                if file_entry == Path(".."):
                    display_name = ".."
                else:
                    display_name = file_entry.name
                    if file_entry.is_dir():
                        display_name = display_name + "/"
                text_lines.append(( "yellow" if real_idx == selected_index else "white", prefix + display_name + "\n"))
            return text_lines

        key_bindings = KeyBindings()

        @key_bindings.add("up")
        def move_up(event):
            nonlocal selected_index, scroll_offset
            selected_index = selected_index - 1
            if selected_index < 0:
                selected_index = len(files) - 1
            if selected_index < scroll_offset:
                scroll_offset = scroll_offset - 1
                if scroll_offset < 0:
                    scroll_offset = 0

        @key_bindings.add("down")
        def move_down(event):
            nonlocal selected_index, scroll_offset
            selected_index = selected_index + 1
            if selected_index >= len(files):
                selected_index = 0
            if selected_index >= scroll_offset + max_display_lines:
                scroll_offset = scroll_offset + 1

        @key_bindings.add("enter")
        def enter_directory(event):
            nonlocal current_path
            selected_file = files[selected_index]
            if selected_file == Path(".."):
                current_path = current_path.parent
                update_file_list()
            elif selected_file.is_dir():
                current_path = selected_file
                update_file_list()
            elif selected_file.is_file():
                event.app.exit(result=str(selected_file))

        @key_bindings.add("escape")
        def cancel_selection(event):
            event.app.exit(result=None)

        @key_bindings.add("c-h")
        def toggle_hidden(event):
            nonlocal show_hidden
            show_hidden = not show_hidden
            update_file_list()

        header_window = Window(content=FormattedTextControl(lambda: f"Current Directory: {current_path}"), height=1)
        list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False, height=max_display_lines)
        footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to toggle hidden files. Escape to exit."), height=1, style=self.style_dict['footer'])
        layout = Layout(HSplit([Frame(header_window), list_window, footer_window]))

        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True, refresh_interval=0.1)
        file_path = app.run()
        return file_path

    def replace_file_references(self, text):
        def file_replacement(match):
            file_path_str = match.group(1)
            if file_path_str is None:
                file_path_str = ""
            file_path_str = file_path_str.strip()
            file_path = Path(os.path.expanduser(file_path_str))
            if file_path.is_file() is False:
                file_path_str = self.prompt_file_selection()
                if file_path_str is None:
                    self.display("highlight", "Selection cancelled.")
                    return None
                file_path = Path(file_path_str)
            try:
                file_text = extract_text(file_path)
                return "```" + file_text.strip() + "```"
            except Exception as error:
                self.display("error", "Error reading file " + str(file_path) + ":\n" + str(error))
                return "[Error: could not read file " + str(file_path) + "]"

        new_text = re.sub(r"/file\s*([^\s]+)?", lambda m: file_replacement(m) or "[Cancelled]", text)
        if "[Cancelled]" in new_text:
            return None
        return new_text

    # Command methods
    def show_model_command(self, contents=None):
        self.display("highlight", "Currently configured model: " + self.config.get("model"))
        return False

    def theme_command(self, contents=None):
        theme_names = list(themes.keys())
        theme_names.sort()
        selected_index = 0
        if self.config.get("theme") in theme_names:
            selected_index = theme_names.index(self.config.get("theme"))

        def get_display_text():
            text_lines = []
            for index, name in enumerate(theme_names):
                if index == selected_index:
                    prefix = "> "
                    style_str = "bold yellow"
                else:
                    prefix = "  "
                    style_str = "white"
                text_lines.append((style_str, prefix + name + "\n"))
            return text_lines

        key_bindings = KeyBindings()

        @key_bindings.add("up")
        def move_up(event):
            nonlocal selected_index
            selected_index = selected_index - 1
            if selected_index < 0:
                selected_index = len(theme_names) - 1

        @key_bindings.add("down")
        def move_down(event):
            nonlocal selected_index
            selected_index = selected_index + 1
            if selected_index >= len(theme_names):
                selected_index = 0

        @key_bindings.add("enter")
        def select_theme(event):
            nonlocal selected_index
            chosen_theme = theme_names[selected_index]
            self.config["theme"] = chosen_theme
            self.save_config({"theme": chosen_theme})
            self._setup_theme()
            self.display("output", "Theme set: " + chosen_theme)
            event.app.exit()

        @key_bindings.add("escape")
        def cancel_selection(event):
            self.display("highlight", "Theme selection cancelled.")
            event.app.exit()

        layout = Layout(HSplit([Frame(Window(content=FormattedTextControl(get_display_text), wrap_lines=False))]))
        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True)
        app.run()
        return False

    def file_command(self, contents=""):
        processed_text = self.replace_file_references("/file" + contents)
        if processed_text is None:
            self.display("highlight", "File selection cancelled or not processed.")
        return False

    def system_command(self, contents=None):
        self.display("highlight", "Editing system prompt (Vim mode enabled):")
        key_bindings = KeyBindings()

        @key_bindings.add("escape", "enter")
        def submit(event):
            event.app.current_buffer.validate_and_handle()

        session = PromptSession(vi_mode=True, multiline=True, key_bindings=key_bindings)
        try:
            new_prompt = session.prompt(">>> ", default=self.config.get("system_prompt")).strip()
            if new_prompt != "":
                self.config["system_prompt"] = new_prompt
                self.display("output", "System prompt updated to:\n" + new_prompt)
                self.save_config({"system_prompt": new_prompt, "model": self.config.get("model")})
            else:
                self.display("error", "System prompt cannot be empty!")
        except KeyboardInterrupt:
            self.display("error", "Cancelled system prompt editing.")
        return False

    def show_system_command(self, contents=None):
        self.display("highlight", "Current system prompt:\n" + self.config.get("system_prompt"))
        return False

    def history_command(self, contents=None):
        if len(self.messages) == 0:
            self.display("highlight", "No chat history available.")
        else:
            for msg in self.messages:
                if msg["role"] == "user":
                    role_text = "[bold green]" + self.config.get("username") + ":[/bold green]"
                else:
                    role_text = "[bold blue]Assistant:[/bold blue]"
                self.console.print(role_text)
                self.console.print(Markdown(msg["content"]))
        return False

    def models_command(self, contents=None):
        """Display and select from available AI models with enhanced navigation."""
        models_list = self.ai.list(["openai", "ollama", "nvidia"])
        models_list.sort()
        selected_index = 0
        visible_start = 0
        terminal_height = os.get_terminal_size().lines
        page_size = terminal_height - 4  # Adjust for header/footer/padding
        visible_end = min(page_size, len(models_list))

        def get_display_text():
            text_lines = []
            for i in range(visible_start, min(visible_end, len(models_list))):
                if i == selected_index:
                    prefix = "> "
                    style_str = "bold yellow"
                else:
                    prefix = "  "
                    style_str = "white"
                text_lines.append((style_str, prefix + models_list[i] + "\n"))
            return text_lines

        key_bindings = KeyBindings()

        @key_bindings.add("up")
        def move_up(event):
            nonlocal selected_index, visible_start, visible_end
            if selected_index > 0:
                selected_index -= 1
                if selected_index < visible_start:
                    visible_start -= 1
                    visible_end = min(visible_end - 1, len(models_list))

        @key_bindings.add("down")
        def move_down(event):
            nonlocal selected_index, visible_start, visible_end
            if selected_index < len(models_list) - 1:
                selected_index += 1
                if selected_index >= visible_end:
                    visible_start += 1
                    visible_end = min(visible_end + 1, len(models_list))

        @key_bindings.add("pageup")
        def page_up(event):
            nonlocal selected_index, visible_start, visible_end
            if visible_start > 0:
                visible_start = max(0, visible_start - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = max(visible_start, selected_index - page_size)
                if selected_index >= len(models_list):
                    selected_index = len(models_list) - 1

        @key_bindings.add("pagedown")
        def page_down(event):
            nonlocal selected_index, visible_start, visible_end
            if visible_end < len(models_list):
                visible_start = min(visible_start + page_size, len(models_list) - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = min(selected_index + page_size, len(models_list) - 1)
                if selected_index < visible_start:
                    selected_index = visible_start

        @key_bindings.add("space")
        def space_page_down(event):
            nonlocal selected_index, visible_start, visible_end
            if visible_end < len(models_list):
                visible_start = min(visible_start + page_size, len(models_list) - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = min(selected_index + page_size, len(models_list) - 1)
                if selected_index < visible_start:
                    selected_index = visible_start

        @key_bindings.add("enter")
        def select_model(event):
            chosen_model = models_list[selected_index]
            self.config["model"] = chosen_model
            self.display("highlight", "Selected model: " + chosen_model)
            self.save_config({"model": chosen_model, "system_prompt": self.config.get("system_prompt")})
            event.app.exit()

        @key_bindings.add("escape")
        def cancel_selection(event):
            self.display("highlight", "Model selection cancelled.")
            event.app.exit()

        layout = Layout(HSplit([Frame(Window(content=FormattedTextControl(get_display_text), wrap_lines=False))]))
        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True, refresh_interval=0.1)
        app.run()
        return False

    def settings_command(self, contents=None):
        args = []
        if contents is not None:
            args = contents.strip().split()
        if len(args) == 0:
            current_settings = {
                "model": self.config.get("model"),
                "system_prompt": self.config.get("system_prompt"),
                "theme": self.config.get("theme"),
                "markdown": self.config.get("markdown"),
                "username": self.config.get("username"),
                "stream": self.config.get("stream"),
                "tools": self.config.get("tools"),
                "memory": self.config.get("memory")
            }
            table = Table(title="Current Configuration Settings",
                          show_header=True,
                          header_style=self.style_dict["highlight"],
                          expand=True)
            table.add_column("Setting", style=self.style_dict["prompt"], ratio=1)
            table.add_column("Value", ratio=3)
            for key, value in current_settings.items():
                table.add_row(key, str(value))
            self.console.print(table)
        elif len(args) >= 2:
            key_setting = args[0]
            value_setting = " ".join(args[1:])
            bool_map = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
            if key_setting == "model":
                self.config["model"] = value_setting
            elif key_setting == "system_prompt":
                self.config["system_prompt"] = value_setting
            elif key_setting == "theme" and value_setting in themes:
                self.config["theme"] = value_setting
                self._setup_theme()
            elif key_setting == "username":
                self.config["username"] = value_setting
            elif key_setting == "markdown":
                self.config["markdown"] = bool_map.get(value_setting.lower(), self.config.get("markdown"))
            elif key_setting == "tools":
                self.config["tools"] = bool_map.get(value_setting.lower(), self.config.get("tools"))
            elif key_setting == "stream":
                self.config["stream"] = bool_map.get(value_setting.lower(), self.config.get("stream"))
            elif key_setting == "memory":
                self.config["memory"] = bool_map.get(value_setting.lower(), self.config.get("memory"))
            else:
                self.display("error", "Invalid setting key: " + key_setting)
                return False
            self.save_config(self.config)
            self.display("highlight", "Updated " + key_setting + " to: " + value_setting)
        else:
            self.display("error", "Invalid command usage. Use /settings <key> <value>.")
        return False

    def flush_command(self, contents=None):
        self.messages.clear()
        self.display("highlight", "Chat history has been flushed.")
        return False

    def exit_command(self, contents=None):
        self.display("footer", "\nExiting!")
        sys.exit(0)
        return True

    def help_command(self, contents=None):
        table = Table(title="Available Commands",
                      show_header=True,
                      header_style=self.style_dict["highlight"],
                      expand=True)
        table.add_column("Command", style=self.style_dict["prompt"], ratio=1)
        table.add_column("Description", ratio=3)
        for command_name, info in sorted(self.command_registry.items()):
            table.add_row(command_name, info["description"])
        self.console.print(table)
        return False

    def extract_code_blocks(self, text):
        pattern = r"```(?:\w+\n)?([\s\S]*?)```"
        return re.findall(pattern, text)

    def ask_ai(self, text, stream_mode=True, code_exec=False):
        text = self.replace_file_references(text)
        if text is None:
            return None

        self.messages.append({"role": "user", "content": text})
        request_messages = [{"role": "system", "content": self.config.get("system_prompt")}] + self.messages
        response_text = ""
        live = None

        if self.config.get("markdown") is True:
            live = Live(console=self.console, refresh_per_second=100)
            live.start()

        provider = ""
        model_name = ""
        if ":" in self.config.get("model"):
            provider, model_name = self.config.get("model").split(":", 1)

        client = None
        if self.config.get("model").startswith("openai"):
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        elif self.config.get("model").startswith("ollama"):
            client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

        try:
            stream_response = client.chat.completions.create(
                model=model_name,
                messages=request_messages,
                stream=stream_mode,
            )
            for chunk in stream_response:
                content = chunk.choices[0].delta.content
                if content is not None:
                    response_text = response_text + content
                    if self.config.get("markdown") is True and live is not None:
                        live.update(Markdown(response_text))
                    else:
                        self.console.print(content, end='')
        except Exception as error:
            self.display("error", "Client error: " + str(error))
            return "An error occurred while communicating with the LLM."

        self.messages.append({"role": "assistant", "content": response_text.strip()})

        if live is not None and live.is_started:
            live.stop()

        if code_exec:
            code_blocks = self.extract_code_blocks(response_text)
            if code_blocks:
                for code in code_blocks:
                    code = code.strip()
                    self.display("highlight", "\n\nWould you like to run the following?")
                    self.display("output", code)
                    answer = Confirm.ask("Do you want to continue?\n[y/n]: ")
                    if answer:
                        self.run_system_command(code)
        return response_text.strip()

    def run_system_command(self, command_text=None):
        try:
            result = subprocess.run(
                command_text,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash"
            )
            output_text = ""
            self.console.print(Rule())
            if result.stdout:
                output_text = output_text + result.stdout
                self.console.print("\n" + result.stdout + "\n")
            if result.stderr:
                output_text = output_text + result.stderr
                self.console.print("\n" + result.stderr + "\n")
            self.console.print(Rule())
            self.messages.append({"role": "user", "content": "$ " + command_text + "\n" + output_text.strip()})
        except Exception as error:
            error_message = "Command execution error: " + str(error)
            self.display("error", error_message)
            self.messages.append({"role": "user", "content": "$ " + command_text + "\n" + error_message})
        return False

    def get_system_context(self):
        os_name = platform.system()
        os_version = platform.release()
        os_full_name = platform.platform()
        now = datetime.datetime.now()
        local_time = now.strftime("%Y-%m-%d %H:%M:%S")
        try:
            timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzname()
        except Exception:
            timezone = "Unknown"
        user_name = getpass.getuser()
        hostname = platform.node()
        current_directory = os.getcwd()
        architecture = platform.machine()
        python_version = platform.python_version()

        hardware_model = "Unknown"
        chip = "Unknown"
        memory_str = "Unknown"
        if os_name == "Darwin":
            try:
                hardware_model_raw = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()
                profiler_output = subprocess.check_output(["system_profiler", "SPHardwareDataType"], text=True)
                model_match = re.search(r"Model Name: (.*)", profiler_output)
                size_match = re.search(r"Model Identifier:.*(\d+-inch)", profiler_output)
                date_match = re.search(r"Model Identifier:.*(\d{4})", profiler_output)
                if model_match is not None:
                    model_name = model_match.group(1)
                else:
                    model_name = "MacBook"
                if size_match is not None:
                    size = size_match.group(1)
                else:
                    size = ""
                if date_match is not None:
                    date = date_match.group(1)
                else:
                    date = ""
                if size and date:
                    hardware_model = model_name + " (" + size + ", " + date + ")"
                else:
                    hardware_model = hardware_model_raw
                chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
                memory_raw = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
                memory_str = str(round(int(memory_raw) / (1024 ** 3))) + " GB"
                os_product = subprocess.check_output(["sw_vers", "-productName"], text=True).strip()
                os_version_full = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()
                os_build = subprocess.check_output(["sw_vers", "-buildVersion"], text=True).strip()
                os_full_name = os_product + " " + os_version_full + " (Build " + os_build + ")"
            except subprocess.CalledProcessError:
                hardware_model = "macOS (model unavailable)"
                chip = "macOS (chip unavailable)"
                memory_str = "macOS (memory unavailable)"
        elif os_name == "Linux":
            try:
                with open("/sys/devices/virtual/dmi/id/product_name", "r") as file_object:
                    hardware_model = file_object.read().strip()
            except FileNotFoundError:
                hardware_model = "Linux (model unavailable)"
        elif os_name == "Windows":
            hardware_model = platform.uname().machine

        shell = "Unknown"
        if os_name in ["Linux", "Darwin"]:
            shell = os.environ.get("SHELL", "Unknown")
            shell = os.path.basename(shell)
        elif os_name == "Windows":
            shell = os.environ.get("COMSPEC", "cmd.exe")
            shell = os.path.basename(shell)
            if "powershell" in sys.executable.lower() or "PS1" in os.environ:
                shell = "powershell"

        context = (
            "The following information is for reference only.\n"
            "```\n"
            "System Context:\n"
            "- Operating System: " + os_full_name + "\n"
            "- Hardware Model: " + hardware_model + "\n"
            "- Chip: " + chip + "\n"
            "- Memory: " + memory_str + "\n"
            "- Date and Time: " + local_time + "\n"
            "- Timezone: " + timezone + "\n"
            "- User: " + user_name + "@" + hostname + "\n"
            "- Current Working Directory: " + current_directory + "\n"
            "- Shell: " + shell + "\n"
            "- Architecture: " + architecture + "\n"
            "- Python Version: " + python_version + "\n"
            "```\n"
        )
        return context

    def handle_command(self, command_text):
        parts = command_text.split(" ", 1)
        command_name = parts[0].strip().lower()
        contents = ""
        if len(parts) > 1:
            contents = parts[1]
        if command_name in self.command_registry:
            return self.command_registry[command_name]["func"](contents)
        return False

    def run(self):
        memory_enabled = self.config.get("memory")
        if memory_enabled:
            from .memory import Memory
            memory_obj = Memory(db=str(self.memory_db_path))
        else:
            memory_obj = None

        # Set system prompt for interactor (without extra context here)
        self.ai.set_system(self.config.get("system_prompt"))

        # Handle command-line arguments or piped input mode
        command_input = False
        user_input = ""
        piped_input = ""
        if len(sys.argv) > 1:
            command_input = True
            user_input = " ".join(sys.argv[1:]).strip()
        if not sys.stdin.isatty():
            command_input = True
            piped_input = sys.stdin.read().strip()

        if command_input:
            if user_input.startswith("/") or piped_input.startswith("/"):
                self.handle_command(user_input or piped_input)
                return
            query = ""
            if user_input != "":
                query = user_input
            if piped_input != "":
                if user_input != "":
                    query = user_input + "\n\n```\n" + piped_input + "\n```\n"
                else:
                    query = piped_input

            query = self.replace_file_references(query)
            response = self.ai.interact(
                query,
                model=self.config.get("model"),
                tools=self.config.get("tools"),
                stream=self.config.get("stream"),
                markdown=self.config.get("markdown")
            )
            self.console.print()
            return

        # Interactive mode
        key_bindings = KeyBindings()

        @key_bindings.add("escape", "enter")
        def submit_event(event):
            event.app.current_buffer.validate_and_handle()

        @key_bindings.add("/")
        def insert_slash(event):
            event.app.current_buffer.insert_text("/")

        @key_bindings.add("c-c")
        def exit_on_ctrl_c(event):
            self.display("footer", "\nExiting!")
            sys.exit(0)

        history = InMemoryHistory()
        session = PromptSession(
            key_bindings=key_bindings,
            style=self.get_prompt_style(),
            vi_mode=True,
            history=history
        )

        while True:
            try:
                user_input = session.prompt(
                    [("class:prompt", ">>> ")],
                    multiline=True,
                    prompt_continuation="... ",
                    style=self.get_prompt_style()
                )
                self.console.print()
                self.ai.set_system(self.config.get("system_prompt") + "\n")
                user_input = self.replace_file_references(user_input)
                if user_input is None or user_input.strip() == "":
                    continue
                if user_input.startswith("/"):
                    should_exit = self.handle_command(user_input)
                    if should_exit:
                        break
                else:
                    if memory_enabled and memory_obj is not None:
                        memories = memory_obj.search(query=user_input, limit=10)
                        memories_str = ""
                        for entry in memories.get("results", []):
                            memories_str = memories_str + "- " + entry.get("content", "") + "\n"
                        new_system = self.config.get("system_prompt") + "\nUse the following memories to help answer if applicable.\n" + memories_str
                        self.ai.set_system(new_system)
                    self.messages.append({"role": "user", "content": user_input})
                    response = self.ai.interact(
                        user_input,
                        model=self.config.get("model"),
                        tools=self.config.get("tools"),
                        stream=self.config.get("stream"),
                        markdown=self.config.get("markdown")
                    )
                    self.messages.append({"role": "assistant", "content": response})
                    if memory_enabled and memory_obj is not None:
                        memory_obj.add("user: " + user_input)
                        memory_obj.add("assistant: " + response)
                    self.console.print("\n")
            except KeyboardInterrupt:
                self.display("footer", "\nExiting!")
                sys.exit(0)
            except EOFError:
                self.display("footer", "\nExiting!")
                sys.exit(0)
            except Exception as error:
                self.display("error", "Unexpected error: " + str(error))
                continue


def global_signal_handler(sig, frame):
    print("\nCtrl+C caught globally, performing cleanup...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, global_signal_handler)
    chatbot = Chatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
