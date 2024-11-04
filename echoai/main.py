#!/usr/bin/env python3
# echoai terminal assistant
# Author: Wadih Khairallah

import sys
import os
import json
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
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
    global model, username, system_prompt, show_hidden_files, theme_name, style_dict
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        model = config.get("model", default_config["model"])
        system_prompt = config.get("system_prompt", default_config["system_prompt"])
        show_hidden_files = config.get("show_hidden_files", default_config["show_hidden_files"])
        theme_name = config.get("theme", default_config["theme"])
        username = config.get("username", default_config["username"])
    else:
        save_config(default_config)  # Save default if file doesn't exist
        model = default_config["model"]
        system_prompt = default_config["system_prompt"]
        show_hidden_files = default_config["show_hidden_files"]
        theme_name = default_config["theme"]
        username = default_config["username"]

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
    show_hidden = show_hidden_files  # Initialize with the config setting

    terminal_height = int(os.get_terminal_size().lines / 2)
    max_display_lines = terminal_height - 2  # Reduce by 2 for header and footer lines

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
            # Show '/' at the end of directory names, but not for the '..' entry
            name = f"{f.name}/" if isinstance(f, Path) and f.is_dir() else f
            line = f"{prefix}{name}"
            text.append((f"bold {'yellow' if real_index == selected_index else 'white'}", line))
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
            event.app.exit(result=selected_file)

    @kb.add("escape")
    def cancel_selection(event):
        event.app.exit(result=None)

    @kb.add("c-h")
    def toggle_hidden(event):
        """Toggle the visibility of hidden files and save to config."""
        nonlocal show_hidden
        show_hidden = not show_hidden
        update_file_list()
        
        # Update configuration for show_hidden_files
        save_config({
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden
        })

    # Layout with footer for shortcut hint
    file_list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False, height=max_display_lines)
    footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to show/hide hidden files. Escape to exit."), height=1, style="bold cyan")
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
            "theme": theme_name
        })

        # Re-create the session to apply the new style
        #session = PromptSession(editing_mode=EditingMode.VI, key_bindings=kb, style=style)
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
    if response:
        console.print(Markdown(response))
    return False

