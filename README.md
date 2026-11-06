# EchoAI

## Overview
EchoAI is a command-line based AI assistant that leverages OpenAI and Ollama models to provide interactive assistance in various tasks. It is designed to be user-friendly, allowing for markdown formatting, file manipulation, and various configuration options.

Key Features:
- Interactive command-line interface with rich text formatting
- Support for multiple AI providers (OpenAI, Ollama, NVIDIA, Mistral, Grok, DeepSeek)
- File analysis capabilities (text, PDF, Word documents)
- Customizable system prompts and themes
- Built-in shell command execution
- Pluggable LLM tools for tool calling 
- Persistent configuration and chat history

## Author
- **Wadih Khairallah**

## Installation

### Prerequisites
- Python 3.13.2 or later
- pipx (recommended for isolated installation)

### Installation Steps

1. **Using pipx:**
```bash
git clone https://github.com/woodyk/echoai.git
cd echoai
pipx install .
```

2. **Using pip:**
```bash
pip install echoai
```

### API Key Configuration
EchoAI supports multiple AI providers including ollama. Set up your API keys as environment variables:

```bash
export OPENAI_API_KEY="your_api_key_here"
export NVIDIA_API_KEY="your_api_key_here"
export MISTRAL_API_KEY="your_api_key_here"
export GROK_API_KEY="your_api_key_here"
export DEEPSEEK_API_KEY="your_api_key_here"
```

For persistent configuration, add these exports to your shell's rc file (e.g., ~/.bashrc or ~/.zshrc).

## Usage

To run the application after installation, simply execute:

```bash
echoai
```
or
```bash
ai
```

To run the application directly from the cloned github repository.

```bash
python -m venv .venv
. .venv/bin/activate
pip install .
python -m echoai.main
```

### Commands

Once the application is running, you can use the following command to show the available slash commands:

- `/help`: Displays available commands.

### Configuration

EchoAI allows for customization via a configuration file located at `~/.echoai`. The configuration includes:

- `model`: The AI model to use (default: `openai:gpt-4o`).
- `system_prompt`: The system prompt for the AI assistant.
- `username`: The username displayed in the application.
- `markdown`: Boolean to determine if markdown should be used for output.
- `theme`: Current theme of the application.
- `tools`: Whether tools are available for use.

Changes to settings can be made via the `/settings` command.

## Features

### Core Features
- Interactive command-line interface with syntax highlighting
- Multi-provider AI support (OpenAI, Ollama, NVIDIA, Mistral, Grok, DeepSeek)
- File analysis capabilities:
  - Plain text files
  - PDF documents (via PyPDF2)
  - Word documents (via python-docx)
  - Code files with syntax highlighting

### Advanced Features
- Shell command execution (prefix commands with `$`)
- Markdown output formatting
- Persistent configuration (~/.echoai)
- Chat history management "/session"
- LLM task management "/task"
- Custom themes and UI customization "/theme"
- System prompt customization "/system"
- Model selection and switching "/models"

### Session commands

`/session` lists saved conversations, like `/task` and `/tools` list their items.
The current session is marked with `*`. Use `/session show` for current conversation
details and `/session help` for all actions.

Reference a session by its name, full ID, or unique short ID from the list. Quote
names containing spaces when followed by another argument. Tab completion inserts
quoted names automatically; existing duplicate names are completed using IDs.
Names are trimmed when saved, must be nonempty and on one line, and must be unique
without regard to capitalization. Existing duplicate names remain accessible by ID.

| Command | Action |
| --- | --- |
| `/session` or `/session list` | List saved sessions |
| `/session show [session]` | Show current or selected session details |
| `/session new <name>` | Create and load a session |
| `/session load <session>` | Load by name or ID |
| `/session rename <session> <new name>` | Rename a session |
| `/session delete <session>` | Delete a session; deleting the active session enters incognito |
| `/session tag [--remove] <session> <tag1,tag2,...>` | Add or remove trimmed, comma-separated tags |
| `/session summary [session]` | Generate and save a summary of the selected session, defaulting to current |
| `/session branch <message_id> <name>` | Branch the active session through the specified message |
| `/session search <text>` | Search saved messages and show their IDs |
| `/session searchmeta <text>` | Search names, tags, and summaries |
| `/session tui` | Open the session browser; `/session_tui` remains an alias |

Examples:

```text
/session new Project notes
/session load "Project notes"
/session rename "Project notes" Release plan
/session tag "Release plan" work,release
/session show "Release plan"
/session search checklist
```

Ambiguous or missing names and IDs produce an error and keep the active
conversation intact. Summaries use the selected transcript without switching or
adding messages to the active conversation. Saved session files keep their
existing format; no migration is needed.

### Interactive LLM Productivity Features
- File content analysis and summarization
- Code review and debugging assistance
- Documentation generation
- Research assistance
- Task automation
- File system management
- Git repo management
- Coding assistant

### Full screen terminal interface

Run `python -m echoai.app` to open the MadLine TUI. It uses the CLI's Chatbot,
`~/.echoai/config`, session directory, task file, memory database, and registered
tools. Changes to model, prompt, settings, and theme are saved for subsequent CLI
and TUI launches. Tool-specific enable/disable choices apply to the current process,
matching `/tools`; the global `tools` setting is persisted.

