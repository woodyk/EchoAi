#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-08 15:53:15
# Modified: 2025-03-22 18:41:22

import sys
import os
import re
import json
import subprocess
import platform
import signal
import datetime
import getpass
import pytz

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.prompt import Confirm
from rich.rule import Rule
from openai import OpenAI
from ollama import Client
from pathlib import Path

from .interactor import Interactor
from .themes import themes

from .functions import (
        run_python_code,
        run_bash_command,
        get_weather,
        create_qr_code,
        get_website_data,
        check_system_health,
        duckduckgo_search,
        google_search,
    )

from .textextract import extract_text

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
    "username": "User",
    "markdown": True,
    "theme": "default",
    "stream": True,
    "tools": True
}

# Function for displaying text.
def display(inform, text):
    console.print(f"[{style_dict[inform]}]{text}[/{style_dict[inform]}]")
    return False
    
# Load or initialize the configuration file
def load_config():
    global model, username, stream, system_prompt, markdown, theme_name, style_dict, tools
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        model = config.get("model", default_config["model"])
        system_prompt = config.get("system_prompt", default_config["system_prompt"])
        theme_name = config.get("theme", default_config["theme"])
        username = config.get("username", default_config["username"])
        tools = bool(config.get("tools", default_config["tools"]))
        stream = bool(config.get("stream", default_config["stream"]))

        # Ensure markdown is always a boolean
        markdown_value = config.get("markdown", default_config["markdown"])
        markdown = isinstance(markdown_value, bool) and markdown_value
    else:
        save_config(default_config)  # Save default if file doesn't exist
        model = default_config["model"]
        system_prompt = default_config["system_prompt"]
        theme_name = default_config["theme"]
        username = default_config["username"]
        markdown = default_config["markdown"]
        tools = default_config["tools"]
        stream = default_config["stream"]

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

    load_config()

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
                display("highlight", "Selection cancelled.")
                return None

        try:
            file_text = extract_text(file_path)
            return f"```{file_text.strip()}```"
        except Exception as e:
            display("error", f"Error reading file {file_path}:\n{e}")
            return f"[Error: could not read file {file_path}]"

    # Replace /file with content, return None if any replacement is cancelled
    result = re.sub(r"/file\s*([^\s]+)?", lambda match: file_replacement(match) or "[Cancelled]", text)
    if "[Cancelled]" in result:
        return None
    return result

@command("/show_model", description="Show the currently configured AI model.")
def show_model_command(contents=None):
    """Display the currently configured model."""
    display("highlight", f"Currently configured model: {model}")
    return False  # Continue execution

@command("/theme", description="Select the theme to use for the application.")
def theme_command(contents=None):
    """Handles the selection and configuration of themes to use."""
    global theme_name, style_dict, style, session

    theme_names = list(themes.keys())
    theme_names.sort()
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
                
        display("output", f"Theme set: {theme_name}.")
        
        # Save the selected theme to config
        save_config({"theme": theme_name})

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
    #response = ask_ai(processed_text)

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
            display("output", f"System prompt updated to:\n{system_prompt}")

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
    display("highlight", f"Current system prompt:\n{system_prompt}")
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
        display("highlight", f"Selected model: {model}")
        
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
    global model, markdown, stream, system_prompt, theme_name, username, style_dict, style, tools

    args = contents.strip().split()

    if len(args) == 0:
        # No additional arguments: show settings
        current_settings = {
            "model": model,
            "system_prompt": system_prompt,
            "theme": theme_name,
            "markdown": markdown,
            "username": username,
            "stream": stream,
            "tools": tools  # Added tools to settings display
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
        elif key == "tools":
            tools = bool_map.get(value.lower(), tools)
        elif key == "stream":
            stream = bool_map.get(value.lower(), stream)
        else:
            display("error", f"Invalid setting key: {key}")
            return False

        # Save the updated configuration
        save_config({
            "model": model,
            "system_prompt": system_prompt,
            "theme": theme_name,
            "username": username,
            "markdown": markdown,
            "stream": stream,
            "tools": tools
        })

        display("highlight", f"Updated {key} to: {value}")
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
    sys.exit(0)
    return True  # Signal to exit the main loop

@command("/help", description="Display this help message with all available commands.")
def help_command(contents=None):
    """Display a list of available commands in a table format with descriptions."""
    table = Table(title="Available Commands", show_header=True, header_style=style_dict["highlight"], expand=True)
    table.add_column("Command", style=style_dict["prompt"], ratio=1)
    table.add_column("Description", ratio=3)

    # Populate the table with commands and descriptions, sorted alphabetically by command
    for cmd, info in sorted(command_registry.items()):
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

@command("/$", description="Run shell command.")
def run_system_command(command=None):
    """Run a system command, capture both stdout and stderr, and store output in messages."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        output = ""

        console.print(Rule())
        if result.stdout:
            output += f"{result.stdout}"
            console.print(f"\n{result.stdout}\n") 

        if result.stderr:
            output += f"{result.stderr}"
            console.print(f"\n{result.stdout}\n") 

        console.print(Rule())

        # Append the command and its output to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{output.strip()}"})
    except Exception as e:
        error_message = f"Command execution error: {e}"
        display("error", f"{error_message}")
        # Append the error to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{error_message}"})

    return False

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
        f"The following information is simply for reference if needed.\n",
        f"There is no need to comment on the following unless asked.\n",
        f"```\n"
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
        f"- Python Version: {python_version}\n"
        f"```\n"
    )

    return context

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

    ai = Interactor(model=model)

    ai.add_function(run_bash_command)
    ai.add_function(run_python_code)
    ai.add_function(get_website_data)
    ai.add_function(google_search)
    ai.add_function(duckduckgo_search)
    ai.add_function(check_system_health)
    ai.add_function(create_qr_code)
    ai.add_function(get_weather)
    ai.add_function(extract_text)
    #ai.set_system(f"{system_prompt}\n\n{get_system_context()}\n")
    ai.set_system(f"{system_prompt}")

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

                user_input = replace_file_references(user_input)  # Replace any /file references with file contents
                if user_input is None:
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
                #console.print(Markdown(f"\n```\n{piped_input}\n```\n"))

            response = ai.interact(
                    query,
                    tools=tools,
                    stream=stream,
                    markdown=markdown
                )

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
            sys.exit(0)

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

        while True:
            #ai.set_system(f"{system_prompt}\n\n{get_system_context()}\n")
            ai.set_system(f"{system_prompt}\n")
            style = Style.from_dict({
                'prompt': style_dict["prompt"],
                '': style_dict["input"]
            })

            try:
                user_input = session.prompt(
                    [("class:prompt", f">>> ")],
                    multiline=True,
                    prompt_continuation="... ",
                    style=style
                )
                console.print()

                # Check if user_input is a string before calling strip()
                if isinstance(user_input, str):
                    user_input = replace_file_references(user_input)  # Replace any /file references with file contents
                    if user_input is None:
                        continue
                    if user_input.strip() == "":
                        continue
                    if user_input.startswith("/"):
                        should_exit = handle_command(user_input)
                        if should_exit:
                            break
                    else:
                        response = ai.interact(
                                user_input,
                                model=model,
                                tools=tools,
                                stream=stream,
                                markdown=markdown
                            )
                        console.print("\n")
                elif text == "exit":
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

    except KeyboardInterrupt:
        # Handle Ctrl+C in command-line or piped input mode
        display("footer", "\nExiting!")
        sys.exit(0)
    except Exception as e:
        display("error", f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