# Update the system prompt and save to config when running /system command
@command("/system", description="Set a new system prompt.")
def system_command(contents=None):
    global system_prompt
    display("highlight", f"Enter new system prompt:")
    new_prompt = input("> ").strip()
    if new_prompt:
        system_prompt = new_prompt
        display("output", f"System prompt updated to:|set|{system_prompt}")
        
        # Update the configuration file with the new system prompt
        save_config({"model": model, "system_prompt": system_prompt})
    else:
        display("error", f"System prompt cannot be empty!")
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
            role = "[bold green]{username}:[/bold green]" if msg["role"] == "user" else "[bold blue]Assistant:[/bold blue]"
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
        pass

    # Gather Ollama available models
    try:
        response = oclient.list()
        for model_data in response['models']:
            models.append("ollama:" + model_data['name'])
    except Exception as e:
        pass

    if not models:
        display("error", "No models available.")
        return False

    # Initial setup for model selection
    selected_index = 0
    visible_start = 0

    terminal_height = int(os.get_terminal_size().lines / 2)
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
    global model, system_prompt, show_hidden_files, theme_name, username, style_dict, style  # Declare globals at the start

    # Check if contents include additional arguments to set a configuration
    args = contents.strip().split()
    
    if len(args) == 0:
        # No additional arguments: show settings
        current_settings = {
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden_files,
            "theme": theme_name,
            "username": username
        }

        table = Table(title="Current Configuration Settings", show_header=True, header_style=style_dict["highlight"])
        table.add_column("Setting", style=style_dict["prompt"])
        table.add_column("Value")

        for setting, value in current_settings.items():
            table.add_row(setting, str(value))

        console.print(table)
    
    elif len(args) >= 2:
        # Additional arguments provided: update a specific setting
        key = args[0]
        value = " ".join(args[1:])  # Combine all subsequent words as the value
        
        # Update configuration based on key
        if key == "model":
            model = value
        elif key == "system_prompt":
            system_prompt = value
        elif key == "show_hidden_files":
            show_hidden_files = value.lower() in ("true", "1", "yes")
        elif key == "theme" and value in themes:
            theme_name = value
            style_dict = themes[theme_name]
            style = Style.from_dict({
                'prompt': style_dict["prompt"],
                '': style_dict["input"]
            })
        elif key == "username":
            username = value
        else:
            display("error", f"Invalid setting key:|set|{key}")
            return False
        
        # Save the updated configuration
        save_config({
            "model": model,
            "system_prompt": system_prompt,
            "show_hidden_files": show_hidden_files,
            "theme": theme_name,
            "username": username
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
@command("/bye", description="Exit the chatbot.")
@command("/quit", description="Exit the chatbot.")
def exit_command(contents=None):
    """Handle the /exit and /quit commands to close the chatbot."""
    display("footer", "Exiting!")
    return True  # Signal to exit the main loop

@command("/help", description="Display this help message with all available commands.")
def help_command(contents=None):
    """Display a list of available commands in a table format with descriptions."""
    table = Table(title="Available Commands", show_header=True, header_style=style_dict["highlight"])
    table.add_column("Command", style=style_dict["prompt"])
    table.add_column("Description")

    # Show the unique $ command
    table.add_row('$', "Execute all following commands in bash.")

    # Populate the table with commands and descriptions
    for cmd, info in command_registry.items():
        table.add_row(cmd, info["description"])

    console.print(table)
    return False  # Continue execution

def ask_ai(text):
    global model
    text = replace_file_references(text)  # Replace any /file references with file contents
    if text is None:
        return None

    messages.append({"role": "user", "content": text})  # Add user message to history
    request_messages = [{"role": "system", "content": system_prompt}] + messages
    response = ''

    if model.startswith("openai"):
        model_name = model.split(":")
        current_model = model_name[1]
        try:
            stream = client.chat.completions.create(
                model=current_model,
                messages=request_messages,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content

            messages.append({"role": "assistant", "content": response.strip()})  # Add assistant's reply to history
            return response.strip()

        except Exception as e:
            display("error", f"OpenAI error: {e}")
            return "An error occurred while communicating with the LLM."

    elif model.startswith("ollama"):
        model_name = model.split(":")
        current_model = model_name[1] + ":" + model_name[2]
        try:
            stream = oclient.chat(
                model=current_model,
                messages = request_messages,
                stream=True,
                options = { "num_ctx": 16000 },
            )

            for chunk in stream:
                response += chunk['message']['content']

            messages.append({"role": "assistant", "content": response.strip()})
            return response.strip()

        except Exception as e:
            display("error", f"Ollama error: {e}")

            return "An error occurred while communicating with the LLM."

def run_system_command(command):
    """Run a system command, capture both stdout and stderr, and store output in messages."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        output = ""

        if result.stdout:
            output += f"{result.stdout}"
            display("output", f"Output:|set|{result.stdout}")

        if result.stderr:
            output += f"{result.stderr}"
            display("error", f"Error:|set|{result.stderr}")

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
        display("error", f"Unknown command:|set|{command}")
        return False  # Continue execution

def main():
    """
    The main function that handles both command-line input and interactive mode.
    """
    # Check if there's piped input
    if not sys.stdin.isatty():  # If input is not coming from the terminal
        piped_input = sys.stdin.read().strip()
        if piped_input:
            if piped_input.startswith("/"):
                # Process as a command if it starts with '/'
                should_exit = handle_command(piped_input)
                return  # Exit after processing the command
            else:
                # Otherwise, treat it as input for the AI
                response = ask_ai(piped_input)
                if response:
                    console.print(Markdown(response))
        return  # Exit after processing piped input

    # Key bindings for using Escape + Enter to submit input in interactive mode
    kb = KeyBindings()

    @kb.add("escape", "enter")
    def submit_event(event):
        event.app.current_buffer.validate_and_handle()

    # Define or update the style based on the selected theme
    style = Style.from_dict({
        'prompt': style_dict["prompt"],
        '': style_dict["input"]
    })

    # Interactive chatbot mode with vi mode and multiline input
    #session = PromptSession(editing_mode=EditingMode.VI, key_bindings=kb, style=style)
    session = PromptSession(key_bindings=kb, style=style)
    display("highlight", f"EchoAI!|set|Type /help for more information.\nUse escape-enter to submit input.")

    while True:
        # Update prompt theme if changed.
        style = Style.from_dict({
            'prompt': style_dict["prompt"],
            '': style_dict["input"]
        })

        try:
            # Enable multiline input with Escape + Enter to submit
            text = session.prompt(
                [("class:prompt", f"{username}: ")],  # This applies the 'prompt' style from the style dictionary
                multiline=True,
                prompt_continuation="... ",
                style=style  # Apply the defined style
            )
            
            if text.strip() == "":
                continue  # Ignore empty inputs

            if text.startswith("/"):
                should_exit = handle_command(text)
                if should_exit:
                    break  # Exit if command returns True
            elif text.startswith("$"):
                # Strip the leading $ and pass the rest as a command
                response = run_system_command(text[1:].strip())
            else:
                response = ask_ai(text)
                if response is None:
                    continue
                console.print(Markdown(response))  # Render response in Markdown format

        except KeyboardInterrupt:
            display("footer", f"Exiting!")
            break
        except EOFError:
            display("footer", f"Exiting!")
            break

if __name__ == "__main__":
    main()

