#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-08 15:53:15
# Modified: 2025-03-16 17:19:46

import sys
import os
import re
import shlex
import json
import subprocess
import io
import contextlib
import traceback
import base64
import pandas as pd
import matplotlib.pyplot as plt
import platform
import signal
import datetime
import getpass
import requests
import pytz
from io import BytesIO
from prompt_toolkit import PromptSession
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.shortcuts import CompleteStyle, prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.widgets import Frame
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.prompt import Confirm
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from openai import OpenAI
from ollama import Client
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from bs4 import BeautifulSoup
import magic
import PyPDF2
import docx

from .interactor import Interactor
from typing import Dict, Any, Optional, Union

def signal_handler(sig, frame):
    print("\nCtrl+C caught globally, performing cleanup...")
    # Perform any cleanup tasks here
    sys.exit(0)

# Register the global handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Path to the config file
config_path = Path.home() / ".echoai"

# Default configuration
default_config = {
    "model": "openai:gpt-4o",
    "system_prompt": "You are a helpful assistant.",
    "show_hidden_files": False,
    "username": "User",
    "markdown": True,
    "theme": "default"
}

themes = {
    "default": {
        "prompt": "#02788E",
        "highlight": "#FFD700",
        "error": "bold #8B0000",
        "output": "#002DED",
        "footer": "#6e757c",
        "input": "#DED300"
    },
    "ocean": {
        "prompt": "bold #00CED1",        # Dark Turquoise
        "highlight": "#4682B4",          # Steel Blue
        "error": "bold #FF4500",         # Orange Red
        "output": "#20B2AA",             # Light Sea Green
        "footer": "#5F9EA0",             # Cadet Blue
        "input": "#00CED1"         # Dark Turquoise
    },
    "forest": {
        "prompt": "bold #2E8B57",        # Sea Green
        "highlight": "#9ACD32",          # Yellow Green
        "error": "bold #FF6347",         # Tomato
        "output": "#556B2F",             # Dark Olive Green
        "footer": "#66CDAA",             # Medium Aquamarine
        "input": "#2E8B57"         # Sea Green
    },
    "sunset": {
        "prompt": "bold #FFA07A",        # Light Salmon
        "highlight": "#FF69B4",          # Hot Pink
        "error": "bold #FF4500",         # Orange Red
        "output": "#FFD700",             # Gold
        "footer": "#FF6347",             # Tomato
        "input": "#FFA07A"         # Light Salmon
    },
    "night": {
        "prompt": "bold #B0C4DE",        # Light Steel Blue
        "highlight": "#4682B4",          # Steel Blue
        "error": "bold #FF4500",         # Orange Red
        "output": "#708090",             # Slate Gray
        "footer": "#2F4F4F",             # Dark Slate Gray
        "input": "#B0C4DE"         # Light Steel Blue
    },
    "pastel": {
        "prompt": "bold #FFB6C1",        # Light Pink
        "highlight": "#AFEEEE",          # Pale Turquoise
        "error": "bold #FA8072",         # Salmon
        "output": "#FFFACD",             # Lemon Chiffon
        "footer": "#D8BFD8",             # Thistle
        "input": "#FFB6C1"         # Light Pink
    },
    "solar": {
        "prompt": "bold #FFD700",        # Gold
        "highlight": "#FF8C00",          # Dark Orange
        "error": "bold #FF4500",         # Orange Red
        "output": "#FFDEAD",             # Navajo White
        "footer": "#FFDAB9",             # Peach Puff
        "input": "#FFD700"         # Gold
    },
    "lava": {
        "prompt": "bold #FF6347",        # Tomato
        "highlight": "#FF4500",          # Orange Red
        "error": "bold #8B0000",         # Dark Red
        "output": "#FFA07A",             # Light Salmon
        "footer": "#CD5C5C",             # Indian Red
        "input": "#FF6347"         # Tomato
    },
    "mint": {
        "prompt": "bold #98FB98",        # Pale Green
        "highlight": "#66CDAA",          # Medium Aquamarine
        "error": "bold #8B0000",         # Dark Red
        "output": "#E0FFFF",             # Light Cyan
        "footer": "#AFEEEE",             # Pale Turquoise
        "input": "#98FB98"         # Pale Green
    },
    "earth": {
        "prompt": "bold #8B4513",        # Saddle Brown
        "highlight": "#D2B48C",          # Tan
        "error": "bold #A52A2A",         # Brown
        "output": "#DEB887",             # Burly Wood
        "footer": "#8B4513",             # Saddle Brown
        "input": "#8B4513"         # Saddle Brown
    },
    "floral": {
        "prompt": "bold #FF69B4",        # Hot Pink
        "highlight": "#DB7093",          # Pale Violet Red
        "error": "bold #8B0000",         # Dark Red
        "output": "#FFF0F5",             # Lavender Blush
        "footer": "#FFB6C1",             # Light Pink
        "input": "#FF69B4"         # Hot Pink
    },
    "royal": {
        "prompt": "bold #4169E1",        # Royal Blue
        "highlight": "#4682B4",          # Steel Blue
        "error": "bold #8B0000",         # Dark Red
        "output": "#87CEEB",             # Sky Blue
        "footer": "#B0C4DE",             # Light Steel Blue
        "input": "#4169E1"         # Royal Blue
    },
    "orchid": {
        "prompt": "bold #DA70D6",        # Orchid
        "highlight": "#BA55D3",          # Medium Orchid
        "error": "bold #9932CC",         # Dark Orchid
        "output": "#E6E6FA",             # Lavender
        "footer": "#DDA0DD",             # Plum
        "input": "#DA70D6"         # Orchid
    },
    "berry": {
        "prompt": "bold #C71585",        # Medium Violet Red
        "highlight": "#D87093",          # Pale Violet Red
        "error": "bold #8B0000",         # Dark Red
        "output": "#FFE4E1",             # Misty Rose
        "footer": "#D8BFD8",             # Thistle
        "input": "#C71585"         # Medium Violet Red
    },
    "tide": {
        "prompt": "bold #00BFFF",        # Deep Sky Blue
        "highlight": "#1E90FF",          # Dodger Blue
        "error": "bold #8B0000",         # Dark Red
        "output": "#E0FFFF",             # Light Cyan
        "footer": "#AFEEEE",             # Pale Turquoise
        "input": "#00BFFF"         # Deep Sky Blue
    },
    "lemonade": {
        "prompt": "bold #FFFACD",        # Lemon Chiffon
        "highlight": "#FFD700",          # Gold
        "error": "bold #FF4500",         # Orange Red
        "output": "#FFF8DC",             # Cornsilk
        "footer": "#FAFAD2",             # Light Goldenrod Yellow
        "input": "#FFFACD"         # Lemon Chiffon
    },
    "slate": {
        "prompt": "bold #708090",        # Slate Gray
        "highlight": "#778899",          # Light Slate Gray
        "error": "bold #8B0000",         # Dark Red
        "output": "#B0C4DE",             # Light Steel Blue
        "footer": "#2F4F4F",             # Dark Slate Gray
        "input": "#708090"         # Slate Gray
    },
    "grape": {
        "prompt": "bold #9370DB",        # Medium Purple
        "highlight": "#8A2BE2",          # Blue Violet
        "error": "bold #8B0000",         # Dark Red
        "output": "#DDA0DD",             # Plum
        "footer": "#9400D3",             # Dark Violet
        "input": "#9370DB"         # Medium Purple
    },
    "bubblegum": {
        "prompt": "bold #FF69B4",        # Hot Pink
        "highlight": "#FF1493",          # Deep Pink
        "error": "bold #8B0000",         # Dark Red
        "output": "#FFC0CB",             # Pink
        "footer": "#FFB6C1",             # Light Pink
        "input": "#FF69B4"         # Hot Pink
    },
    "sky": {
        "prompt": "bold #87CEFA",        # Light Sky Blue
        "highlight": "#4682B4",          # Steel Blue
        "error": "bold #8B0000",         # Dark Red
        "output": "#ADD8E6",             # Light Blue
        "footer": "#87CEEB",             # Sky Blue
        "input": "#87CEFA"         # Light Sky Blue
    },
}

