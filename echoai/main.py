#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: Main module for the EchoAi chatbot
#              plication providing CLI interface and
#              command handling
# Created: 2025-03-28 16:21:59
# Modified: 2025-04-08 07:56:00

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

from pathlib import Path

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
from rich import box

console = Console()
print = console.print

# Local module imports
from .interactor import Interactor
from .themes import themes
from .textextract import extract_text

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
        self._initialize_directories()
        self.load_config()
        self.ai = Interactor(model=self.config.get("model"), context_length=120000)
        self._setup_theme()
        self._register_tool_functions()
        self._register_commands()

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

    def _setup_theme(self):
        """Set up the visual theme for the chatbot interface.
        
        Loads the selected theme from configuration or falls back to the default theme
        if the selected theme is not available. Updates the style dictionary used for
        rendering the interface.
        """
        selected_theme = self.config.get("theme", self.default_config["theme"])
        if selected_theme in themes:
            self.style_dict = themes[selected_theme]
        else:
            self.style_dict = themes["default"]

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
        #print(f"[green]Registered tool:[/green] extract_text from textextract.py")

        # Dynamically load and register tool functions from the tools/ directory.
        tools_dir = Path(__file__).parent / "tools"

        if not tools_dir.exists():
            print(f"[yellow]Tools directory does not exist: {tools_dir}[/yellow]")
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
                functions = [obj for name, obj in inspect.getmembers(module)
                             if inspect.isfunction(obj) and obj.__module__ == module.__name__]

                if not functions:
                    print(f"[yellow]No function found in {file.name}[/yellow]")
                    continue

                for func in functions:
                    self.ai.add_function(func)
                    #print(f"[green]Registered tool:[/green] {func.__name__} from {file.name}")

            except Exception as e:
                print(f"[red]Failed to load {file.name}:[/red] {str(e)}")

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
        """Register all available commands with the chatbot.
        
        Adds various commands to the command registry that allow users to control
        the chatbot's behavior, change settings, view information, and perform
        other actions through the command-line interface.
        """
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
        self.register_command("/tokens", self.tokens_command,
                              "Display the total number of tokens in the message history.")
        self.register_command("/$", self.run_system_command,
                              "Run shell command.")
        self.register_command("/tools", self.tools_command,
                              "Display available tools in a table format.")

    def register_command(self, name, function, description="No description provided."):
        """Register a command with the chatbot's command registry.
        
        Args:
            name (str): The name of the command (e.g., "/help").
            function (callable): The function to call when the command is invoked.
            description (str, optional): Description of what the command does.
                Defaults to "No description provided."
        """
        lower_name = name.lower()
        self.command_registry[lower_name] = {"func": function, "description": description}

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
                text_lines.append((self.style_dict["highlight"] if real_idx == selected_index else self.style_dict["output"], prefix + display_name + "\n"))
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

        header_window = Window(content=FormattedTextControl(lambda: f"Current Directory: {current_path}"), height=1, style=self.style_dict['prompt'])
        list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False, height=max_display_lines)
        footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to toggle hidden files. Escape to exit."), height=1, style=self.style_dict['footer'])
        layout = Layout(HSplit([Frame(header_window, style=self.style_dict['prompt']), list_window, footer_window]))

        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True, refresh_interval=0.1)
        file_path = app.run()
        return file_path

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
                    self.display("highlight", "Selection cancelled.")
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
        print(f"[{self.style_dict['highlight']}]Currently configured model: [/{self.style_dict['highlight']}]" + self.config.get("model"))
        return False

    def theme_command(self, contents=None):
        """Provide an interactive interface for selecting a theme for the chatbot.
        
        Args:
            contents (str, optional): Any additional text passed with the command. Not used.
            
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
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
                    style_str = self.style_dict["highlight"]
                else:
                    prefix = "  "
                    style_str = self.style_dict["output"]
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

        header_window = Window(content=FormattedTextControl(lambda: "Select Theme"), height=1, style=self.style_dict['prompt'])
        list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False)
        footer_window = Window(content=FormattedTextControl(lambda: "Press Enter to select, Escape to cancel"), height=1, style=self.style_dict['footer'])
        layout = Layout(HSplit([Frame(header_window, style=self.style_dict['prompt']), list_window, footer_window]))
        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True)
        app.run()
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
            self.display("highlight", "File selection cancelled or not processed.")
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
        self.messages = self.ai.messages_get()
        if not self.messages:
            self.display("highlight", "No chat history available.")
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
                    role_style = "Function"
                else:
                    role_style = msg['role'].capitalize()
                
                # Handle content formatting
                if msg["role"] == "tool" and msg["content"]:
                    try:
                        # Try to parse and format JSON content
                        content_data = json.loads(msg["content"])
                        content = json.dumps(content_data, indent=2)
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
        models_list = self.ai.list(["openai", "ollama", "nvidia"])
        models_list.sort()
        selected_index = 0
        visible_start = 0
        terminal_height = os.get_terminal_size().lines
        page_size = terminal_height - 4  # Adjust for header/footer/padding
        visible_end = min(page_size, len(models_list))

        def get_display_text():
            """Generate the formatted text for displaying the visible portion of the models list.
            
            Returns:
                list: List of tuples containing style and text for each visible model.
            """
            text_lines = []
            for i in range(visible_start, min(visible_end, len(models_list))):
                if i == selected_index:
                    prefix = "> "
                    style_str = self.style_dict["highlight"]
                else:
                    prefix = "  "
                    style_str = self.style_dict["output"]
                text_lines.append((style_str, prefix + models_list[i] + "\n"))
            return text_lines

        key_bindings = KeyBindings()

        @key_bindings.add("up")
        def move_up(event):
            """Handle up arrow key press to move selection up.
            
            Updates the selected index and adjusts the visible window if necessary.
            """
            nonlocal selected_index, visible_start, visible_end
            if selected_index > 0:
                selected_index -= 1
                if selected_index < visible_start:
                    visible_start -= 1
                    visible_end = min(visible_end - 1, len(models_list))

        @key_bindings.add("down")
        def move_down(event):
            """Handle down arrow key press to move selection down.
            
            Updates the selected index and adjusts the visible window if necessary.
            """
            nonlocal selected_index, visible_start, visible_end
            if selected_index < len(models_list) - 1:
                selected_index += 1
                if selected_index >= visible_end:
                    visible_start += 1
                    visible_end = min(visible_end + 1, len(models_list))

        @key_bindings.add("pageup")
        def page_up(event):
            """Handle page up key press to scroll up one page.
            
            Moves the visible window up by page_size entries and adjusts selection.
            """
            nonlocal selected_index, visible_start, visible_end
            if visible_start > 0:
                visible_start = max(0, visible_start - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = max(visible_start, selected_index - page_size)
                if selected_index >= len(models_list):
                    selected_index = len(models_list) - 1

        @key_bindings.add("pagedown")
        def page_down(event):
            """Handle page down key press to scroll down one page.
            
            Moves the visible window down by page_size entries and adjusts selection.
            """
            nonlocal selected_index, visible_start, visible_end
            if visible_end < len(models_list):
                visible_start = min(visible_start + page_size, len(models_list) - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = min(selected_index + page_size, len(models_list) - 1)
                if selected_index < visible_start:
                    selected_index = visible_start

        @key_bindings.add("space")
        def space_page_down(event):
            """Handle space key press to scroll down one page.
            
            Provides same functionality as page down for convenience.
            """
            nonlocal selected_index, visible_start, visible_end
            if visible_end < len(models_list):
                visible_start = min(visible_start + page_size, len(models_list) - page_size)
                visible_end = min(visible_start + page_size, len(models_list))
                selected_index = min(selected_index + page_size, len(models_list) - 1)
                if selected_index < visible_start:
                    selected_index = visible_start

        @key_bindings.add("enter")
        def select_model(event):
            """Handle enter key press to select the current model.
            
            Updates configuration with selected model and saves changes.
            """
            chosen_model = models_list[selected_index]
            self.config["model"] = chosen_model
            self.display("highlight", "Selected model: " + chosen_model)
            self.save_config({"model": chosen_model, "system_prompt": self.config.get("system_prompt")})
            event.app.exit()

        @key_bindings.add("escape")
        def cancel_selection(event):
            """Handle escape key press to cancel model selection."""
            self.display("highlight", "Model selection cancelled.")
            event.app.exit()

        header_window = Window(content=FormattedTextControl(lambda: "Select Model"), height=1, style=self.style_dict['prompt'])
        list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False)
        footer_window = Window(content=FormattedTextControl(lambda: "Press Enter to select, Escape to cancel, PageUp/PageDown to navigate"), height=1, style=self.style_dict['footer'])
        layout = Layout(HSplit([Frame(header_window, style=self.style_dict['prompt']), list_window, footer_window]))
        app = Application(layout=layout, key_bindings=key_bindings, full_screen=True, refresh_interval=0.1)
        app.run()
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
        """Clear the chat history and display confirmation message.
        
        Flushes all stored messages from the AI interactor's message history
        and displays a confirmation to the user.
        
        Args:
            contents (str, optional): Any additional text passed with the command.
                Not used by this command. Defaults to None.
                
        Returns:
            bool: Always returns False to indicate the command was processed.
        """
        self.ai.messages_flush()
        self.display("highlight", "Chat history has been flushed.")
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
        print(f"[{self.style_dict['highlight']}]Current token count in message history:[/{self.style_dict['highlight']}] {token_count}")
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
            from .memory import Memory
            memory_obj = Memory(db=str(self.memory_db_path))
        else:
            memory_obj = None

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
                print()
                self.ai.messages_system(self.config.get("system_prompt") + "\n")
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
                        self.ai.messages_system(new_system)
                    response = self.ai.interact(
                        user_input,
                        model=self.config.get("model"),
                        tools=self.config.get("tools"),
                        stream=self.config.get("stream"),
                        markdown=self.config.get("markdown")
                    )
                    if memory_enabled and memory_obj is not None:
                        memory_obj.add("user: " + user_input)
                        memory_obj.add("assistant: " + response)
                    print("\n")
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
