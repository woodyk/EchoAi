# EchoAI

## Overview
EchoAI is a command-line based AI assistant that leverages OpenAI and Ollama models to provide interactive assistance in various tasks. It is designed to be user-friendly, allowing for markdown formatting, file manipulation, and various configuration options.

Key Features:
- Interactive command-line interface with rich text formatting
- Support for multiple AI providers (OpenAI, Ollama, NVIDIA, Mistral, Grok, DeepSeek)
- File analysis capabilities (text, PDF, Word documents)
- Customizable system prompts and themes
- Built-in shell command execution
- Persistent configuration and chat history

## Author
- **Wadih Khairallah**

## Installation

### Prerequisites
- Python 3.13.2 or later
- pipx (recommended for isolated installation)

### Installation Steps
```bash
git clone https://github.com/woodyk/echoai.git
cd echoai
pipx install .
```

### Alternative Installation Methods
1. **Using pip (not recommended):**
   ```bash
   pip install echoai
   ```
2. **Development Installation:**
   ```bash
   git clone https://github.com/woodyk/echoai.git
   cd echoai
   pip install -e .
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
- Chat history management
- Custom themes and UI customization
- System prompt customization
- Model selection and switching

### Productivity Features
- File content analysis and summarization
- Code review and debugging assistance
- Documentation generation
- Research assistance
- Task automation

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