# Function for displaying text.
def display(inform, text):
    if "|set|" in text:
        # Split the string on "|set|"
        left, right = text.split("|set|", 1)
        left = left.strip()
        right = right.strip()

        console.print(f"[{style_dict[inform]}]{left}[/{style_dict[inform]}] {right}")
    else:
        console.print(f"[{style_dict[inform]}]{text}[/{style_dict[inform]}]")

    return False
    
# Load or initialize the configuration file
def load_config():
    global model, username, system_prompt, markdown, show_hidden_files, theme_name, style_dict
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        model = config.get("model", default_config["model"])
        system_prompt = config.get("system_prompt", default_config["system_prompt"])
        show_hidden_files = bool(config.get("show_hidden_files", default_config["show_hidden_files"]))
        theme_name = config.get("theme", default_config["theme"])
        username = config.get("username", default_config["username"])

        # Ensure markdown is always a boolean
        markdown_value = config.get("markdown", default_config["markdown"])
        markdown = isinstance(markdown_value, bool) and markdown_value  # Force boolean type
    else:
        save_config(default_config)  # Save default if file doesn't exist
        model = default_config["model"]
        system_prompt = default_config["system_prompt"]
        show_hidden_files = default_config["show_hidden_files"]
        theme_name = default_config["theme"]
        username = default_config["username"]
        markdown = default_config["markdown"]

    # Load the selected theme style
    style_dict = themes[theme_name]

# Save configuration to the file
def save_config(new_config):
    existing_config = default_config.copy()
    if config_path.exists():
        with open(config_path, "r") as f:
            existing_config.update(json.load(f))
    existing_config.update(new_config)

    with open(config_path, "w") as f:
        json.dump(existing_config, f, indent=4)


# Initialize configuration on load
load_config()

# Define or update the style based on the selected theme, including user input color
style = Style.from_dict({
    'prompt': style_dict["prompt"],          # Style for the "User: " prompt label
    '': style_dict["input"]     # Style for the user input text
})

# Initialize the OpenAI Client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize the Ollama Client
oclient = Client(host="http://127.0.0.1:11434")

# Initialize Rich Console
console = Console()

# Prepare the command registry
command_registry = {}

messages = []

# Command decorator to register commands easily with descriptions
def command(name, description="No description provided."):
    def decorator(func):
        command_registry[name.lower()] = {"func": func, "description": description}
        return func
    return decorator

