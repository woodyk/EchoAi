
# EchoAI

EchoAI is an interactive, terminal-based AI chatbot that allows users to interact with an AI model, execute system commands, browse files, and analyze text from files in various formats. Designed for seamless command-line usage, it offers a range of commands and functionalities for an enriched AI experience.

## Features

- **AI Chat Interaction**: Communicate with an AI model directly from the terminal by simply typing text.
- **System Commands**: Execute shell commands directly using the `$` prefix.
- **File Insertion and Analysis**: Insert file contents using the `/file` command to analyze them with the AI model.
- **Chat History Management**: View and clear the chat history anytime.
- **Customizable System Prompt**: Set a custom system prompt to modify the AI's response style.
- **Integrated File Browser**: Navigate files easily, with support for toggling hidden files using `Ctrl-H`.
- **Configurable Themes**: Choose from multiple themes for a personalized terminal experience.
- **Flexible AI Model Selection**: Switch between available AI models and set the active model for interactions.
- **Configuration Persistence**: Settings such as theme, model, and system prompt are saved and reloaded from a configuration file.

## Requirements

- Python 3.8+
- Required Python libraries:
  - `prompt_toolkit`
  - `rich`
  - `openai` (API key required)
  - `python-docx` (for DOCX file analysis)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/woodyk/EchoAI.git
   cd EchoAI
   ```

2. Install the required dependencies:

   ```bash
   pip install .
   ```

3. Set up your OpenAI API key as an environment variable:

   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

## Usage

Run the script directly from the terminal:

```bash
echoai
```

### Commands

| Command         | Description                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------- |
| `/file <path>`  | Insert the content of the specified file path for AI analysis. Supports `~` for home directory.   |
| `/system`       | Set a new system prompt for the AI model.                                                         |
| `/show_system`  | Display the current system prompt.                                                                |
| `/history`      | Show the chat history.                                                                            |
| `/flush`        | Clear the chat history.                                                                           |
| `/exit`         | Exit the chatbot.                                                                                 |
| `/help`         | Display a list of available commands with descriptions.                                           |
| `/theme`        | Choose a theme for the chatbot interface.                                                         |
| `/models`       | List and select from available AI models.                                                         |
| `/show_model`   | Show the currently configured AI model.                                                           |
| `/settings`     | Display the current configuration settings.                                                       |

### Example Usage

- **Chat with AI**: Type any text to interact with the AI.
- **Execute System Commands**: Prefix commands with `$` to execute them directly.
- **File Insertion**: Use `/file ~/filename.txt` to insert the contents of a file.
- **Show/Hide Hidden Files**: Use `Ctrl-H` in the file browser to toggle hidden files.
- **Theme Selection**: Use `/theme` to select a visual theme for the terminal.
- **Model Selection**: Use `/models` to select an available AI model.

## Configuration

EchoAI saves user configurations (e.g., selected theme, model, system prompt) in a configuration file located at `~/.echoai`. This file is created automatically if it doesn’t exist, and updates with user preferences upon modification. Users can also view and update configurations using commands such as `/theme`, `/models`, and `/system`.

## License

This project is licensed under the MIT License.
