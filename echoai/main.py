#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: Main module for the EchoAi chatbot
#              plication providing CLI interface and
#              command handling
# Created: 2025-03-28 16:21:59
# Modified: 2025-05-05 14:06:14

import sys
import os
import re
import json
import subprocess
import platform
import signal
import datetime
import getpass
import importlib.util
import inspect
import shlex

from pathlib import Path

from openai import OpenAI

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application, run_in_terminal
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Dialog, TextArea, Button, Label, Frame
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.dimension import Dimension as D

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.prompt import Confirm
from rich.rule import Rule
from rich import box

console = Console()
print = console.print

from pii import extract, extract_text

# Local module imports
from .lib.interactor import Interactor
from .lib.session import Session
from .lib.themes import THEMES
from .tools import task_manager

# TUI Modules

class Chatbot:
    """Main chatbot class that handles user interactions, commands, and AI responses.
    
    This class manages the configuration, user interface, and interaction with the AI model.
    It provides a command-line interface with various commands for controlling the chatbot's
    behavior and appearance.
    """
    def __init__(self):
        """Initialize the chatbot with default settings and configurations.
        
        Sets up the command registry, loads configuration, initializes the AI interactor,
        sets up the theme, and registers tool functions and commands.
        """
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
        self.prompt_history_path = self.ECHOAI_DIR / ".history"
        self.session_directory = self.ECHOAI_DIR / "sessions"
        self.session = Session(directory=self.session_directory)
        self.session_id_lookup = {}
        self.refresh_session_lookup()
        self._initialize_directories()
        self.load_config()
        self.ai = Interactor(
            model=self.config.get("model"),
            context_length=120000,
            session_enabled=True,
            session_path=self.session_directory,
        )
        self._setup_theme()
        self._register_tool_functions()
        self._register_commands()
        self.memory = None

    def _initialize_directories(self):
        """Create necessary directories for the chatbot if they don't exist.
        
        Ensures that the .echoai directory exists in the user's home directory.
        """
        if not self.ECHOAI_DIR.exists():
            self.ECHOAI_DIR.mkdir(exist_ok=True)

    def load_config(self):
        """Load configuration settings from the config file.
        
        Reads settings from the config file if it exists, otherwise uses default settings.
        Updates the current configuration with values from the file.
        """
        if self.CONFIG_PATH.exists():
            with self.CONFIG_PATH.open("r") as file_object:
                config_from_file = json.load(file_object)
            self.config = self.default_config.copy()
            self.config.update(config_from_file)
        else:
            self.config = self.default_config.copy()
            self.save_config(self.config)

    def save_config(self, new_config):
        """Save configuration settings to the config file.
        
        Args:
            new_config (dict): Dictionary containing configuration settings to update.
            
        Updates the existing configuration with new values and writes them to the config file.
        Then reloads the configuration to ensure all settings are up to date.
        """
        current_config = self.default_config.copy()
        if self.CONFIG_PATH.exists():
            with self.CONFIG_PATH.open("r") as file_object:
                current_config.update(json.load(file_object))
        current_config.update(new_config)
        with self.CONFIG_PATH.open("w") as file_object:
            json.dump(current_config, file_object, indent=4)
        self.load_config()


    def refresh_session_lookup(self):
        """Populate name → id map for session lookup."""
        self.session_id_lookup = {
            f"{s.get('name', 'unnamed')} ({s['id'][:8]})": s["id"]
            for s in self.session.list()
        }

    def _setup_theme(self):
        """Set up the visual theme for the chatbot interface.
        Loads the selected theme from configuration or falls back to the default theme
        if the selected theme is not available. Updates the style dictionary used for
        rendering the interface.
        """
        selected_theme = self.config.get("theme", self.default_config["theme"])
        if selected_theme in THEMES:
            self.style_dict = THEMES[selected_theme]
        else:
            self.style_dict = THEMES["default"]

    def get_prompt_style(self):
        """Return the style dictionary for the prompt interface.
        
        Returns:
            Style: A prompt_toolkit Style object configured with the current theme's
                  prompt and input styles.
        """
        return Style.from_dict({
            'prompt': self.style_dict["prompt"],
            '': self.style_dict["input"]
        })

    def _register_tool_functions(self):
        # Load the global textextract function for reading files
        self.ai.add_function(extract_text)

        # Dynamically load and register tool functions from the tools/ directory.
        tools_dir = Path(__file__).parent / "tools"

        if not tools_dir.exists():
            self.display("warning", f"Tools directory does not exists: {tools_dir}")
            return

        for file in tools_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue

            module_name = f"tools.{file.stem}"
            module_path = str(file)

            try:
                # Load module from file
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get top-level callable function(s)
                functions = [
                    obj for name, obj in inspect.getmembers(module)
                    if inspect.isfunction(obj)
                    and obj.__module__ == module.__name__
                    and not name.startswith("_")
                ]


                if not functions:
                    self.display("warning", f"No function found in {file.name}")
                    continue

                for func in functions:
                    self.ai.add_function(func)
                    #self.display("info", f"Registered tool: {func.__name__} from {file.name}")

            except Exception as e:
                self.display("error", f"Filed to load {file.name}: {str(e)}")

    def tools_command(self, contents=None):
        """Display available tools in a formatted table."""
        table = Table(title="Available Tools", box=box.SQUARE, show_lines=True, header_style="bold " + self.style_dict["highlight"], expand=True)
        table.add_column("Tool Name", style=self.style_dict["prompt"], ratio=1)
        table.add_column("Description", ratio=3)
        
        # Get tool functions from the AI interactor
        for func in self.ai.get_functions():
            table.add_row(func["function"]["name"], func['function']['description'])
        
        print(table)
        return False


    def _register_commands(self):
        """Register all available slash commands with execution logic and autocomplete metadata."""

        self.register_command(
            "/show_model",
            func=self.show_model_command,
            description="Show the currently configured AI model."
        )

        self.register_command(
            "/theme",
            func=self.theme_command,
            description="Select the theme to use for the application."
        )

        self.register_command(
            "/file",
            func=self.file_command,
            description="Insert the contents of a file for analysis."
        )

        self.register_command(
            "/system",
            func=self.system_command,
            description="Set a new system prompt."
        )

        self.register_command(
            "/show_system",
            func=self.show_system_command,
            description="Show the current system prompt."
        )

        self.register_command(
            "/history",
            func=self.history_command,
            description="Show the chat history."
        )

        self.register_command(
            "/models",
            func=self.models_command,
            description="Select the AI model to use."
        )

        self.register_command(
            "/settings",
            func=self.settings_command,
            description="Display or modify the current configuration settings."
        )

        self.register_command(
            "/incognito",
            func=self.incognito_command,
            description="Switch to incognito mode (temporary session)."
        )

        self.register_command(
            "/exit",
            func=self.exit_command,
            description="Exit the chatbot."
        )

        self.register_command(
            "/help",
            func=self.help_command,
            description="Display help with available commands."
        )

        self.register_command(
            "/tokens",
            func=self.tokens_command,
            description="Display the total number of tokens in the message history."
        )

        self.register_command(
            "/$",
            func=self.run_system_command,
            description="Run shell command."
        )

        self.register_command(
            "/tools",
            func=self.tools_command,
            description="Display available tools in a table format."
        )

        self.register_command(
            "/remember",
            func=self.remember_command,
            description="Save content to vector memory."
        )

        self.register_command(
            "/recall",
            func=self.recall_command,
            description="Recall information from vector memory."
        )

        self.register_command(
            "/task",
            func=self.task_command,
            description="Manage and view assistant tasks.",
            subcommands=["add", "list", "edit", "delete", "mark"],
            args={
                "edit": lambda: [t["id"] for t in task_manager.task_list()["result"]],
                "delete": lambda: [t["id"] for t in task_manager.task_list()["result"]],
                "mark": lambda: [t["id"] for t in task_manager.task_list()["result"]],
            }
        )

        self.register_command(
            "/session_tui",
            func=self.session_tui_command,
            description="Session Manger TUI",
        )

        self.register_command(
            "/session",
            func=self.session_command,
            description="Manage chat sessions.",
            subcommands=[
                "branch", "delete", "list", "load", "new",
                "rename", "search", "searchmeta", "summary", "tag"
            ],
            args={
                "load": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                ),
                "delete": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                ),
                "rename": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                ),
                "summary": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                ),
                "tag": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                ),
                "branch": lambda: sorted(
                    f"{s.get('name', 'unnamed')} ({s['id'][:8]})"
                    for s in self.session.list()
                )
            }
        )


    def register_command(
        self,
        name: str,
        func: callable,
        description: str = "No description provided.",
        subcommands: list = None,
        args: dict = None
    ):
        """
        Register a command with metadata for execution and autocompletion.

        Args:
            name (str): Slash command (e.g. "/task")
            func (callable): Function to call when command is triggered
            description (str): Description for /help output
            subcommands (list[str], optional): List of valid subcommands (sorted alphabetically)
            args (dict[str, callable], optional): Map of subcommand -> argument generator function
        """
        name = name.lower()

        if not callable(func):
            raise ValueError(f"Command '{name}' must include a valid 'func' callable.")

        if subcommands:
            subcommands = sorted(subcommands)

        self.command_registry[name] = {
            "func": func,
            "description": description,
            "subcommands": subcommands or [],
            "args": args or {}
        }

    def display(self, inform, text):
        """Display formatted text to the user using the current theme's styles.
        
        Args:
            inform (str): The style key to use from the current theme's style dictionary.
            text (str): The text to display.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        print(f"[{self.style_dict[inform]}]{text}[/{self.style_dict[inform]}]")
        return False

    def prompt_file_selection(self):
        """Provide an interactive file browser interface for selecting files.
        
        Creates a terminal-based file browser that allows users to navigate directories
        and select files. Supports navigation with arrow keys, showing/hiding hidden files,
        and canceling the selection.
        
        Returns:
            str or None: The path to the selected file as a string, or None if selection was canceled.
        """
        from .tui.file_selector import FileSelector
        fs = FileSelector(theme=self.config.get("theme"))
        selected_file = fs.run()
        return selected_file

    def replace_file_references(self, text):
        """Replace file references in text with the contents of the referenced files.
        
        Args:
            text (str): The text containing file references in the format '/file [path]'.
            
        Returns:
            str or None: The text with file references replaced by file contents,
                        or None if file selection was canceled.
        """
        def file_replacement(match):
            file_path_str = match.group(1)
            if file_path_str is None:
                file_path_str = ""
            file_path_str = file_path_str.strip()
            file_path = Path(os.path.expanduser(file_path_str))

            # Skip interactive prompt if not in a terminal and no valid file path
            if not sys.stdin.isatty() and not file_path.is_file():
                return "[Error: file selection not available in non-interactive mode]"

            if file_path.is_file() is False:
                file_path_str = self.prompt_file_selection()
                if file_path_str is None:
                    self.display("warning", "Selection cancelled.")
                    return None
                file_path = Path(file_path_str)
            try:
                file_text = extract_text(file_path)
                contents = f"```\n{file_text.strip()}\n```\n"
                return contents
            except Exception as error:
                self.display("error", "Error reading file " + str(file_path) + ":\n" + str(error))
                return "[Error: could not read file " + str(file_path) + "]"

        new_text = re.sub(r"/file\s*([^\s]+)?", lambda m: file_replacement(m) or "[Cancelled]", text)
        if "[Cancelled]" in new_text:
            return None
        return new_text

    # Command methods
    def show_model_command(self, contents=None):
        """Display the currently configured AI model.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        if self.config.get("model") is None:
            self.display("warning", "Model is not configured.")
        else:
            self.display("info", "Currently configured model: " + self.config.get("model"))

        return False

    def theme_command(self, contents=None):
        """Provide an interactive interface for selecting a theme for the chatbot.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        from .tui.theme_selector import ThemeSelector
        ts = ThemeSelector(self.config.get("theme"))
        selected_theme = ts.run()
        if selected_theme:
            self.config["theme"] = selected_theme
            self.save_config({"theme": selected_theme})
            self._setup_theme()
            self.display("success", "Theme set: " + selected_theme)
        else:
            self.display("info", "Theme unchanged: " + self.config.get("theme"))

        return False

    def file_command(self, contents=""):
        """Process file references in the command contents.
        
        Args:
            contents (str, optional): Text containing file references to process.
                Defaults to an empty string.
                
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        processed_text = self.replace_file_references(contents)
        if processed_text is None:
            self.display("warning", "File selection cancelled or not processed.")
        return False

    def system_command(self, contents=None):
        """Provide an interface for editing the system prompt for the AI.
        
        Opens a Vim-like editor for modifying the system prompt that controls
        the AI's behavior and personality.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        self.display("info", "Editing system prompt (Vim mode enabled):")
        key_bindings = KeyBindings()

        @key_bindings.add("escape", "enter")
        def submit(event):
            event.app.current_buffer.validate_and_handle()

        session = PromptSession(vi_mode=True, multiline=True, key_bindings=key_bindings)
        try:
            new_prompt = session.prompt(">>> ", default=self.config.get("system_prompt")).strip()
            if new_prompt != "":
                self.config["system_prompt"] = new_prompt
                self.display("success", "System prompt updated to:\n" + new_prompt)
                self.save_config({"system_prompt": new_prompt, "model": self.config.get("model")})
            else:
                self.display("error", "System prompt cannot be empty!")
        except KeyboardInterrupt:
            self.display("warning", "Cancelled system prompt editing.")
        return False

    def show_system_command(self, contents=None):
        """Display the current system prompt in a formatted table.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        # Create a header with a title
        print(Rule("[bold]System Prompt[/bold]", style=self.style_dict["highlight"], align="left"))
        
        # Create a table for the system prompt content
        table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 1))
        table.add_column("Content", overflow="fold")
        table.add_row(self.config.get("system_prompt"))
        
        # Print the table
        print(table)
        
        # Add a footer
        print(Rule(style=self.style_dict["footer"]))
        return False

    def history_command(self, contents=None):
        """Display the chat history in a formatted table.
        
        Retrieves the message history from the AI interactor and displays it in a
        table with role and content columns. System messages that match the default
        system prompt are skipped.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        self.messages = self.ai.messages_full()
        if not self.messages:
            self.display("warning", "No chat history available.")
        else:
            # Create a header with a title
            print(Rule("[bold]Chat History[/bold]", style=self.style_dict["highlight"], align="left"))
            
            # Create a table for the chat history
            table = Table(show_header=True, box=box.SIMPLE, expand=True, padding=(0, 1))
            table.add_column("Role", style=self.style_dict["prompt"], no_wrap=True)
            table.add_column("Content", style="white", overflow="fold")
            
            # Add each message to the table
            for msg in self.messages:
                # Skip system messages if they're just the default prompt
                if msg["role"] == "system" and msg["content"] == self.config.get("system_prompt"):
                    continue
                    
                # Determine role styling and name
                if msg["role"] == "user":
                    role_style = self.config.get("username")
                elif msg["role"] == "assistant":
                    role_style = "Assistant"
                elif msg["role"] == "system":
                    role_style = "System"
                elif msg["role"] == "tool":
                    role_style = "Tool"
                else:
                    role_style = msg['role'].capitalize()
                
                # Handle content formatting
                if msg["role"] == "tool" and msg["content"]:
                    try:
                        # Try to parse and format JSON content
                        content_data = json.loads(msg["content"])
                        content = f"content: {json.dumps(content_data, indent=2)},\ntool_call_id: {msg["tool_call_id"]}"
                    except json.JSONDecodeError:
                        content = msg["content"]
                else:
                    # Regular message content
                    content = msg["content"] if msg["content"] else ""
                
                # Add the row to the table
                table.add_row(role_style, content)
            
            # Print the table
            print(table)
            
            # Add a footer
            print(Rule(style=self.style_dict["footer"]))
        return False

    def session_tui_command(self, contents=None):
        """
        Launches the Session Manager TUI and loads the selected session if any.

        Returns:
            bool: Always False to continue shell loop.
        """
        from .tui.session_manager import SessionManager
        try:
            sm = SessionManager(self.config.get("theme"))
            session_id = sm.run()
            if session_id:
                self.ai.session_use(session_id)
                self.refresh_session_lookup()
                self.display("success", f"Loaded session from TUI: {session_id[:8]}")
            else:
                self.display("info", "No session selected.")
        except Exception as e:
            self.display("error", f"Session TUI failed: {str(e)}")
        return False

    def session_command(self, contents=None):
        """Manage chat sessions using: /session [list|load|delete|search|rename|tag|branch|summary]"""
        args = shlex.split(contents) if contents else []
        action = args[0] if args else "list"
        rest = args[1:] if len(args) > 1 else []

        def _resolve_session_id(label_parts):
            label = " ".join(label_parts).strip()
            session_id = self.session_id_lookup.get(label)
            if session_id:
                return session_id
            try:
                self.session.load_full(label)
                return label
            except Exception:
                return None

        try:
            if not args:
                full = self.ai.messages_full()
                tokens = self.ai.messages_length()

                role_counts = {r: 0 for r in ["user", "assistant", "system", "tool"]}
                for msg in full:
                    role = msg.get("role", "").lower()
                    if role in role_counts:
                        role_counts[role] += 1

                if self.ai.session_id:
                    try:
                        data = self.session.load_full(self.ai.session_id)
                    except:
                        self.ai.session_reset()
                        self.display("warning", "Session not found. Reverting to incognito.")
                        return False

                    table = Table(title="Current Session", box=box.SIMPLE, show_header=True)
                    table.add_column("Field", style=self.style_dict["prompt"], ratio=2)
                    table.add_column("Value", style="white", ratio=1)
                    table.add_row("ID", data["id"])
                    table.add_row("Name", data.get("name", ""))
                    table.add_row("Created", data["created"])
                    table.add_row("Tags", ", ".join(data.get("tags", [])))
                    table.add_row("Summary", data.get("summary") or "(none)")
                    table.add_row("Total Messages", str(len(full)))
                    table.add_row("User Messages", str(role_counts["user"]))
                    table.add_row("Assistant Messages", str(role_counts["assistant"]))
                    table.add_row("System Messages", str(role_counts["system"]))
                    table.add_row("Tool Messages", str(role_counts["tool"]))
                    table.add_row("Token Count", str(tokens))
                    print(table)
                else:
                    table = Table(title="Incognito Session (Unsaved)", box=box.SIMPLE, show_header=True)
                    table.add_column("Metric", style=self.style_dict["prompt"], ratio=2)
                    table.add_column("Value", style="white", ratio=1)
                    table.add_row("Session Mode", "Incognito")
                    table.add_row("Total Messages", str(len(full)))
                    table.add_row("User Messages", str(role_counts["user"]))
                    table.add_row("Assistant Messages", str(role_counts["assistant"]))
                    table.add_row("System Messages", str(role_counts["system"]))
                    table.add_row("Tool Messages", str(role_counts["tool"]))
                    table.add_row("Token Count", str(tokens))
                    print(table)
                return False

            if action == "list":
                sessions = self.session.list()
                if not sessions:
                    self.display("highlight", "No sessions found.")
                    return False
                table = Table(title="Session List", box=box.SIMPLE, header_style="bold", show_header=True)
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Tags", style="green")
                table.add_column("Summary", style="dim")
                table.add_column("Created", style="white")
                for s in sessions:
                    table.add_row(
                        s["id"][:8],
                        s.get("name", ""),
                        ", ".join(s.get("tags", [])),
                        (s.get("summary") or "")[:60] + "...",
                        s["created"].split("T")[0]
                    )
                print(table)
                return False

            if action == "load":
                session_id = _resolve_session_id(rest)
                if session_id:
                    self.ai.session_use(session_id)
                    self.refresh_session_lookup()
                    self.display("success", f"Switched to session: {session_id[:8]}")
                else:
                    self.display("warning", "Session not found. Reverting to incognito.")
                    self.ai.session_reset()
                return False

            if action == "delete":
                session_id = _resolve_session_id(rest)
                if session_id:
                    self.session.delete(session_id)
                    self.refresh_session_lookup()
                    if self.ai.session_id == session_id:
                        self.ai.session_reset()
                    self.display("success", f"Deleted session: {session_id[:8]}")
                else:
                    self.display("error", "Session not found.")
                return False

            if action == "new":
                if not rest:
                    self.display("error", "Usage: /session new <name>")
                    return False
                name = " ".join(rest)
                sid = self.session.create(name)
                self.ai.session_use(sid)
                self.refresh_session_lookup()
                self.display("success", f"New session created: {sid[:8]} ({name})")
                return False

            if action == "tag":
                if len(rest) < 2:
                    self.display("error", "Usage: /session tag [--remove] <session> <tag1,tag2,...>")
                    return False

                removing = False
                if rest[0] == "--remove":
                    removing = True
                    rest = rest[1:]

                session_id = _resolve_session_id(rest[:-1])
                tags = rest[-1].split(",")

                if not session_id:
                    self.display("error", "Session not found.")
                    return False

                session_data = self.session.load_full(session_id)
                existing_tags = session_data.get("tags", [])

                if removing:
                    updated_tags = [t for t in existing_tags if t not in tags]
                else:
                    updated_tags = list(sorted(set(existing_tags + tags)))

                self.session.update(session_id, "tags", updated_tags)
                self.refresh_session_lookup()
                self.display("success", f"{'Removed' if removing else 'Updated'} tags on session: {session_id[:8]}")
                return False

            if action == "rename":
                if len(rest) != 2:
                    self.display("error", "Usage: /session rename <session> <new name>")
                    return False
                session_id = _resolve_session_id([rest[0]])
                new_name = rest[1]
                if session_id:
                    self.session.update(session_id, "name", new_name)
                    self.refresh_session_lookup()
                    self.display("success", f"Renamed session {session_id[:8]} to: {new_name}")
                else:
                    self.display("error", "Session not found.")
                return False

            if action == "summary":
                session_id = _resolve_session_id(rest)
                if session_id:
                    self.session.summarize(session_id)
                    self.refresh_session_lookup()
                    self.display("success", f"Session summary updated.")
                else:
                    self.display("error", "Session not found.")
                return False

            if action == "branch":
                if len(rest) < 2:
                    self.display("error", "Usage: /session branch <message_id> <branch name>")
                    return False
                if not self.ai.session_id:
                    self.display("error", "Cannot branch in incognito mode.")
                    return False
                message_id = rest[0]
                branch_name = " ".join(rest[1:])
                new_id = self.session.branch(self.ai.session_id, message_id, branch_name)
                self.ai.session_use(new_id)
                self.refresh_session_lookup()
                self.display("success", f"Branched session created: {new_id[:8]}")
                return False

            if action == "search":
                if not rest:
                    self.display("error", "Usage: /session search <terms>")
                    return False
                results = self.session.search(" ".join(rest))
                print(json.dumps(results, indent=2))
                return False

            if action == "searchmeta":
                if not rest:
                    self.display("error", "Usage: /session searchmeta <terms>")
                    return False
                results = self.session.search_meta(" ".join(rest))
                print(json.dumps(results, indent=2))
                return False

            self.display("error", f"Unknown session command: {action}")
            return False

        except Exception as e:
            self.display("error", f"Session command failed: {str(e)}")
            return False

    def task_command(self, contents=None):
        """Manage assistant tasks using: /task [add|edit|delete|mark|list]

        Examples:
            /task add Fix the UI layout bug
            /task delete 91f73b2a
            /task edit 91f73b2a Update the table rendering logic
            /task mark 91f73b2a
            /task list
        """
        args = contents.strip().split() if contents else []
        action = args[0] if args else "list"
        rest = args[1:] if len(args) > 1 else []

        try:
            if action == "add":
                if not rest:
                    self.display("error", "Usage: /task add <task description>")
                    return False
                result = task_manager.task_add(" ".join(rest))
                self.display("success", f"Task added: {result['result']['content']}")

            elif action == "edit":
                if len(rest) < 2:
                    self.display("error", "Usage: /task edit <task_id> <new content>")
                    return False
                tid = rest[0]
                new_content = " ".join(rest[1:])
                result = task_manager.task_update(tid, {"content": new_content})
                if result["status"] == "success":
                    self.display("success", f"Updated: {result['result']['content']}")
                else:
                    self.display("error", result["error"])

            elif action == "delete":
                if not rest:
                    self.display("error", "Usage: /task delete <task_id>")
                    return False
                result = task_manager.task_delete(rest[0])
                if result["status"] == "success":
                    self.display("success", result["result"])
                else:
                    self.display("error", result["error"])

            elif action == "mark":
                if not rest:
                    self.display("error", "Usage: /task mark <task_id>")
                    return False
                result = task_manager.task_complete(rest[0])
                if result["status"] == "success":
                    self.display("success", f"Marked complete: {result['result']['content']}")
                else:
                    self.display("error", result["error"])

            elif action == "list":
                result = task_manager.task_list()
                tasks = result["result"]

                if not tasks:
                    self.display("warning", "No tasks found.")
                    return False

                # Sort tasks from newest to oldest by 'created' datetime
                tasks.sort(key=lambda t: t.get("created", ""), reverse=True)

                table = Table(title="Task List",
                              show_header=True,
                              header_style=self.style_dict["highlight"],
                              expand=True,
                              box=box.SQUARE)

                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Content", style="white")
                table.add_column("Status", style="green")
                table.add_column("Tag", style="magenta")
                table.add_column("Notes", style="yellow")
                table.add_column("Created", style="dim", no_wrap=True)

                for task in tasks:
                    table.add_row(
                        task["id"],
                        task["content"],
                        task["status"],
                        task.get("tag") or "",
                        task.get("notes") or "",
                        task.get("created", "").split("T")[0]
                    )

                print(table)
                self.display("footer", "Available actions: [ add | edit | delete | mark | list ]")

            else:
                self.display("error", f"Unknown task command: {action}")
        except Exception as e:
            self.display("error", f"Task command failed: {str(e)}")

        return False

    def models_command(self, contents=None):
        """Display and select from available AI models with enhanced navigation.
        
        Provides an interactive interface for selecting AI models with keyboard navigation
        and pagination support. Models are displayed in a scrollable list with visual
        indicators for the current selection.
        
        Args:
            contents (str, optional): Additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        from .tui.model_selector import ModelSelector
        ms = ModelSelector(
            theme=self.config.get("theme"),
            default_model=self.config.get("model")
        )
        selected_model = ms.run()
        if selected_model:
            self.config["model"] = selected_model
            self.save_config({"model": selected_model})
            self.display("success", "Model set: " + selected_model)
        else:
            self.display("info", "Model unchanged: " + self.config.get("model"))

        return False

    def settings_command(self, contents=None):
        """Display and modify configuration settings.
        
        Provides functionality to view current settings in a table format and update
        individual settings with new values. Supports boolean, string, and theme settings.
        
        Args:
            contents (str, optional): Space-separated setting key and value to update.
                If not provided, displays current settings.
                
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        args = []
        if contents is not None:
            args = contents.strip().split()
        if len(args) == 0:
            current_settings = {
                "markdown": self.config.get("markdown"),
                "memory": self.config.get("memory"),
                "model": self.config.get("model"),
                "stream": self.config.get("stream"),
                "system_prompt": self.config.get("system_prompt"),
                "theme": self.config.get("theme"),
                "tools": self.config.get("tools"),
                "username": self.config.get("username")
            }
            table = Table(title="Current Configuration Settings",
                          show_header=True,
                          header_style=self.style_dict["highlight"],
                          expand=True)
            table.add_column("Setting", style=self.style_dict["prompt"], ratio=1)
            table.add_column("Value", ratio=3)
            for key, value in current_settings.items():
                table.add_row(key, str(value))
            print(table)
        elif len(args) >= 2:
            key_setting = args[0]
            value_setting = " ".join(args[1:])
            bool_map = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
            if key_setting == "model":
                self.config["model"] = value_setting
            elif key_setting == "system_prompt":
                self.config["system_prompt"] = value_setting
            elif key_setting == "theme" and value_setting in THEMES:
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
            self.display("success", "Updated " + key_setting + " to: " + value_setting)
        else:
            self.display("error", "Invalid command usage. Use /settings <key> <value>.")
        return False

    def incognito_command(self, contents=None):
        """Clear the chat history and display confirmation message.
        
        Flushes all stored messages from the AI interactor's message history
        and displays a confirmation to the user.
        
        Args:
            contents (str, optional): Any additional text passed with the command.
                Not used by this command. Defaults to None.
                
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        self.ai.session_reset()
        self.display(" info", "Switched to incognito mode. History is now temporary.")
        return False

    def exit_command(self, contents=None):
        """Exit the chatbot application.

        Displays an exit message and terminates the program with a status code of 0.

        Args:
            contents (str, optional): Any additional text passed with the command.
                Not used by this command. Defaults to None.

        Returns:
            bool: Always returns True to indicate the program should exit.
        """
        self.display("footer", "\nExiting!")
        sys.exit(0)
        return True

    def tokens_command(self, contents=None):
        """Display the total number of tokens in the message history.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        token_count = self.ai.messages_length()
        self.display("info", f"Current token count in message history: {token_count}")
        return False

    def remember_command(self, contents: str):
        """Stores user-provided content in vector memory."""
        if not contents.strip():
            self.display("error", "Nothing to remember. Usage: /remember <text>")
            return False

        self.memory.create(contents.strip())
        self.display("success", "Memory stored.")
        return False

    def recall_command(self, contents: str):
        """Searches memory vector DB with optional top_k result count."""
        if not contents.strip():
            self.display("error", "Nothing to search. Usage: /recall [top_k] <query>")
            return False

        try:
            parts = contents.strip().split(" ", 1)

            # Check if first part is a digit (limit override)
            if len(parts) == 2 and parts[0].isdigit():
                recall_limit = int(parts[0])
                query = parts[1]
            else:
                recall_limit = 10
                query = contents.strip()

            response = self.memory.search(query=query, limit=recall_limit)
            matches = response.get("results", [])

            if not matches:
                self.display("info", "No relevant memories found.")
                return False

            table = Table(title="Memory Search Results")
            table.add_column("Score", justify="right", style="cyan", no_wrap=True)
            table.add_column("Memory", style="magenta")

            for match in matches:
                score = match.get("score", 0.0)
                text = match.get("content", "")
                table.add_row(f"{score:.4f}", text.replace("\n", " "))

            print(table)
            return False

        except Exception as e:
            self.display("error", f"Memory recall failed: {str(e)}")
            return False



    def help_command(self, contents=None):
        """Display a table of available commands and their descriptions.

        Creates and displays a formatted table showing all registered commands
        and their corresponding descriptions, sorted alphabetically.

        Args:
            contents (str, optional): Any additional text passed with the command.
                Not used by this command. Defaults to None.

        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        table = Table(title="Available Commands",
                      show_header=True,
                      header_style=self.style_dict["highlight"],
                      expand=True)
        table.add_column("Command", style=self.style_dict["prompt"], ratio=1)
        table.add_column("Description", ratio=3)
        for command_name, info in sorted(self.command_registry.items()):
            table.add_row(command_name, info["description"])
        print(table)
        return False

    def run_system_command(self, command_text=None):
        """Execute a system command and handle its output.

        This method runs a shell command using bash, captures both stdout and stderr,
        displays the output, and adds it to the AI's message history.

        Args:
            command_text (str, optional): The shell command to execute. Defaults to None.

        Returns:
            bool: Always returns False to indicate command processing is complete.

        Raises:
            Exception: Catches and handles any exceptions during command execution.
        """
        try:
            result = subprocess.run(
                command_text,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash"
            )
            output_text = ""
            print(Rule())
            if result.stdout:
                output_text = output_text + result.stdout
                print("\n" + result.stdout + "\n")
            if result.stderr:
                output_text = output_text + result.stderr
                print("\n" + result.stderr + "\n")
            print(Rule())
            self.ai.messages_add(role="user", content=output_text.strip())
        except Exception as error:
            error_message = "Command execution error: " + str(error)
            self.display("error", error_message)
            self.ai.messages_add(role="user", content=f"$ {command_text}\n{error_message}")
        return False

    def handle_command(self, command_text):
        """Handle execution of chatbot commands.

        Parses the command text to extract the command name and any additional contents,
        then executes the corresponding command function if it exists in the command registry.

        Args:
            command_text (str): The full command text to process, including the command name
                              and any additional arguments/contents.

        Returns:
            bool: True if the command indicates the program should exit, False otherwise.
                 Most commands return False to continue normal operation.

        Example:
            >>> chatbot.handle_command("/help")  # Executes help command
            False
            >>> chatbot.handle_command("/exit")  # Executes exit command
            True
        """
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
            from .lib.memory import Memory
            self.memory = Memory(db=str(self.memory_db_path))
            self.ai.add_function(self.memory.search, name="memory_search", description="Tool to search vector data base of our chat transcripts using semantic search.")
            self.ai.add_function(self.memory.create, name="memory_create", description="Tool to create and save memories when ask to remember or the context suggests that you should remember something.")
        else:
            self.memory = None

        # Set system prompt for interactor (without extra context here)
        self.ai.messages_system(self.config.get("system_prompt"))

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
                query = user_input + "\n\n```\n" + piped_input + "\n```\n"

            #print(Markdown(query))
            query = self.replace_file_references(query)
            response = self.ai.interact(
                query,
                model=self.config.get("model"),
                tools=self.config.get("tools"),
                stream=self.config.get("stream"),
                markdown=self.config.get("markdown")
            )
            print()
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

        history = FileHistory(self.prompt_history_path)
        session = PromptSession(
            completer=SlashCommandCompleter(self),
            key_bindings=key_bindings,
            style=self.get_prompt_style(),
            vi_mode=True,
            history=history
        )

        response = self.ai.interact(
            "Greet the user and provide an update on any open tasks.",
            model=self.config.get("model"),
            tools=self.config.get("tools"),
            stream=self.config.get("stream"),
            markdown=self.config.get("markdown")
        )
        print("\n")

        while True:
            try:
                user_input = session.prompt(
                    [("class:prompt", ">>> ")],
                    multiline=True,
                    prompt_continuation="... ",
                    style=self.get_prompt_style()
                )
                self.ai.messages_system(self.config.get("system_prompt") + "\n")
                user_input = self.replace_file_references(user_input)
                if user_input is None or user_input.strip() == "":
                    continue
                if user_input.startswith("/"):
                    should_exit = self.handle_command(user_input)
                    if should_exit:
                        break
                else:
                    """
                    if memory_enabled and self.memory is not None:
                        memories = self.memory.search(query=user_input, limit=10)
                        memories_str = ""
                        for entry in memories.get("results", []):
                            memories_str = memories_str + "- " + entry.get("content", "") + "\n"
                        new_system = self.config.get("system_prompt") + "\nUse the following memories to help answer if applicable.\n" + memories_str
                        self.ai.messages_system(new_system)
                    """
                    if not isinstance(self.ai.session_id, str):
                        self.ai.session_id = None

                    response = self.ai.interact(
                        user_input,
                        model=self.config.get("model"),
                        tools=self.config.get("tools"),
                        stream=self.config.get("stream"),
                        markdown=self.config.get("markdown"),
                        session_id=self.ai.session_id
                    )
                    """
                    if memory_enabled and self.memory is not None:
                        self.memory.add("user: " + user_input)
                        self.memory.add("assistant: " + response)
                    """
                    print()
            except KeyboardInterrupt:
                self.display("footer", "\nExiting!")
                sys.exit(0)
            except EOFError:
                self.display("footer", "\nExiting!")
                sys.exit(0)
            except Exception as error:
                self.display("error", "Unexpected error: " + str(error))
                continue