def extract_text_from_file(file_path):
    """Extract text from supported file types using magic to determine the file type."""
    file_path = Path(file_path)

    # Determine MIME type using magic
    mime_type = magic.from_file(str(file_path), mime=True)

    if mime_type == "application/pdf":
        text = ""
        with file_path.open("rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif mime_type.startswith("text"):
        return file_path.read_text()

    else:
        display("error", f"Unsupported file type '{mime_type}'")

def prompt_file_selection():
    """Terminal-based file browser using prompt_toolkit to navigate and select files."""
    current_path = Path.cwd()  # Start in the user's home directory
    files = []
    selected_index = 0  # Track the selected file/folder index
    scroll_offset = 0  # Track the starting point of the visible list
    show_hidden = False  # Initialize hidden files visibility

    terminal_height = int(os.get_terminal_size().lines) #int(os.get_terminal_size().lines / 2)
    max_display_lines = terminal_height - 4  # Reduce by 2 for header and footer lines

    def update_file_list():
        """Update the list of files in the current directory, with '..' as the first entry to go up."""
        nonlocal files, selected_index, scroll_offset
        # List current directory contents and insert '..' at the top for navigating up
        all_files = [".."] + sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        # Filter out hidden files if `show_hidden` is False
        files = [f for f in all_files if isinstance(f, str) or show_hidden or not f.name.startswith('.')]

        selected_index = 0
        scroll_offset = 0

    def get_display_text():
        """Display text for the current directory contents with the selected item highlighted."""
        text = []
        visible_files = files[scroll_offset:scroll_offset + max_display_lines]
        for i, f in enumerate(visible_files):
            real_index = scroll_offset + i
            prefix = "> " if real_index == selected_index else "  "
            
            # Use only the file or directory name for display
            display_name = f if isinstance(f, str) else f.name
            display_name += "/" if isinstance(f, Path) and f.is_dir() else ""
            
            line = f"{prefix}{display_name}"
            text.append((f"{'yellow' if real_index == selected_index else 'white'}", line))
            text.append(('', '\n'))
        return text

    # Initialize file list with the home directory contents
    update_file_list()

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    def move_up(event):
        nonlocal selected_index, scroll_offset
        selected_index = (selected_index - 1) % len(files)
        # Scroll up if the selection goes above the visible area
        if selected_index < scroll_offset:
            scroll_offset = max(0, scroll_offset - 1)

    @kb.add("down")
    def move_down(event):
        nonlocal selected_index, scroll_offset
        selected_index = (selected_index + 1) % len(files)
        # Scroll down if the selection goes beyond the visible area
        if selected_index >= scroll_offset + max_display_lines:
            scroll_offset = min(len(files) - max_display_lines, scroll_offset + 1)

    @kb.add("enter")
    def enter_directory(event):
        nonlocal current_path
        selected_file = files[selected_index]

        if selected_file == "..":
            # Move up to the parent directory
            current_path = current_path.parent
            update_file_list()
        elif isinstance(selected_file, Path) and selected_file.is_dir():
            # Enter the selected directory
            current_path = selected_file
            update_file_list()
        elif isinstance(selected_file, Path) and selected_file.is_file():
            # Select the file and exit
            event.app.exit(result=str(selected_file))  # Return the file path as a string

    @kb.add("escape")
    def cancel_selection(event):
        event.app.exit(result=None)  # Exit with None if canceled

    @kb.add("c-h")
    def toggle_hidden(event):
        """Toggle the visibility of hidden files."""
        nonlocal show_hidden
        show_hidden = not show_hidden
        update_file_list()

    # Layout with footer for shortcut hint
    file_list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False, height=max_display_lines)
    footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to show/hide hidden files. Escape to exit."), height=1, style=style_dict['footer'])
    layout = Layout(HSplit([
        Frame(Window(FormattedTextControl(lambda: f"Current Directory: {current_path}"), height=1)),
        file_list_window,
        footer_window  # Footer with shortcut instructions
    ]))

    # Application
    app = Application(layout=layout, key_bindings=kb, full_screen=True, refresh_interval=0.1)

    # Run the application and return the selected file path (or None if canceled)
    return app.run()

def replace_file_references(text):
    """Replace /file <path> with the contents of the specified file in the text."""
    import re

    def file_replacement(match):
        file_path = match.group(1).strip() if match.group(1) else ""
        
        # Expand the tilde if present
        file_path = os.path.expanduser(file_path)

        if os.path.isfile(file_path):
            file_path = Path(file_path).expanduser()
        else:
            # Prompt user to select a file if no path is provided or if the file doesn’t exist
            file_path = prompt_file_selection()
            if file_path is None:  # If selection was cancelled, return None
                return None

        try:
            file_text = extract_text_from_file(file_path)
            return f"```{file_text.strip()}```"
        except Exception as e:
            display("error", f"Error reading file {file_path}:|set|{e}")
            return f"[Error: could not read file {file_path}]"

    # Replace /file with content, return None if any replacement is cancelled
    result = re.sub(r"/file\s*([^\s]+)?", lambda match: file_replacement(match) or "[Cancelled]", text)
    if "[Cancelled]" in result:
        return None
    return result

