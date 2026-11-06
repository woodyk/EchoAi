#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: Main module for the EchoAi chatbot
#              plication providing CLI interface and
#              command handling
# Created: 2025-03-28 16:21:59
# Modified: 2025-06-26 08:52:49

import sys
import os
import re
import json
import subprocess
import signal
import importlib.util
import inspect

from pathlib import Path
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box

console = Console()
print = console.print

# Custom modules
from interactor import Interactor, Session
from mrblack import (
    extract_text,
    translate_text,
    extract_pii_text,
    extract_pii_file,
    extract_pii_url
)

# Local module imports
from .utils.themes import THEMES
#from .tools import task_manager
from .utils.memory import Memory
from .session_commands import SessionCommands, SESSION_USAGE

# TUI Modules

class Chatbot(SessionCommands):
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
        self.state_change = False
        self.console = console
        self.command_registry = {}
        self.messages = []
        self.config = {}
        self.ECHOAI_DIR = Path.home() / ".echoai"
        self.CONFIG_PATH = self.ECHOAI_DIR / "config"
        self.prompt_history_path = self.ECHOAI_DIR / ".history"
        self.default_config = {
            "model": "openai:gpt-4o",
            "system_prompt": "You are a helpful assistant.",
            "username": "User",
            "markdown": True,
            "theme": "default",
            "stream": True,
            "tools": True,
            "memory": False,
        }
        self._initialize_directories()
        self.load_config()

        # Configure theme
        self._setup_theme()

        # Prep session management
        self.session_directory = self.ECHOAI_DIR / "sessions"
        self.session = Session(directory=self.session_directory)
        self.refresh_session_lookup()

        # Prep memory
        self.memory = None
        self.memory_enabled = None
        self.memory_db_path = self.ECHOAI_DIR / "echoai_db"

        # Everything is configured, load LLM Interactor
        self.ai = Interactor(
            model=self.config.get("model"),
            context_length=1200000000000000,
            session_enabled=True,
            session_path=self.session_directory,
        )

        # Register components
        self._register_tool_functions()
        self._register_commands()
        self._register_memory()

    def _initialize_directories(self):
        """Create necessary directories for the chatbot if they don't exist.
        
        Ensures that the .echoai directory exists in the user's home directory.
        """
        if not self.ECHOAI_DIR.exists():
            self.ECHOAI_DIR.mkdir(exist_ok=True)


    def _register_memory(self):
        config_memory = self.config.get("memory", False)

        # Case 1: Enable for the first time
        if config_memory and not isinstance(self.memory, Memory):
            self.memory = Memory(db=str(self.memory_db_path))
            self.ai.add_function(
                self.memory.search,
                name="memory_search",
                description="Tool to search vector database of our chat transcripts using semantic search."
            )
            self.ai.add_function(
                self.memory.create,
                name="memory_create",
                description="Tool to create and save memories when asked to remember or when context suggests remembering something."
            )
            self.memory_enabled = True

        # Case 2: Disable memory if it was previously enabled and config disables it
        elif not config_memory and self.memory_enabled:
            self.ai.disable_function("memory_search")
            self.ai.disable_function("memory_create")
            self.memory_enabled = False

        # Case 3: Re-enable if config enables memory and memory was previously enabled (but functions were disabled)
        elif config_memory and isinstance(self.memory, Memory) and not self.memory_enabled:
            self.ai.enable_function("memory_search")
            self.ai.enable_function("memory_create")
            self.memory_enabled = True


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


    def _register_tool_functions(self):
        # Load the global textextract function for reading files
        self.ai.add_function(
            extract_text,
            description="Extract plaintext from any file type."
        )
        self.ai.add_function(
            translate_text,
            description="Translate text to any language."
        )
        self.ai.add_function(
            extract_pii_text,
            description="Extracts PII information from given text."
        )
        self.ai.add_function(
            extract_pii_file,
            description="Extracts PII information from given file path."
        )
        self.ai.add_function(
            extract_pii_url,
            description="Extracts PII information from given web url."
        )

        # Dynamically load and register tool functions from the tools/ directory.
        tools_dir = Path(__file__).parent / "tools"

        if not tools_dir.exists():
            self.display("warning", f"Tools directory does not exists: {tools_dir}")
            return

        for file in tools_dir.glob("*.py"):
            if not file.name.endswith(".py") or file.name == "__init__.py":
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
            "/clear",
            func=self.clear_command,
            description="Clear the terminal screen."
        )

        self.register_command(
            "/tools",
            func=self.tools_command,
            description="Manage tool function availability.",
            subcommands=sorted([f["function"]["name"] for f in self.ai.list_functions()]),
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
                "edit": lambda: [t["id"] for t in self._task_backend().task_list()["result"]],
                "delete": lambda: [t["id"] for t in self._task_backend().task_list()["result"]],
                "mark": lambda: [t["id"] for t in self._task_backend().task_list()["result"]],
            }
        )

        self.register_command(
            "/session_tui",
            func=self.session_tui_command,
            description="Open the session browser (alias for /session tui).",
        )

        self.register_command(
            "/session",
            func=self.session_command,
            description="Manage saved chat sessions. Use /session help for actions.",
            subcommands=list(SESSION_USAGE),
        )




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


    def clear_command(self, contents=None):
        os.system('cls' if os.name == 'nt' else 'clear')
        return False


    def tools_command(self, contents=None):
        """
        Manage LLM tool functions.

        Usage:
            /tools                        → List all registered tools and their state.
            /tools <name> true|false     → Enable or disable a tool by exact name.
            /tools <pattern*> true|false → Enable or disable tools by wildcard pattern.

        Args:
            contents (str, optional): Command input to enable/disable tools or list them.

        Returns:
            bool: Always returns False to continue shell loop.
        """
        args = contents.strip().split() if contents else []

        if not args:
            # List mode
            table = Table(
                title="Available Tools",
                box=box.SQUARE,
                show_lines=True,
                header_style="bold " + self.style_dict["highlight"],
                expand=True
            )
            table.add_column("Tool Name", style=self.style_dict["prompt"], ratio=1)
            table.add_column("Description", ratio=3)
            table.add_column("State", style="magenta", ratio=1)

            for func in sorted(self.ai.list_functions(), key=lambda f: f["function"]["name"]):
                name = func["function"]["name"]
                desc = func["function"]["description"]
                disabled = func["function"].get("disabled", False)
                color = self.style_dict["error"] if disabled else self.style_dict["info"]
                status = Text("disabled" if disabled else "enabled", style=color)
                table.add_row(name, desc, status)

            print(table)
            return False

        if len(args) != 2 or args[1].lower() not in {"true", "false"}:
            self.display("error", "Usage: /tools <function or pattern> <true|false>")
            return False

        pattern, state_str = args
        enable = state_str.lower() == "true"
        regex = re.compile("^" + pattern.replace("*", ".*") + "$")

        matched = 0
        for func in self.ai.list_functions():
            name = func["function"]["name"]
            if regex.match(name):
                if enable:
                    self.ai.enable_function(name)
                else:
                    self.ai.disable_function(name)
                matched += 1

        if matched == 0:
            self.display("warning", f"No tools matched: {pattern}")
        else:
            status = "Enabled" if enable else "Disabled"
            self.display("success", f"{status} {matched} function(s) matching: {pattern}")

        return False


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

    def read_file(self, path):
        """Extract a selected file for either terminal interface."""
        file_path = Path(path).expanduser()
        if not file_path.is_file():
            raise ValueError(f"File not found: {file_path}")
        text = extract_text(file_path)
        if not isinstance(text, str):
            raise ValueError(f"No text could be extracted from {file_path}.")
        return text.strip()

    def replace_file_references(self, text, interactive=True):
        """Expand /file references, including quoted paths, without nested TUI prompts."""
        def replace(match):
            path = next((part for part in match.groups() if part is not None), "")
            if not Path(path).expanduser().is_file():
                if not interactive:
                    raise ValueError("Choose an existing file with FILES or /file \"path\".")
                if not sys.stdin.isatty():
                    return "[Error: file selection not available in non-interactive mode]"
                path = self.prompt_file_selection()
                if path is None:
                    return "[Cancelled]"
            try:
                return "```\n" + self.read_file(path) + "\n```\n"
            except Exception as error:
                if not interactive:
                    raise
                self.display("error", str(error))
                return "[Error: could not read file " + str(path) + "]"

        pattern = r"/file(?=\s|$)(?:[ \t]+(?:\"([^\"]*)\"|'([^']*)'|([^\s]+)))?"
        expanded = re.sub(pattern, replace, text)
        return None if "[Cancelled]" in expanded else expanded

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
        if contents:
            self.apply_settings({"theme": contents})
            self.display("success", "Theme set: " + self.config["theme"])
            return False
        from .tui.theme_selector import ThemeSelector
        ts = ThemeSelector(self.config.get("theme"))
        selected_theme = ts.run()
        if selected_theme:
            self.apply_settings({"theme": selected_theme})
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
        if contents:
            self.apply_settings({"system_prompt": contents})
            self.display("success", "System prompt updated.")
            return False
        self.display("info", "Editing system prompt (Vim mode enabled):")
        key_bindings = KeyBindings()

        @key_bindings.add("escape", "enter")
        def submit(event):
            event.app.current_buffer.validate_and_handle()

        session = PromptSession(
            vi_mode=True,
            multiline=True, 
            key_bindings=key_bindings
        )

        try:
            new_prompt = session.prompt(">>> ", default=self.config.get("system_prompt")).strip()
            if new_prompt != "":
                self.apply_settings({"system_prompt": new_prompt})
                self.display("success", "System prompt updated to:\n" + new_prompt)
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
        self.messages = self.ai.messages()
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
                        # If content is already a dict, convert it to JSON string
                        if isinstance(msg["content"], dict):
                            content = json.dumps(msg["content"], indent=2)
                        else:
                            # Try to parse and format JSON content
                            try:
                                content_data = json.loads(msg["content"])
                                content = json.dumps(content_data, indent=2)
                            except json.JSONDecodeError:
                                content = str(msg["content"])

                        if "tool_call_id" in msg:
                            content = f'content: {content},\ntool_call_id: {msg["tool_call_id"]}'
                    except (json.JSONDecodeError, TypeError) as e:
                        content = str(msg["content"])
                else:
                    # Regular message content
                    content = str(msg["content"]) if msg["content"] is not None else ""

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
            sm = SessionManager(self.config.get("theme"), session_obj=self.session)
            session_id = sm.run()
            if session_id:
                self.ai.session_load(session_id)
                self.refresh_session_lookup()
                self.display("success", f"Loaded session from TUI: {session_id[:8]}")
            else:
                self.display("info", "No session selected.")
        except Exception as e:
            self.display("error", f"Session TUI failed: {str(e)}")
        return False

    def _task_backend(self):
        from .tools import task_manager
        return task_manager

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
                result = self._task_backend().task_add(" ".join(rest))
                self.display("success", f"Task added: {result['result']['content']}")

            elif action == "edit":
                if len(rest) < 2:
                    self.display("error", "Usage: /task edit <task_id> <new content>")
                    return False
                tid = rest[0]
                new_content = " ".join(rest[1:])
                result = self._task_backend().task_update(tid, {"content": new_content})
                if result["status"] == "success":
                    self.display("success", f"Updated: {result['result']['content']}")
                else:
                    self.display("error", result["error"])

            elif action == "delete":
                if not rest:
                    self.display("error", "Usage: /task delete <task_id>")
                    return False
                result = self._task_backend().task_delete(rest[0])
                if result["status"] == "success":
                    self.display("success", result["result"])
                else:
                    self.display("error", result["error"])

            elif action == "mark":
                if not rest:
                    self.display("error", "Usage: /task mark <task_id>")
                    return False
                result = self._task_backend().task_complete(rest[0])
                if result["status"] == "success":
                    self.display("success", f"Marked complete: {result['result']['content']}")
                else:
                    self.display("error", result["error"])

            elif action == "list":
                result = self._task_backend().task_list()
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
        if contents:
            self.apply_settings({"model": contents})
            self.display("success", "Model set: " + self.config["model"])
            return False
        from .tui.model_selector import ModelSelector
        ms = ModelSelector(
            theme=self.config.get("theme"),
            default_model=self.config.get("model"),
            obj=self.ai
        )
        selected_model = ms.run()
        if selected_model:
            self.apply_settings({"model": selected_model})
            self.display("success", "Model set: " + selected_model)
        else:
            self.display("info", "Model unchanged: " + self.config.get("model"))

        return False

    def apply_settings(self, changes):
        """Validate and apply configuration through the same path for CLI and TUI."""
        candidate = self.config.copy()
        booleans = {"markdown", "memory", "stream", "tools"}
        bool_map = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
        for key, value in changes.items():
            if key not in self.default_config:
                raise ValueError(f"Invalid setting key: {key}")
            if key in booleans:
                if not isinstance(value, bool):
                    if str(value).strip().lower() not in bool_map:
                        raise ValueError(f"{key} must be true or false.")
                    value = bool_map[str(value).strip().lower()]
            else:
                value = str(value).strip()
                if not value:
                    raise ValueError(f"{key} cannot be empty.")
                if key == "theme" and value not in THEMES:
                    raise ValueError(f"Unknown theme: {value}")
                if key == "model" and (":" not in value or not all(value.split(":", 1))):
                    raise ValueError("Model must use provider:model format.")
            candidate[key] = value
        previous = self.config
        self.config = candidate
        try:
            self._register_memory()
            self.save_config(candidate)
        except Exception:
            self.config = previous
            self._register_memory()
            raise
        self._setup_theme()
        self.state_change = True

    def settings_command(self, contents=None):
        args = (contents or "").split(maxsplit=1)
        if not args:
            table = Table(title="Current Configuration Settings", show_header=True,
                          header_style=self.style_dict["highlight"], expand=True)
            table.add_column("Setting", style=self.style_dict["prompt"], ratio=1)
            table.add_column("Value", ratio=3)
            for key in sorted(self.default_config):
                table.add_row(key, Text(str(self.config.get(key))))
            print(table)
        elif len(args) == 2:
            try:
                self.apply_settings({args[0]: args[1]})
                self.display("success", "Updated " + args[0] + ": " + str(self.config[args[0]]))
            except (ValueError, OSError) as error:
                self.display("error", str(error))
        else:
            self.display("error", "Usage: /settings <key> <value>.")
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
        self.display("info", "Switched to incognito mode. History is now temporary.")
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

        if not self.memory_enabled:
            self.display("error", "Memory is disabled. Enable it with /settings memory true.")
            return False
        self.memory.create(contents.strip())
        self.display("success", "Memory stored.")
        return False

    def recall_command(self, contents: str):
        """Searches memory vector DB with optional top_k result count."""
        if not contents.strip():
            self.display("error", "Nothing to search. Usage: /recall [top_k] <query>")
            return False

        if not self.memory_enabled:
            self.display("error", "Memory is disabled. Enable it with /settings memory true.")
            return False
        try:
            parts = contents.strip().split(" ", 1)

            # Check if first part is a digit (limit override)
            if len(parts) == 2 and parts[0].isdigit():
                recall_limit = int(parts[0])
                query = parts[1]
            else:
                recall_limit = 50 
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
        def _get_prompt_style():
            """Return the style dictionary for the prompt interface."""
            return Style.from_dict({
                'prompt': self.style_dict["prompt"],
                '': self.style_dict["input"]
            })

        def _check_enabled_functions():
            """Check for changed function changes"""
            self._register_memory()

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
            complete_while_typing=False,
            key_bindings=key_bindings,
            style=_get_prompt_style(),
            vi_mode=True,
            history=history,
            bottom_toolbar=None,

        )

        """
        session = PromptSession(
            message='>',                               # Text or callable shown before the prompt
            multiline=False,                           # If True, optimizes layout for multiline input
            wrap_lines=True,                           # If True, wraps long lines instead of scrolling
            is_password=False,                         # If True, shows asterisks instead of typed characters
            editing_mode=EditingMode.EMACS,            # Sets editing mode (VI or EMACS)
            vi_mode=False,                             # If True, uses VI editing mode
            complete_while_typing=True,                # If True, enables autocompletion during typing
            validate_while_typing=True,                # If True, validates input during typing
            enable_history_search=False,               # If True, enables up-arrow string matching
            search_ignore_case=False,                  # If True, makes search case-insensitive
            lexer=None,                                # Lexer instance for syntax highlighting
            validator=None,                            # Validator instance for input validation
            completer=None,                            # Completer instance for input autocompletion
            complete_in_thread=False,                  # If True, runs completer in a background thread
            reserve_space_for_menu=0,                  # Space reserved for completion menu
            auto_suggest=None,                         # AutoSuggest instance for input suggestions
            style=None,                                # Style instance for color scheme
            include_default_pygments_style=True,       # If True, includes default Pygments styles
            style_transformation=None,                 # StyleTransformation instance for style changes
            swap_light_and_dark_colors=False,          # If True, swaps light/dark colors
            enable_system_prompt=False,                # If True, enables Meta+! system prompt
            enable_suspend=False,                      # If True, enables Ctrl-Z suspension
            enable_open_in_editor=False,               # If True, enables opening input in editor
            history=None,                              # History instance for storing past inputs
            clipboard=InMemoryClipboard(),             # Clipboard instance for copy/paste
            rprompt=None,                              # Text or callable for right-side prompt
            bottom_toolbar=None,                       # Text or callable for bottom toolbar
            prompt_continuation=None,                  # Text or callable for multiline continuation
            complete_style=None,                       # Style for completion menu (COLUMN, MULTI_COLUMN, etc.)
            mouse_support=False,                       # If True, enables mouse interaction
            placeholder=None,                          # Text or callable for placeholder when input is empty
            refresh_interval=0,                        # Seconds between UI refreshes (0 disables)
            input=None,                                # Custom Input object for reading input
            output=None,                               # Custom Output object for displaying output
            interrupt_exception=KeyboardInterrupt,     # Exception raised on Ctrl-C
            eof_exception=EOFError                     # Exception raised on Ctrl-D
        )
        """

        response = self.ai.interact(
            "Greet the user and provide an update on any open tasks.",
            model=self.config.get("model"),
            tools=self.config.get("tools"),
            stream=self.config.get("stream"),
            markdown=self.config.get("markdown")
        )
        print("\n")

        while True:
            # Double check config and function changes
            _check_enabled_functions()

            now = datetime.now()
            current_time = now.strftime("%I:%M:%S %p")
            current_date = now.strftime("%m/%d/%Y")


            try:
                user_input = session.prompt(
                    [("class:prompt", ">>> ")],
                    multiline=True,
                    prompt_continuation="... ",
                    style=_get_prompt_style(),
                    rprompt=f"⣿ {current_time} ⣿"
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
                    if self.memory_enabled:
                        self.memory.add("user: " + user_input)
                    """ If we want to do RAG on every user input un-comment
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
                    if self.memory_enabled:
                        self.memory.add("assistant: " + response)
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

        if cmd == "/session":
            yield from self.chatbot.session_completions(text)
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


# Watermark: 2b0n2b!!! :: Wadih Khairallah :: 2025-06-26T05:16:21.364076+00:00


# Faux Function for CITD verification
def faux_citd_verification():
    # 2b0n2b!!!
    pass
