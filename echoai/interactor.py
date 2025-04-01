#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: interactor.py
# Author: Wadih Khairallah
# Description: Universal AI interaction class with streaming, tool calling, and dynamic model switching
# Created: 2025-03-14 12:22:57
# Modified: 2025-04-01 19:24:22

import os
import re
import openai
import json
import subprocess
import inspect
from rich.prompt import Confirm
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.syntax import Syntax
from rich.rule import Rule
from typing import Dict, Any, Optional

console = Console()

class Interactor:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "openai:gpt-4o-mini",
        tools: Optional[bool] = True,
        stream: bool = True
    ):
        """Initialize the AI interaction client."""
        self.stream = stream
        self.tools = []
        self.messages = []
        self.providers = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": api_key or os.getenv("OPENAI_API_KEY") or None
            },
            "ollama": {
                "base_url": "http://localhost:11434/v1",
                "api_key": api_key or "ollama"
            },
            "nvidia": {
                "base_url": "https://integrate.api.nvidia.com/v1",
                "api_key": api_key or os.getenv("NVIDIA_API_KEY") or None
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com/v1",
                "api_key": api_key or os.getenv("ANTHROPIC_API_KEY") or None
            },
            "mistral": {
                "base_url": "https://api.mistral.ai/v1",
                "api_key": api_key or os.getenv("MISTRAL_API_KEY") or None
            },
            "deepseek": {
                "base_url": "https://api.deepseek.com",
                "api_key": api_key or os.getenv("DEEPSEEK_API_KEY") or None
            },
            "grok": {
                "base_url": "https://api.x.ai/v1",
                "api_key": api_key or os.getenv("GROK_API_KEY") or None
            }
        }
        self._setup_client(model, base_url, api_key)
        self.tools_enabled = self.tools_supported if tools is None else tools and self.tools_supported

    def _setup_client(
            self,
            model: Optional[str] = None,
            base_url: Optional[str] = None,
            api_key: Optional[str] = None
        ):
        """Set up or update the client and model configuration using providers dict."""
        provider, model_name = model.split(":", 1)
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers: {list(self.providers.keys())}")
        
        provider_config = self.providers[provider]
        effective_base_url = base_url or provider_config["base_url"]
        effective_api_key = api_key or provider_config["api_key"]
        
        if not effective_api_key and provider != "ollama":  # Ollama doesn't require a real API key
            raise ValueError(f"API key not provided and not found in environment for {provider.upper()}_API_KEY")

        self.client = openai.OpenAI(base_url=effective_base_url, api_key=effective_api_key)
        self.model = model_name
        self.provider = provider
        self.tools_supported = self._check_tool_support()
        if not self.tools_supported:
            pass

    def _check_tool_support(self) -> bool:
        """Test if the model supports tool calling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Use a tool for NY weather."}],
                stream=False,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "test_function",
                        "description": "Test tool support",
                        "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
                    }
                }],
                tool_choice="auto"
            )
            message = response.choices[0].message
            return bool(message.tool_calls and len(message.tool_calls) > 0)
        except Exception:
            return False

    def set_system(self, prompt: str):
        """Set a new system prompt."""
        # Check if the prompt is valid: must be a non-empty string
        if not isinstance(prompt, str):
            raise ValueError("System prompt must be a non-empty string.")
        if not prompt:
            raise ValueError("System prompt must be a non-empty string.")

        # Create a new list to store messages
        new_messages = []

        # Go through each message in the current messages list
        for message in self.messages:
            # Only keep messages that are not system messages
            if message["role"] != "system":
                new_messages.append(message)

        # Add the new system prompt as a message
        system_message = {
            "role": "system",
            "content": prompt
        }
        new_messages.append(system_message)

        # Update the messages list with our new filtered list plus the system prompt
        self.messages = new_messages

    def add_function(
        self,
        external_callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Register a function for tool calling."""
        if not self.tools_enabled:
            return
        if not external_callable:
            raise ValueError("An external callable is required.")

        function_name = name or external_callable.__name__
        description = description or (inspect.getdoc(external_callable) or "No description provided.").split("\n")[0]
        
        signature = inspect.signature(external_callable)
        properties = {
            name: {
                "type": (
                    "number" if param.annotation in (float, int) else
                    "string" if param.annotation in (str, inspect.Parameter.empty) else
                    "boolean" if param.annotation == bool else
                    "array" if param.annotation == list else
                    "object"
                ),
                "description": f"{name} parameter"
            } for name, param in signature.parameters.items()
        }
        required = [name for name, param in signature.parameters.items() if param.default == inspect.Parameter.empty]

        tool = {
            "type": "function",
            "function": {
                "name": function_name,
                "description": description,
                "parameters": {"type": "object", "properties": properties, "required": required}
            }
        }
        self.tools.append(tool)
        setattr(self, function_name, external_callable)



    def list(
        self,
        providers: Optional[str | list[str]] = None,
        filter: Optional[str] = None
    ) -> list:
        """Check providers for available models.

        Args:
            providers: If specified, list only models from these providers. Can be a single provider string
                      or a list of provider strings. If None, lists all providers.
            filter: If specified, only include models whose names match this regex pattern (case-insensitive).

        Returns:
            List of model names matching the criteria.
        """
        models = []

        # Normalize providers input to a list
        if providers is None:
            providers_to_list = self.providers
        elif isinstance(providers, str):
            providers_to_list = {providers: self.providers.get(providers)}
        elif isinstance(providers, list):
            providers_to_list = {p: self.providers.get(p) for p in providers}
        else:
            #console.print(f"[red]Error: 'providers' must be a string, list of strings, or None, got {type(providers)}[/red]")
            return []

        # Validate providers
        invalid_providers = [p for p in providers_to_list if p not in self.providers]
        if invalid_providers:
            #console.print(f"[red]Error: Invalid providers {invalid_providers}. Available providers: {list(self.providers.keys())}[/red]")
            return []

        # Compile regex pattern if filter is provided
        regex_pattern = None
        if filter:
            try:
                regex_pattern = re.compile(filter, re.IGNORECASE)
            except re.error as e:
                #console.print(f"[red]Error: Invalid regex pattern '{filter}': {str(e)}[/red]")
                return []

        # Fetch and filter models
        for provider_name, config in providers_to_list.items():
            try:
                client = openai.OpenAI(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
                response = client.models.list()
                for model_data in response:
                    model_id = f"{provider_name}:{model_data.id}"
                    # Apply regex filter if provided, otherwise include all
                    if regex_pattern is None or regex_pattern.search(model_id):
                        models.append(model_id)
            except Exception as e:
                #console.print(f"[yellow]Warning: Could not fetch models for {provider_name}: {str(e)}[/yellow]")
                pass

        return models


    def interact(
        self,
        user_input: Optional[str],
        quiet: bool = False,
        history: bool = True,
        tools: bool = True,
        stream: bool = True,
        markdown: bool = False,
        model: Optional[str] = None
    ) -> Optional[str]:
        """Interact with the AI, handling streaming and multiple tool calls iteratively."""
        if not user_input:
            return None

        # Switch model if provided
        if model:
            provider, model_name = model.split(":", 1)
            if provider != self.provider or model_name != self.model:
                self._setup_client(model)

        tool_results = ""
        self.tools_enabled = tools and self.tools_supported

        if not history:
            self.messages = [msg for msg in self.messages if msg["role"] == "system"]
        
        self.messages.append({"role": "user", "content": user_input})
        use_stream = self.stream if stream is None else stream
        content = ""
        live = Live(console=console, refresh_per_second=100) if use_stream and markdown and not quiet else None

        while True:
            params = {
                "model": self.model,
                "messages": self.messages,
                "stream": use_stream
            }
            if self.tools_supported and self.tools_enabled:
                params["tools"] = self.tools
                params["tool_choice"] = "auto"

            try:
                response = self.client.chat.completions.create(**params)
                tool_calls = []

                if use_stream:
                    if live:
                        live.start()
                    tool_calls_dict = {}
                    for chunk in response:
                        delta = chunk.choices[0].delta
                        finish_reason = chunk.choices[0].finish_reason

                        if delta.content:
                            content += delta.content
                            if live:
                                live.update(Markdown(content))
                            elif not markdown and not quiet:
                                console.print(delta.content, end="")

                        if delta.tool_calls:
                            for tool_call_delta in delta.tool_calls:
                                index = tool_call_delta.index
                                if index not in tool_calls_dict:
                                    tool_calls_dict[index] = {"id": None, "function": {"name": "", "arguments": ""}}
                                if tool_call_delta.id:
                                    tool_calls_dict[index]["id"] = tool_call_delta.id
                                if tool_call_delta.function.name:
                                    tool_calls_dict[index]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    tool_calls_dict[index]["function"]["arguments"] += tool_call_delta.function.arguments

                    tool_calls = list(tool_calls_dict.values())
                    if live:
                        live.stop()
                else:
                    message = response.choices[0].message
                    tool_calls = message.tool_calls or []
                    if not tool_calls:
                        content += message.content or "No response."
                        if not quiet:
                            self._render_content(content, markdown, live=None)
                        break

                if not tool_calls:
                    break

                assistant_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call["id"] if isinstance(call, dict) else call.id,
                        "type": "function",
                        "function": {
                            "name": call["function"]["name"] if isinstance(call, dict) else call.function.name,
                            "arguments": call["function"]["arguments"] if isinstance(call, dict) else call.function.arguments
                        }
                    } for call in tool_calls]
                }
                self.messages.append(assistant_msg)

                for call in tool_calls:
                    name = call["function"]["name"] if isinstance(call, dict) else call.function.name
                    arguments = call["function"]["arguments"] if isinstance(call, dict) else call.function.arguments
                    tool_call_id = call["id"] if isinstance(call, dict) else call.id
                    result = self._handle_tool_call(name, arguments, tool_call_id, params, markdown, live)
                    self.messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call_id
                    })

            except Exception as e:
                error_msg = f"Error: {e}"
                if not quiet:
                    console.print(f"[red]{error_msg}[/red]")
                content += f"\n{error_msg}"
                break

        full_content = f"{tool_results}\n{content}"

        if history:
            self.messages.append({"role": "assistant", "content": full_content})

        return full_content

    def _render_content(
            self, content: str,
            markdown: bool,
            live: Optional[Live]
        ):
        """Render content based on streaming and markdown settings."""
        if markdown and live:
            live.update(Markdown(content))
        elif not markdown:
            console.print(content, end="")

    def _handle_tool_call(
        self,
        function_name: str,
        function_arguments: str,
        tool_call_id: str,
        params: dict,
        markdown: bool,
        live: Optional[Live],
        safe: bool = False
    ) -> str:
        """Process a tool call and return the result."""
        arguments = json.loads(function_arguments or "{}")
        func = getattr(self, function_name, None)
        if not func:
            raise ValueError(f"Function '{function_name}' not found.")

        if live:
            live.stop()

        command_result = (
            {"status": "cancelled", "message": "Tool call aborted by user"}
            if safe and not Confirm.ask(
                f"[bold yellow]Proposed tool call:[/bold yellow] {function_name}({json.dumps(arguments, indent=2)})\n[bold cyan]Execute? [y/n]: [/bold cyan]",
                default=False
            )
            else func(**arguments)
        )
        if safe and command_result["status"] == "cancelled":
            console.print("[red]Tool call cancelled by user[/red]")
        if live:
            live.start()

        return command_result