@command("/show_model", description="Show the currently configured AI model.")
def show_model_command(contents=None):
    """Display the currently configured model."""
    display("highlight", f"Currently configured model:|set|{model}")
    return False  # Continue execution

@command("/theme", description="Select the theme to use for the application.")
def theme_command(contents=None):
    """Handles the selection and configuration of themes to use."""
    global theme_name, style_dict, style, session

    theme_names = list(themes.keys())
    selected_index = theme_names.index(theme_name)

    def get_display_text():
        """Returns the list of themes with the selected one highlighted."""
        text = []
        for i, name in enumerate(theme_names):
            prefix = "> " if i == selected_index else "  "
            style = "bold yellow" if i == selected_index else "white"
            text.append((style, f"{prefix}{name}\n"))
        return text

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    def move_up(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(theme_names)

    @kb.add("down")
    def move_down(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(theme_names)

    @kb.add("enter")
    def select_theme(event):
        """Set the theme, update config, and apply immediately."""
        global theme_name, style_dict, style, session
        theme_name = theme_names[selected_index]
        style_dict = themes[theme_name]
        
        # Apply the new style
        style = Style.from_dict({
            'prompt': style_dict["prompt"],
            '': style_dict["input"]
        })
                
        display("output", f"Theme set to|set|{theme_name}.")
        
        # Save the selected theme to config
        save_config({
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden_files,
            "theme": theme_name,
            "markdown": markdown,
        })

        # Re-create the session to apply the new style
        session = PromptSession(key_bindings=kb, style=style)
        
        event.app.exit()

    @kb.add("escape")
    def cancel_selection(event):
        """Cancel theme selection and exit."""
        display("highlight", f"Theme selection cancelled.")
        event.app.exit()

    # Display layout for theme selection
    theme_selection_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False)
    layout = Layout(HSplit([Frame(theme_selection_window)]))

    # Application
    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    app.run()
    return False

@command("/file", description="Insert the contents of a file at a specified path for analysis.")
def file_command(contents=''):
    """Handle /file command, allowing it to work consistently as a standalone or inline command."""

    # Replace any /file references with the contents of the specified file
    processed_text = replace_file_references("/file" + contents)
    
    if processed_text is None:
        display("highlight", f"File selection cancelled or not processed.")
        return False

    # Pass the processed input to ask_ai function
    response = ask_ai(processed_text)

    return False

# Update the system prompt and save to config when running /system command
@command("/system", description="Set a new system prompt.")
def system_command(contents=None):
    global system_prompt

    display("highlight", f"Editing system prompt (Vim mode enabled):")

    kb = KeyBindings()

    @kb.add("escape", "enter")
    def submit(event):
        event.app.current_buffer.validate_and_handle()

    session = PromptSession(
        vi_mode=True,  # Vim mode
        multiline=True,  # Enable multi-line editing
        key_bindings=kb  # Custom key binding for Escape + Enter
    )

    try:
        new_prompt = session.prompt(">>> ", default=system_prompt).strip()
        if new_prompt:
            system_prompt = new_prompt
            display("output", f"System prompt updated to:|set|\n{system_prompt}")

            # Update the configuration file with the new system prompt
            save_config({"model": model, "system_prompt": system_prompt})
        else:
            display("error", f"System prompt cannot be empty!")
    except KeyboardInterrupt:
        display("error", "Cancelled system prompt editing.")

    return False

@command("/show_system", description="Show the current system prompt.")
def show_system_command(contents=None):
    """Display the current system prompt."""
    display("highlight", f"Current system prompt:|set|{system_prompt}")
    return False

@command("/history", description="Show the chat history.")
def history_command(contents=None):
    """Handle the /history command showing the history of the chat."""
    if not messages:
        display("highlight", f"No chat history available.")
    else:
        for msg in messages:
            role = f"[bold green]{username}:[/bold green]" if msg["role"] == "user" else "[bold blue]Assistant:[/bold blue]"
            console.print(role)  # Display role with color
            console.print(Markdown(msg["content"]))  # Display content formatted as Markdown
    return False

# Update the model and save to config when selecting from models
@command("/models", description="Select the AI model to use.")
def models_command(contents=None):
    global model
    models = []

    # Gather OpenAI available models
    try:
        response = client.models.list()
        for model_data in response:
            models.append("openai:" + model_data.id)
    except Exception as e:
        console.print(f"Error getting openai models: {e}")
        pass

    # Gather Ollama available models
    try:
        response = oclient.list()
        for model_data in response['models']:
            models.append("ollama:" + model_data.model)
    except Exception as e:
        console.print(f"Error getting ollama models: {e}")
        pass

    if not models:
        display("error", "No models available.")
        return False

    # Sort models alphabetically
    models.sort()

    # Initial setup for model selection
    selected_index = 0
    visible_start = 0

    terminal_height = int(os.get_terminal_size().lines)
    visible_end = terminal_height

    def get_display_text():
        """Returns the list of models with the selected one highlighted and scrolling window."""
        text = []
        for i in range(visible_start, visible_end):
            model_name = models[i]
            prefix = "> " if i == selected_index else "  "
            style = "bold yellow" if i == selected_index else "white"
            text.append((style, f"{prefix}{model_name}\n"))
        return text

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    def move_up(event):
        nonlocal selected_index, visible_start, visible_end
        if selected_index > 0:
            selected_index -= 1
            # Scroll up if the selected index is above the visible window
            if selected_index < visible_start:
                visible_start -= 1
                visible_end -= 1

    @kb.add("down")
    def move_down(event):
        nonlocal selected_index, visible_start, visible_end
        if selected_index < len(models) - 1:
            selected_index += 1
            # Scroll down if the selected index is below the visible window
            if selected_index >= visible_end:
                visible_start += 1
                visible_end += 1

    @kb.add("enter")
    def select_model(event):
        """Set the global model to the selected model, update config, and exit."""
        global model
        model = models[selected_index]
        display("highlight", f"Selected model:|set|{model}")
        
        # Update the configuration file with the new model
        save_config({"model": model, "system_prompt": system_prompt})
        
        event.app.exit()

    @kb.add("escape")
    def cancel_selection(event):
        """Cancel model selection and exit."""
        display("highlight", "Model selection cancelled.")
        event.app.exit()

    # Display layout for model selection
    model_selection_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False)
    layout = Layout(HSplit([Frame(model_selection_window)]))

    # Application
    app = Application(layout=layout, key_bindings=kb, full_screen=True)

    # Run the application
    app.run()

    return False