| Left menu | CLI counterpart | Behavior |
| --- | --- | --- |
| FILES | `/file "path"` | Browse and extract a file into the input draft; review it before sending |
| MEMORY | `/settings memory true`, `/remember`, `/recall` | Enable or disable memory, save text, and search stored memories |
| MODELS | `/models`, `/settings model provider:model` | Search available models and save the selected model |
| PROMPTS | `/system` | Edit and save the system prompt |
| SESSIONS | `/session tui` and other `/session` actions | Use the shared session browser, naming rules, metadata, and storage |
| SETTINGS | `/settings` | Edit the same validated configuration fields as the CLI |
| TASKS | `/task` | Use the shared task browser and JSON task store |
| THEMES | `/theme` | Preview themes; save a selection or cancel to restore the previous theme |
| TOOLS | `/tools` | Enable or disable registered functions and the global tools setting |

The input accepts the CLI slash commands, including session actions, task actions,
history, tokens, incognito, memory, and `/$ <shell command>`. `/models <model>`,
`/theme <theme>`, and `/system <prompt>` accept direct values in both interfaces;
without arguments they open their respective selectors or editor. `/settings`,
`/session`, `/task`, and `/tools` retain their CLI listing behavior when typed.

Every menu uses the same bordered panel with a scrollable body, status area,
keyboard hint, and bottom action bar. Action buttons have equal widths, stay
centered above the bottom border, and wrap into additional rows on narrow
terminals. **Tab** and **Shift+Tab** visit each enabled field and button; **Enter**
or **Space** activates a focused button, and mouse clicks invoke the same actions.
Unavailable actions remain visible but cannot be activated.

Files has **Open**, **Up**, and **Close** actions. Models and Themes have
**Select/Cancel**, editable settings and prompts have **Save/Cancel**, and Tools
has **Apply/Cancel**. Memory exposes its enable/disable, remember, and recall
actions in the same footer. Session and task browsers also use this template,
with bottom buttons for their list actions and **Create/Save/Search/Cancel**
buttons while editing or searching. Deleting an item opens a separate
**Delete/Cancel** confirmation; cancelling keeps the stored item intact.

Press **Esc then Enter** or **Alt+Enter** to send. **Enter** adds a newline.
**Tab** switches the main panels and moves through dialog fields/actions.
**Ctrl+S** saves settings/prompt forms; **Esc** cancels a dialog. **Ctrl+P/Ctrl+N**
browse input history. **F1** shows command help and **F2** opens the menu.
**Ctrl+C** exits when no operation is running. Model requests, model discovery,
file extraction, and memory initialization run in a worker; the interface blocks
overlapping state changes until the operation finishes and displays errors in the
conversation. Provider/tool operations themselves must finish before exiting.

To run the offline regression suite from a checkout with the normal dependencies:

```bash
python -m unittest discover -s tests -v
```

Tests use actual JSON session/task storage and Urwid rendering with fake model and
embedding implementations, so they do not require API credentials or model downloads.

## Dependencies

### Required Dependencies
- Python 3.13.2 or later
- Core Libraries:
  - `rich`: Terminal formatting and styling
  - `prompt_toolkit`: Interactive command-line interface
  - `openai`: OpenAI API client
  - `ollama`: Ollama API client
  - `python-magic`: File type detection
  - `PyPDF2`: PDF document processing
  - `python-docx`: Word document processing
  - `pandas`: Data analysis (optional for some features)

### Optional Dependencies
- `nvidia-pyindex`: For NVIDIA AI provider support
- `mistralai`: For Mistral AI provider support

## Pluggable LLM Tool Sets

Tool call plugins are located in the `echoai/tools` directory. To add a new tool:

- Place your Python script in `echoai/tools`.
- All **top-level functions** (excluding those prefixed with `_`) are auto-imported.
- **Nested functions** and those starting with `_` are ignored.
- Keep tools **simple and self-contained**—ideally, one function per tool.
- Use **type hints** and a clear **docstring**. These are required for LLM auto-discovery and instruction parsing.

### Example Tool

```python
from typing import Dict

def read_file(path: str) -> Dict[str, str]:
    """
    Reads a file and returns its content or an error message.

    Parameters:
        path (str): File path.

    Returns:
        Dict[str, str]: {
            "status": "success" or "error",
            "content": file content or error message
        }
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "content": str(e)}
```

## Troubleshooting

### Common Issues
1. **API Key Not Found:**
   - Ensure API keys are properly exported in your environment
   - Verify the keys are added to your shell's rc file if using persistent configuration

2. **Installation Errors:**
   - Ensure you have Python 3.13.2 or later
   - Try using `pipx install --force .` if encountering dependency conflicts

3. **File Analysis Issues:**
   - Verify file permissions
   - Ensure required libraries (PyPDF2, python-docx) are installed

4. **Theme or Display Issues:**
   - Try resetting to default theme with `/theme default`
   - Ensure your terminal supports ANSI color codes

## Contributing

We welcome contributions! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description of changes

## Roadmap

Planned future features:
- [ ] Browser integration
- [ ] Plugin system
- [ ] Enhanced memory capabilities
- [ ] Multi-modal support (images, audio)
- [ ] Local model support

## Support

For additional help, please open an issue on the [GitHub repository](https://github.com/woodyk/echoai).

## License

This project is licensed under the MIT License.


# Watermark: 2b0n2b!!! :: Wadih Khairallah :: 2025-06-26T05:16:21.328609+00:00