# Rest of the functions (run_bash_command, get_current_weather, get_website_data, main) remain unchanged
def run_bash_command(command: str) -> Dict[str, Any]:
    """Run a simple bash command (e.g., 'ls -la ./' to list files) and return the output."""
    console.print(Syntax(f"\n{command}\n", "bash", theme="monokai"))
    if not Confirm.ask("execute? [y/n]: ", default=False):
        return {"status": "cancelled"}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        console.print(Rule(), result.stdout.strip(), Rule())
        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": result.stderr.strip() or None,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Command timed out."}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_current_weather(location: str, unit: str = "Celsius") -> Dict[str, Any]:
    """Get the weather from a specified location."""
    return {"location": location, "unit": unit, "temperature": 72}

def get_website_data(url: str) -> Dict[str, Any]:
    """Extract text from a webpage."""
    import requests
    from bs4 import BeautifulSoup

    try:
        console.print(f"Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for elem in soup(['script', 'style']):
            elem.decompose()
        return {"status": "success", "text": " ".join(soup.get_text().split()), "url": url}
    except requests.RequestException as e:
        return {"status": "error", "error": f"Failed to fetch: {e}", "url": url}
    except Exception as e:
        return {"status": "error", "error": f"Processing error: {e}", "url": url}

def main():
    caller = Interactor(model="openai:gpt-4o-mini")
    caller.add_function(run_bash_command)
    caller.add_function(get_current_weather)
    caller.add_function(get_website_data)
    caller.set_system("You are a helpful assistant. Only call tools if one is applicable.")

    console.print("Welcome to the AI Interaction Chatbot! Type 'exit' to quit.")
    #models = caller.list(["openai","nvidia"], filter="gpt|llama")
    #models = caller.list()
    #console.print(models)
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in {"exit", "quit"}:
            console.print("Goodbye!")
            break
        response = caller.interact(user_input, tools=True, stream=True, markdown=True, quiet=False)

if __name__ == "__main__":
    main()