@command("/settings", description="Display or modify the current configuration settings.")
def settings_command(contents=None):
    """Displays or modifies the current configuration settings."""
    global model, markdown, system_prompt, show_hidden_files, theme_name, username, style_dict, style

    args = contents.strip().split()

    if len(args) == 0:
        # No additional arguments: show settings
        current_settings = {
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden_files,
            "theme": theme_name,
            "markdown": markdown,
            "username": username
        }

        table = Table(title="Current Configuration Settings", show_header=True, header_style=style_dict["highlight"], expand=True)
        table.add_column("Setting", style=style_dict["prompt"], ratio=1)
        table.add_column("Value", ratio=3)

        for setting, value in current_settings.items():
            table.add_row(setting, str(value))

        console.print(table)

    elif len(args) >= 2:
        # Additional arguments provided: update a specific setting
        key = args[0]
        value = " ".join(args[1:])  # Combine all subsequent words as the value

        # Convert recognized boolean values
        bool_map = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}

        if key == "model":
            model = value
        elif key == "system_prompt":
            system_prompt = value
        elif key == "show_hidden_files":
            show_hidden_files = bool_map.get(value.lower(), show_hidden_files)
        elif key == "theme" and value in themes:
            theme_name = value
            style_dict = themes[theme_name]
            style = Style.from_dict({
                'prompt': style_dict["prompt"],
                '': style_dict["input"]
            })
        elif key == "username":
            username = value
        elif key == "markdown":
            markdown = bool_map.get(value.lower(), markdown)
        else:
            display("error", f"Invalid setting key:|set|{key}")
            return False

        # Save the updated configuration
        save_config({
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden_files,
            "theme": theme_name,
            "username": username,
            "markdown": markdown
        })

        display("highlight", f"Updated {key} to:|set|{value}")
    else:
        display("error", "Invalid command usage. Use /settings <key> <value> to update a setting.")

    return False


@command("/flush", description="Clear the chat history.")
def flush_command(contents=None):
    """Handle the /flush command to clear the chat history."""
    global messages
    messages.clear()
    display("highlight", f"Chat history has been flushed.")

    return False

@command("/exit", description="Exit the chatbot.")
def exit_command(contents=None):
    """Handle the /exit command to close the chatbot."""
    display("footer", "\nExiting!")
    return True  # Signal to exit the main loop

@command("/help", description="Display this help message with all available commands.")
def help_command(contents=None):
    """Display a list of available commands in a table format with descriptions."""
    table = Table(title="Available Commands", show_header=True, header_style=style_dict["highlight"], expand=True)
    table.add_column("Command", style=style_dict["prompt"], ratio=1)
    table.add_column("Description", ratio=3)

    # Show the unique $ command
    table.add_row('$', "Execute all following commands in bash.")

    # Populate the table with commands and descriptions
    for cmd, info in command_registry.items():
        table.add_row(cmd, info["description"])

    console.print(table)
    return False  # Continue execution

def extract_code_blocks(text):
    """Extracts all code blocks enclosed in triple backticks."""
    pattern = r"```(?:\w+\n)?([\s\S]*?)```"
    return re.findall(pattern, text)

