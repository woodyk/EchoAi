#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-08 15:53:15
# Modified: 2025-03-12 18:59:37

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
from openai import OpenAI
from ollama import Client
from pathlib import Path
import magic
import PyPDF2
import docx

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

class PythonInterpreter:
    def __init__(self):
        self.global_env = {}

    def execute_code(self, code: str):
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        output_data = None
        image_data = None

        try:
            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                exec(code, self.global_env)
            output = stdout_buffer.getvalue()

            # Capture pandas DataFrame output (if any)
            for var in self.global_env.values():
                if isinstance(var, pd.DataFrame):
                    output_data = var.to_dict()

            # Capture matplotlib plots (if generated)
            fig = plt.gcf()
            if fig.get_axes():
                buf = BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                image_data = base64.b64encode(buf.read()).decode()
                plt.close(fig)
        except Exception:
            output = stderr_buffer.getvalue() + "\n" + traceback.format_exc()

        return {"text_output": output.strip(), "data_output": output_data, "image_output": image_data}

# Global persistent interpreter instance for /py command
python_interpreter = PythonInterpreter()

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
def save_config(config):
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

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
    current_path = Path.home()  # Start in the user's home directory
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

@command("/py", description="Execute Python code in a persistent Python environment. Usage: /py <code>")
def python_command(contents=None):
    """
    Executes Python code provided after /py and displays any text output,
    JSON representation of DataFrames, or Base64-encoded matplotlib plots.
    """
    if not contents:
        display("error", "No Python code provided. Usage: /py <code>")
        return False

    result = python_interpreter.execute_code(contents)
    if result["text_output"]:
        display("output", f"Text Output:\n{result['text_output']}")
    if result["data_output"]:
        display("output", f"Data Output (JSON):\n{json.dumps(result['data_output'], indent=2)}")
    if result["image_output"]:
        display("output", f"Image Output (Base64):\n{result['image_output'][:100]}... (truncated)")
    return False

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
        print(f"Error getting openai models: {e}")
        pass

    # Gather Ollama available models
    try:
        response = oclient.list()
        for model_data in response['models']:
            models.append("ollama:" + model_data.model)
    except Exception as e:
        print(f"Error getting ollama models: {e}")
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
    display("footer", "Exiting!")
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

def ask_ai(text, stream=True):
    global model, markdown
    text = replace_file_references(text)  # Replace any /file references with file contents
    if text is None:
        return None

    messages.append({"role": "user", "content": text})  # Add user message to history
    request_messages = [{"role": "system", "content": system_prompt}] + messages
    response = ''

    if markdown:
        live = Live(console=console, refresh_per_second=10)
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
                        print(chunk.choices[0].delta.content, end='', flush=True)
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
                    print(chunk['message']['content'], end='', flush=True)
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
    code_blocks = extract_code_blocks(response)
    if code_blocks:
        for code in code_blocks:
            code = code.strip()
            display("highlight", f"\n\nWould you like to run the following?")
            display("output", f"{code}")

            # Prompt user for execution
            user_input = input("[y/n]: ").strip().lower()
            if user_input == 'y':
                run_system_command(code)  # Execute the command

    return response.strip()
    
def run_system_command(command):
    """Run a system command, capture both stdout and stderr, and store output in messages."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        output = ""

        if result.stdout:
            output += f"{result.stdout}"
            display("output", f"\nOutput:|set|\n{result.stdout}")

        if result.stderr:
            output += f"{result.stderr}"
            display("error", f"\nError:|set|\n{result.stderr}")

        # Append the command and its output to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{output.strip()}"})
        return output.strip()

    except Exception as e:
        error_message = f"Command execution error: {e}"
        display("error", f"{error_message}")
        # Append the error to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{error_message}"})
        return error_message

def handle_command(command):
    parts = command.split(" ", 1)
    command = parts[0].strip().lower()
    contents = parts[1] if len(parts) > 1 else '' 

    if command in command_registry:
        return command_registry[command]["func"](contents)  # Call the registered command function
    else:
        return False  # Continue execution

def main():
    """
    The main function that handles both command-line input and interactive mode.
    """
    if len(sys.argv) > 1:
        # One-shot mode: process input directly and return response
        user_input = " ".join(sys.argv[1:]).strip()
        if user_input:
            if user_input.startswith("/"):
                # If the input is a command, execute it and exit
                handle_command(user_input)
            else:
                ask_ai(user_input, stream=True)  # Stream response directly
        return  # Exit after processing the command

    # Check if there's piped input
    if not sys.stdin.isatty():  # If input is not coming from the terminal
        piped_input = sys.stdin.read().strip()
        if piped_input:
            if piped_input.startswith("/"):
                handle_command(piped_input)  # Execute commands from pipe input
            else:
                ask_ai(piped_input, stream=True)
        return  # Exit after processing piped input

    # Key bindings for using Escape + Enter to submit input in interactive mode
    kb = KeyBindings()

    @kb.add("escape", "enter")
    def submit_event(event):
        event.app.current_buffer.validate_and_handle()

    # Disable default Vim '/' search behavior
    @kb.add("/")
    def insert_slash(event):
        event.app.current_buffer.insert_text("/")

    # Create an in-memory history for Up/Down navigation
    history = InMemoryHistory()

    # Define or update the style based on the selected theme
    style = Style.from_dict({
        'prompt': style_dict["prompt"],
        '': style_dict["input"]
    })

    # Interactive chatbot mode
    session = PromptSession(
            key_bindings=kb,
            style=style,
            vi_mode=True,
            history=history
        )

    display("highlight", f"EchoAI!|set|Type /help for more information.\nUse escape-enter to submit input.")

    while True:
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

            if text.strip() == "":
                continue

            if text.startswith("/"):
                should_exit = handle_command(text)
                if should_exit:
                    break
            elif text.startswith("$"):
                response = run_system_command(text[1:].strip())
            else:
                response= ask_ai(text, stream=True)

        except (KeyboardInterrupt, EOFError):
            display("footer", f"Exiting!")
            break

        console.print("\n")

if __name__ == "__main__":
    main()

