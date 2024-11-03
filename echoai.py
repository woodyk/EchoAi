#!/usr/bin/env python3

import sys
import os
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
from pathlib import Path
import magic
import PyPDF2
import docx

# Define a custom style for the prompt
style = Style.from_dict({
    'prompt': 'bold yellow'
})

# Initialize the OpenAI Client and Rich Console
client = OpenAI()
client.api_key = os.getenv('OPENAI_API_KEY')

console = Console()
command_registry = {}

messages = []

# Default system prompt
system_prompt = "You are a helpful assistant."

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
        raise ValueError(f"Unsupported file type '{mime_type}'. Only PDF, DOC, DOCX, and text files are supported.")

def prompt_file_selection():
    """Terminal-based file browser using prompt_toolkit to navigate and select files."""
    
    current_path = Path.home()  # Start in the user's home directory
    files = []
    selected_index = 0  # Track the selected file/folder index
    scroll_offset = 0  # Track the starting point of the visible list
    show_hidden = False  # Flag to show or hide hidden files

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
        """Toggle the visibility of hidden files."""
        nonlocal show_hidden
        show_hidden = not show_hidden
        update_file_list()

    # Layout with footer for shortcut hint
    file_list_window = Window(content=FormattedTextControl(get_display_text), wrap_lines=False, height=max_display_lines)
    footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to show/hide hidden files"), height=1, style="bold cyan")
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
            console.print(f"[bold red]Error reading file {file_path}: {e}[/bold red]")
            return f"[Error: could not read file {file_path}]"

    # Replace /file with content, return None if any replacement is cancelled
    result = re.sub(r"/file\s*([^\s]+)?", lambda match: file_replacement(match) or "[Cancelled]", text)
    if "[Cancelled]" in result:
        return None
    return result

@command("/file", description="Insert the contents of a file at a specified path for analysis.")
def file_command(contents=''):
    """Handle /file command, allowing it to work consistently as a standalone or inline command."""

    # Replace any /file references with the contents of the specified file
    processed_text = replace_file_references("/file" + contents)
    
    if processed_text is None:
        console.print("[bold yellow]File selection cancelled or not processed.[/bold yellow]")
        return False

    # Pass the processed input to ask_ai function
    response = ask_ai(processed_text)
    if response:
        console.print(Markdown(response))
    return False

@command("/system", description="Set a new system prompt.")
def system_command(contents=None):
    """Handle the /system command to set a new system prompt."""
    global system_prompt
    console.print("[bold yellow]Enter new system prompt:[/bold yellow]")
    new_prompt = input("> ").strip()
    if new_prompt:
        system_prompt = new_prompt
        console.print(f"[bold green]System prompt updated to:[/bold green] {system_prompt}")
    else:
        console.print("[bold red]System prompt cannot be empty![/bold red]")
    return False

@command("/show_system", description="Show the current system prompt.")
def show_system_command(contents=None):
    """Display the current system prompt."""
    console.print(f"[bold green]Current system prompt:[/bold green] {system_prompt}")
    return False

@command("/history", description="Show the chat history.")
def history_command(contents=None):
    """Handle the /history command showing the history of the chat."""
    if not messages:
        console.print("[bold yellow]No chat history available.[/bold yellow]")
    else:
        for msg in messages:
            role = "[bold green]User:[/bold green]" if msg["role"] == "user" else "[bold blue]Assistant:[/bold blue]"
            console.print(role)  # Display role with color
            console.print(Markdown(msg["content"]))  # Display content formatted as Markdown
    return False

@command("/flush", description="Clear the chat history.")
def flush_command(contents=None):
    """Handle the /flush command to clear the chat history."""
    global messages
    messages.clear()
    console.print("[bold yellow]Chat history has been flushed.[/bold yellow]")
    return False

@command("/exit", description="Exit the chatbot.")
@command("/bye", description="Exit the chatbot.")
@command("/quit", description="Exit the chatbot.")
def exit_command(contents=None):
    """Handle the /exit and /quit commands to close the chatbot."""
    console.print("[bold magenta]Exiting![/bold magenta]")
    return True  # Signal to exit the main loop

@command("/help", description="Display this help message with all available commands.")
def help_command(contents=None):
    """Display a list of available commands in a table format with descriptions."""
    table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="bold cyan")
    table.add_column("Description", style="bold green")

    # Populate the table with commands and descriptions
    for cmd, info in command_registry.items():
        table.add_row(cmd, info["description"])

    console.print(table)
    return False  # Continue execution

def ask_ai(text):
    model = "gpt-4o"  # Ensure this model is available in your Ollama instance

    text = replace_file_references(text)  # Replace any /file references with file contents
    if text is None:
        return None

    messages.append({"role": "user", "content": text})  # Add user message to history
    response = ''
    try:
        # Combine the system prompt with the messages
        request_messages = [{"role": "system", "content": system_prompt}] + messages
        stream = client.chat.completions.create(
            model=model,
            messages=request_messages,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content

        messages.append({"role": "assistant", "content": response.strip()})  # Add assistant's reply to history
        return response.strip()

    except Exception as e:
        console.print(f"[bold red]Ollama error: {e}[/bold red]")
        return "An error occurred while communicating with the LLM."

def run_system_command(command):
    """Run a system command, capture both stdout and stderr, and store output in messages."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        output = ""

        if result.stdout:
            output += f"{result.stdout}"
            console.print(f"[bold green]Output:[/bold green]\n{result.stdout}")
        if result.stderr:
            output += f"{result.stderr}"
            console.print(f"[bold red]Error:[/bold red]\n{result.stderr}")

        # Append the command and its output to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{output.strip()}"})

    except Exception as e:
        error_message = f"Command execution error: {e}"
        console.print(f"[bold red]{error_message}[/bold red]")
        # Append the error to messages for history
        messages.append({"role": "user", "content": f"$ {command}\n{error_message}"})

def handle_command(command):
    parts = command.split(" ", 1)
    command = parts[0].strip().lower()
    contents = parts[1] if len(parts) > 1 else '' 

    if command in command_registry:
        return command_registry[command]["func"](contents)  # Call the registered command function
    else:
        console.print(f"[bold red]Unknown command:[/bold red] {command}")
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
    bindings = KeyBindings()

    @bindings.add("escape", "enter")
    def submit_event(event):
        event.app.current_buffer.validate_and_handle()

    # Interactive chatbot mode with vi mode and multiline input
    session = PromptSession(editing_mode=EditingMode.VI, key_bindings=bindings, style=style)
    console.print("[bold magenta]EchoAI![/bold magenta] Type '/exit' or '/quit' to end.\n")

    while True:
        try:
            # Enable multiline input with Escape + Enter to submit
            text = session.prompt([("class:prompt", "User: ")], multiline=True, prompt_continuation="... ")
            if text.strip() == "":
                continue  # Ignore empty inputs
            if text.startswith("/"):
                should_exit = handle_command(text)
                if should_exit:
                    break  # Exit if command returns True
            elif text.startswith("$"):
                # Strip the leading $ and pass the rest as a command
                run_system_command(text[1:].strip())
            else:
                response = ask_ai(text)
                if response is None:
                    continue
                console.print(Markdown(response))  # Render response in Markdown format

        except KeyboardInterrupt:
            console.print("\n[bold magenta]Exiting![/bold magenta]")
            break
        except EOFError:
            console.print("\n[bold magenta]Exiting![/bold magenta]")
            break

if __name__ == "__main__":
    main()