def ask_ai(text, stream=True, code_exec=False):
    global model, markdown
    text = replace_file_references(text)  # Replace any /file references with file contents
    if text is None:
        return None

    messages.append({"role": "user", "content": text})  # Add user message to history
    request_messages = [{"role": "system", "content": system_prompt}] + messages
    response = ''

    if markdown:
        live = Live(console=console, refresh_per_second=100)
        live.start()

    if model.startswith("openai"):
        model_name = model.split(":")[1]
        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=request_messages,
                stream=stream,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    if markdown:
                        live.update(Markdown(response))
                    else:
                        console.print(chunk.choices[0].delta.content, end='', flush=True)
        except Exception as e:
            display("error", f"OpenAI error: {e}")
            return "An error occurred while communicating with the LLM."

    elif model.startswith("ollama"):
        model_name = model.split(":")[1] + ":" + model.split(":")[2]
        try:
            stream = oclient.chat(
                model=model_name,
                messages=request_messages,
                stream=stream,
                options={"num_ctx": 16000},
            )

            for chunk in stream:
                response += chunk['message']['content']
                if markdown:
                    live.update(Markdown(response))
                else:
                    console.print(chunk['message']['content'], end='', flush=True)
        except Exception as e:
            display("error", f"Ollama error: {e}")
            return "An error occurred while communicating with the LLM."

    messages.append({"role": "assistant", "content": response.strip()})

    # Stop live rendering
    try:
        if live.is_started:
            live.stop()
    except:
        pass

    # Extract and handle code execution prompt
    if code_exec:
        code_blocks = extract_code_blocks(response)
        if code_blocks:
            for code in code_blocks:
                code = code.strip()
                display("highlight", f"\n\nWould you like to run the following?")
                display("output", f"{code}")

                # Prompt user for execution
                answer = Confirm.ask("Do you want to continue?\n[y/n]: ")
                if answer:
                    run_system_command(code)  # Execute the command

    return response.strip()
    
def run_system_command(command):
    """Run a system command, capture both stdout and stderr, and store output in messages."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        output = ""

        if result.stdout:
            output += f"{result.stdout}"
            display("output", f"\nOutput:|set|{result.stdout}")

        if result.stderr:
            output += f"{result.stderr}"
            display("error", f"\nError:|set|{result.stderr}")

        # Append the command and its output to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{output.strip()}"})
        return output.strip()

    except Exception as e:
        error_message = f"Command execution error: {e}"
        display("error", f"{error_message}")
        # Append the error to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{error_message}"})
        return error_message
def get_system_context() -> str:
    """
    Gather system and context information for inclusion in an AI system prompt, including detailed MacBook info.

    Returns:
        A formatted string containing system details.
    """
    # Operating System and Version
    os_name = platform.system()  # e.g., "Linux", "Windows", "Darwin" (macOS)
    os_version = platform.release()  # e.g., "23.0.0" (macOS), "5.15.0-73-generic" (Linux)
    os_details = platform.platform()  # e.g., "Darwin-23.0.0-x86_64-i386-64bit"

    # Current Date and Time
    now = datetime.datetime.now()
    local_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., "2025-03-15 19:00:00"

    # Timezone (fallback if pytz isn’t installed)
    try:
        import pytz  # Optional dependency
        timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzname()  # e.g., "PDT"
    except ImportError:
        timezone = "Unknown (pytz not installed)"

    # User and Host
    username = getpass.getuser()  # e.g., "john_doe"
    hostname = platform.node()  # e.g., "Johns-MacBook-Pro"

    # Current Working Directory
    cwd = os.getcwd()  # e.g., "/Users/john_doe/projects"

    # Architecture and Python Version
    architecture = platform.machine()  # e.g., "arm64", "x86_64"
    python_version = platform.python_version()  # e.g., "3.11.2"

    # Hardware Model, Chip, and Memory (platform-specific)
    hardware_model = "Unknown"
    chip = "Unknown"
    memory = "Unknown"
    os_full_name = f"{os_name} {os_version}"
    
    if os_name == "Darwin":  # macOS
        try:
            # Hardware Model (e.g., "MacBook Pro (16-inch, Nov 2004)")
            hardware_model_raw = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()  # e.g., "MacBookPro15,1"
            profiler_output = subprocess.check_output(["system_profiler", "SPHardwareDataType"], text=True)
            model_match = re.search(r"Model Name: (.*)", profiler_output)
            size_match = re.search(r"Model Identifier:.*(\d+-inch)", profiler_output)
            date_match = re.search(r"Model Identifier:.*(\d{4})", profiler_output)
            
            model_name = model_match.group(1) if model_match else "MacBook"
            size = size_match.group(1) if size_match else ""
            date = date_match.group(1) if date_match else ""
            hardware_model = f"{model_name} ({size}, {date})" if size and date else hardware_model_raw

            # Chip (e.g., "Apple M4 Max")
            chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()

            # Memory (e.g., "36 GB")
            memory_raw = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()  # Bytes
            memory_gb = int(memory_raw) / (1024 ** 3)  # Convert to GB
            memory = f"{round(memory_gb)} GB"

            # Full OS Name (e.g., "macOS Sequoia 15.3.2")
            os_product = subprocess.check_output(["sw_vers", "-productName"], text=True).strip()  # e.g., "macOS"
            os_version_full = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()  # e.g., "15.3.2"
            os_build = subprocess.check_output(["sw_vers", "-buildVersion"], text=True).strip()  # e.g., "24D50"
            os_full_name = f"{os_product} {os_version_full} (Build {os_build})"
            # Note: macOS codename (e.g., "Sequoia") isn’t directly available via CLI; we could map version to name if desired

        except subprocess.CalledProcessError:
            hardware_model = "macOS (model unavailable)"
            chip = "macOS (chip unavailable)"
            memory = "macOS (memory unavailable)"
    elif os_name == "Linux":
        try:
            with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                hardware_model = f.read().strip()
        except FileNotFoundError:
            hardware_model = "Linux (model unavailable)"
    elif os_name == "Windows":
        hardware_model = platform.uname().machine  # e.g., "AMD64"

    # Current Shell
    shell = "Unknown"
    if os_name in ["Linux", "Darwin"]:
        shell = os.environ.get("SHELL", "Unknown")
        shell = os.path.basename(shell)  # e.g., "zsh", "bash"
    elif os_name == "Windows":
        shell = os.environ.get("COMSPEC", "cmd.exe")
        shell = os.path.basename(shell)
        if "powershell" in sys.executable.lower() or "PS1" in os.environ:
            shell = "powershell"

    # Construct the system context string
    context = (
        f"System Context:\n"
        f"- Operating System: {os_full_name}\n"
        f"- Hardware Model: {hardware_model}\n"
        f"- Chip: {chip}\n"
        f"- Memory: {memory}\n"
        f"- Date and Time: {local_time}\n"
        f"- Timezone: {timezone}\n"
        f"- User: {username}@{hostname}\n"
        f"- Current Working Directory: {cwd}\n"
        f"- Shell: {shell}\n"
        f"- Architecture: {architecture}\n"
        f"- Python Version: {python_version}"
        f"Instructions:\n",
        f"IMPORTANT: All function calling will be run prior to your response.\n",
    )

    return context

# ---------- Functions For Function Calling ----------
# Persistent namespace for the Python environment
persistent_python_env = {}
def run_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code in a persistent environment and return its output.

    Args:
        code (str): A string containing Python code to execute.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): 'success', 'error', or 'cancelled'
            - output (str, optional): The captured stdout if execution succeeded or partially executed
            - error (str, optional): The captured stderr or exception message if execution failed
            - message (str, optional): A message if execution was cancelled
            - namespace (dict, optional): Current state of the persistent environment (non-builtin variables)

    Notes:
        - Executes code in a persistent namespace, preserving variables across calls.
        - Prompts the user for confirmation before execution.
        - Captures and displays both stdout and stderr using the rich console.
        - Returns early with a 'cancelled' status if the user declines execution.
    """

    console.print(Syntax(f"\n{code.strip()}\n", "python", theme="monokai"))

    # Ask for user confirmation
    answer = Confirm.ask("execute? [y/n]:", default=False)
    if not answer:
        console.print("[red]Execution cancelled[/red]")
        return {"status": "cancelled", "message": "Execution aborted by user. Continue forward."}

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    console.print(Rule())
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute the code in the persistent namespace
            exec(code, persistent_python_env)
        
        stdout_output = stdout_capture.getvalue().strip()
        stderr_output = stderr_capture.getvalue().strip()

        # Display output if any
        if stdout_output:
            console.print(stdout_output)
        if stderr_output:
            console.print(f"[red]Error output:[/red] {stderr_output}")

        console.print(Rule())

        return {
            "status": "success",
            "output": stdout_output,
            "error": stderr_output if stderr_output else None,
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }

    except Exception as e:
        stderr_output = stderr_capture.getvalue().strip() or str(e)
        console.print(f"[red]Execution failed:[/red] {stderr_output}")
        console.print(Rule())

        return {
            "status": "error",
            "error": stderr_output,
            "output": stdout_capture.getvalue().strip() if stdout_capture.getvalue() else None,
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }

