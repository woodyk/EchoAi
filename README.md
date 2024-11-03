
# EchoAI

EchoAI is an interactive, terminal-based AI chatbot that allows users to interact with an AI model, execute system commands, 
browse files, and view extracted text from files in various formats. This script is designed for command-line usage, offering 
a wide range of commands and functionalities for a seamless experience with AI interactions.

## Features

- **AI Chat Interaction**: Communicate with an AI model by simply typing text in the terminal.
- **System Commands**: Execute shell commands directly from the chatbot using the `$` prefix.
- **File Insertion**: Insert the contents of files using the `/file` command to analyze them with the AI model.
- **Chat History**: View and clear the chat history at any time.
- **Customizable System Prompt**: Set a custom system prompt to modify the AI’s response style.
- **File Browser**: Integrated file browser with support for hidden file toggling using `Ctrl-H`.

## Requirements

- Python 3.8+
- `prompt_toolkit`
- `rich`
- `openai` (API key required)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/woodyk/EchoAI.git
   cd EchoAI
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key as an environment variable:

   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

## Usage

Run the script directly from the terminal:

```bash
python echoai.py
```

### Commands

| Command        | Description |
| -------------- | ----------- |
| `/file <path>` | Insert file content at the specified path for analysis. Supports `~` for home directory shortcuts. |
| `/system`      | Set a new system prompt for the AI model. |
| `/show_system` | Display the current system prompt. |
| `/history`     | Show the chat history. |
| `/flush`       | Clear the chat history. |
| `/exit`        | Exit the chatbot. |
| `/help`        | Display a list of available commands and their descriptions. |

### Example Usage

- **Chat with AI**: Type text normally to interact with the AI.
- **System Commands**: Prefix commands with `$` to execute them directly.
- **File Command**: Use `/file ~/filename.txt` to insert the contents of a file.
- **Show/Hide Hidden Files**: Use `Ctrl-H` in the file browser to toggle hidden files.

## License

This project is licensed under the MIT License.