class SlashCommandCompleter(Completer):
    def __init__(self, chatbot):
        self.chatbot = chatbot

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        if not text.strip().startswith("/"):
            return

        parts = text.strip().split()
        if not parts:
            return

        cmd = parts[0]
        cmd_info = self.chatbot.command_registry.get(cmd)

        # Command-level completion
        if len(parts) == 1 and not text.endswith(" "):
            word = parts[0]
            for command in sorted(self.chatbot.command_registry):
                if command.startswith(word):
                    yield Completion(command, start_position=-len(word))
            return

        if not cmd_info:
            return

        # Subcommand-level completion
        if len(parts) == 1 and text.endswith(" "):
            for sub in sorted(cmd_info.get("subcommands", [])):
                yield Completion(sub, start_position=0)
            return

        if len(parts) == 2 and not text.endswith(" "):
            sub_partial = parts[1]
            for sub in sorted(cmd_info.get("subcommands", [])):
                if sub.startswith(sub_partial):
                    yield Completion(sub, start_position=-len(sub_partial))
            return

        # Argument-level completion
        if len(parts) >= 2:
            sub = parts[1]
            arg_provider = cmd_info.get("args", {}).get(sub)
            if callable(arg_provider):
                suggestions = arg_provider()
                arg_partial = parts[2] if len(parts) > 2 else ""
                for val in sorted(suggestions):
                    if val.startswith(arg_partial):
                        yield Completion(val, start_position=-len(arg_partial))


def global_signal_handler(sig, frame):
    print("\nCtrl+C caught globally, performing cleanup...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, global_signal_handler)
    chatbot = Chatbot()
    chatbot.run()

if __name__ == "__main__":
    main()