def run_bash_command(command: str) -> Dict[str, Any]:
    """
    Execute a Bash one-liner command securely and return its output.

    Args:
        command (str): The Bash command to execute.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): 'success' or 'error'
            - output (str, optional): The command's standard output if successful
            - error (str, optional): Error message or stderr if execution failed
            - return_code (int, optional): The command's return code if successful

    Notes:
        - Prompts the user for confirmation before execution.
        - Displays the command and its output using the rich console.
        - Cancels execution if the user declines confirmation.
    """

    console.print(Syntax(f"\n{command.strip()}\n", "bash", theme="monokai"))

    # Ask for user confirmation
    answer = Confirm.ask("execute? [y/n]:", default=False)
    if not answer:
        console.print("[red]Execution cancelled[/red]")
        return {"status": "cancelled", "message": "Execution aborted by user. Continue forward."}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        console.print(Rule())
        console.print(result.stdout.strip())
        console.print(Rule())

        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Command timed out."}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_website_data(url: str) -> Dict[str, Any]:
    """
    Extract all viewable text from a webpage given a URL and format it for LLM use.

    Args:
        url (str): The URL of the webpage to extract text from.

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): The extracted and cleaned text if successful
            - url (str): The original URL
            - error (str, optional): Error message if the operation failed

    Raises:
        None: Errors are caught and returned in the response dictionary.

    Examples:
        {'status': 'success', 'text': 'Example text...', 'url': 'https://example.com'}
    """

    
    try:
        # Fetch webpage content
        console.print(f"Fetching:\n[bright_cyan]{url}[/bright_cyan]\n")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
            
        # Extract all text and clean it
        text = soup.get_text()
        
        # Remove excessive whitespace and normalize
        cleaned_text = " ".join(text.split())

        #console.print(Markdown(f"```\n{cleaned_text}\n```\n"))

        return {
            "status": "success",
            "text": cleaned_text,
            "url": url
        }
        
    except requests.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to fetch webpage: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error processing webpage: {str(e)}",
            "url": url
        }

