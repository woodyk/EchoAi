# EchoAI

## Overview
EchoAI is a command-line based AI assistant that leverages OpenAI and Ollama models to provide interactive assistance in various tasks. It is designed to be user-friendly, allowing for markdown formatting, file manipulation, and various configuration options.

## Author
- **Wadih Khairallah**

## Installation

Ensure you have Python 3.13.2 or later installed. You may want to create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required packages:

```bash
pip install rich prompt_toolkit openai ollama python-magic PyPDF2 python-docx pandas
```

Make sure to set up your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Usage

To run the application, simply execute:

```bash
python main.py
```

### Commands

Once the application is running, you can use the following commands:

- `/help`: Displays available commands.
- `/exit`: Exits the application.
- `/flush`: Clears the chat history.
- `/show_model`: Displays the currently configured AI model.
- `/theme`: Select a theme for the application.
- `/file <path>`: Inserts the contents of a specified file for analysis.
- `/system`: Set a new system prompt.
- `/show_system`: Show the current system prompt.
- `/history`: Show the chat history.
- `/models`: Select the AI model to use.
- `/settings`: Display or modify current configuration settings.

### Configuration

EchoAI allows for customization via a configuration file located at `~/.echoai`. The configuration includes:

- `model`: The AI model to use (default: `openai:gpt-4o`).
- `system_prompt`: The system prompt for the AI assistant.
- `show_hidden_files`: Boolean to determine whether to show hidden files in file selections.
- `username`: The username displayed in the application.
- `markdown`: Boolean to determine if markdown should be used for output.
- `theme`: Current theme of the application.
- `tools`: Whether tools are available for use.

Changes to settings can be made via the `/settings` command.

## Features

- Interactive command-line interface.
- File manipulation capabilities for reading text files, PDFs, and Word documents.
- The ability to run shell commands using the `$` command.
- Supports markdown output for better text formatting.

## Dependencies

- Python 3.13.2 or later
- Libraries: `rich`, `prompt_toolkit`, `openai`, `ollama`, `python-magic`, `PyPDF2`, `python-docx`, `pandas`

## License

This project is licensed under the MIT License.