def google_search(query: str) -> Dict[str, Any]:
    """
    Perform a Google search using the Custom Search JSON API and return the results.

    Args:
        query (str): The search query to send to Google.

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): The cleaned search results (titles and snippets) if successful
            - error (str, optional): Error message if the operation failed

    Raises:
        None: Errors are caught and returned in the response dictionary.

    Examples:
        {'status': 'success', 'text': 'Result 1: Title - Snippet\nResult 2: Title - Snippet', 'error': None}
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_API_CX")
    #cse_id = "your-cse-id-here"  # Replace with your Custom Search Engine ID

    if not api_key:
        return {"status": "error", "error": "Google API key not set in environment variable GOOGLE_API_KEY"}

    try:
        # Google Custom Search API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": 10  # Number of results (max 10 per request)
        }

        console.print(f"Searching Google for:\n[bright_cyan]{query}[/bright_cyan]\n")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        items = data.get("items", [])

        # Extract titles and snippets
        results = []
        for item in items:
            title = item.get("title", "No title")
            snippet = item.get("snippet", "No snippet").replace("\n", " ")
            results.append(f"{title} - {snippet}")

        # Combine results into a single cleaned text string
        cleaned_text = " ".join(results)

        return {
            "status": "success",
            "text": cleaned_text,
            "error": None
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to fetch search results: {str(e)}",
            "query": query
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error processing search: {str(e)}",
            "query": query
        }

def handle_command(command):
    parts = command.split(" ", 1)
    command = parts[0].strip().lower()
    contents = parts[1] if len(parts) > 1 else '' 

    if command in command_registry:
        return command_registry[command]["func"](contents)  # Call the registered command function
    else:
        return False

def main():
    """
    The main function that handles both command-line input and interactive mode.
    Handles Ctrl+C gracefully to exit like /exit in all modes.
    """
    command_input = False
    user_input = False
    piped_input = False

    model_name = model.split(":")[1]
    if model.startswith("openai:"):
        ai = Interactor(model=model_name)
    elif model.startswith("ollama:"):
        ai = Interactor(base_url="http://localhost:11434/v1", model=model_name)
    else:
        ai = Interactor()

    ai.add_function(run_bash_command)
    ai.add_function(run_python_code)
    ai.add_function(get_website_data)
    ai.add_function(google_search)
    ai.set_system(f"{get_system_context()}\n\n{system_prompt}\n")

    try:
        if len(sys.argv) > 1:
            command_input = True
            user_input = " ".join(sys.argv[1:]).strip()

        if not sys.stdin.isatty():
            command_input = True
            piped_input = sys.stdin.read().strip()

        if command_input:
            query = ""
            if user_input:
                if user_input.startswith("/"):
                    handle_command(user_input)
                    return
                query += user_input

            if piped_input:
                if piped_input.startswith("/"):
                    handle_command(piped_input)
                    return
                if user_input:
                    query = f"{user_input}\n\n```\n{piped_input}\n```\n"
                else:
                    query = piped_input
                console.print(Markdown(f"\n```\n{piped_input}\n```\n"))

            re = ai.interact(query, stream=True, markdown=markdown)
            return

        # Key bindings for interactive mode
        kb = KeyBindings()

        @kb.add("escape", "enter")
        def submit_event(event):
            event.app.current_buffer.validate_and_handle()

        @kb.add("/")
        def insert_slash(event):
            event.app.current_buffer.insert_text("/")

        @kb.add("c-c")
        def exit_on_ctrl_c(event):
            """Handle Ctrl+C to exit gracefully like /exit."""
            display("footer", "\nExiting!")

        history = InMemoryHistory()
        style = Style.from_dict({
            'prompt': style_dict["prompt"],
            '': style_dict["input"]
        })

        session = PromptSession(
            key_bindings=kb,
            style=style,
            vi_mode=True,
            history=history
        )

        display("highlight", f"EchoAI!|set|Type /help for more information.\nUse escape-enter to submit input.")

        while True:
            ai.set_system(f"{get_system_context()}\n\n{system_prompt}\n")
            style = Style.from_dict({
                'prompt': style_dict["prompt"],
                '': style_dict["input"]
            })

            try:
                text = session.prompt(
                    [("class:prompt", f"{username}: ")],
                    multiline=True,
                    prompt_continuation="... ",
                    style=style
                )

                # Check if text is a string before calling strip()
                if isinstance(text, str):
                    if text.strip() == "":
                        continue
                    if text.startswith("/"):
                        should_exit = handle_command(text)
                        if should_exit:
                            break
                    elif text.startswith("$"):
                        response = run_system_command(text[1:].strip())
                    else:
                        re = ai.interact(text, stream=True, markdown=markdown)
                elif text == "exit":  # Handle Ctrl+C exit signal from key binding
                    break

            except KeyboardInterrupt:
                # Handle Ctrl+C outside prompt_toolkit
                display("footer", "\nExiting!")
                sys.exit(0)
                break
            except EOFError:
                # Handle Ctrl+D (Unix)
                display("footer", "\nExiting!")
                sys.exit(0)
                break
            except Exception as e:
                display("error", f"Unexpected error: {str(e)}")
                continue

            console.print("\n")

    except KeyboardInterrupt:
        # Handle Ctrl+C in command-line or piped input mode
        display("footer", "\nExiting!")
        sys.exit(0)
    except Exception as e:
        display("error", f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
