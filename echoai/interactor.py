#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: interactor.py
# Author: Wadih Khairallah
# Description: Universal AI interaction class with streaming, tool calling, and dynamic model switching
# Created: 2025-03-14 12:22:57
# Modified: 2025-03-26 17:13:07

import openai
import json
import subprocess
import inspect
import os
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
        """
        self.messages = [{"role": "system", "content": (
            "You are a helpful assistant. Use tools only for specific tasks matching their purpose. "
            "For 'run_bash_command', execute simple bash commands like 'ls -la' or 'dir' to list files. "
            "For greetings or vague inputs, respond directly without tools."
        )}]
        """
        self._setup_client(model, base_url, api_key)
        self.tools_enabled = self.tools_supported if tools is None else tools and self.tools_supported

    def _setup_client(
            self,
            model: Optional[str] = None,
            base_url: Optional[str] = None,
            api_key: Optional[str] = None
        ):
        """Set up or update the client and model configuration."""
        provider, model_name = model.split(":", 1)
        if provider == "ollama":
            base_url = base_url or "http://localhost:11434/v1"
            api_key = api_key or "ollama"
        elif provider == "openai":
            base_url = base_url or "https://api.openai.com/v1"
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set. Provide an API key for OpenAI.")

        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model_name
        self.tools_supported = self._check_tool_support()
        if not self.tools_supported:
            pass
            #console.print(f"Note: Model '{model}' does not support tools.")

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
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("System prompt must be a non-empty string.")
        self.messages = [msg for msg in self.messages if msg["role"] != "system"] + [{"role": "system", "content": prompt}]

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

    def list(self):
        """Check providers for available models."""
        models = []
        # Gather OpenAI available models
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.models.list()
            print(response)
            for model_data in response:
                models.append("openai:" + model_data.id)
        except Exception as e:
            pass

        # Gather Ollama available models
        try:
            client = openai.OpenAI(
                    api_key="ollama",
                    base_url="http://localhost:11434/v1"
                )
            response = client.models.list()
            for model_data in response:
                models.append("ollama:" + model_data.id)
        except Exception as e:
            pass

        return models

    def interact(
        self,
        user_input: Optional[str],
        quiet: bool = False,  # If True, only return result, don't print it
        history: bool = True,  # If False, clear message history except system prompt
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
            if model_name != self.model: 
                self._setup_client(model)

        self.tools_enabled = tools and self.tools_supported

        # Clear history if history=False, keeping only system message
        if not history:
            self.messages = [msg for msg in self.messages if msg["role"] == "system"]
        
        self.messages.append({"role": "user", "content": user_input})
        use_stream = self.stream if stream is None else stream
        full_content = ""
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
                            full_content += delta.content
                            if live:
                                live.update(Markdown(full_content))
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
                    if tool_calls:
                        pass  # Optionally print tool calls for debugging: console.print(f"[TOOL_CALLS] {json.dumps(tool_calls)}")
                else:
                    message = response.choices[0].message
                    tool_calls = message.tool_calls or []
                    if not tool_calls:
                        full_content += message.content or "No response."
                        if not quiet:
                            self._render_content(full_content, markdown, live=None)
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
                    # Optionally append tool result to output if not quiet
                    if not quiet:
                        full_content += f"\nTool result ({name}): {json.dumps(result)}"

            except Exception as e:
                error_msg = f"Error: {e}"
                if not quiet:
                    console.print(f"[red]{error_msg}[/red]")
                full_content += f"\n{error_msg}"
                break

        # Only append final assistant message if history is enabled
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
    #models = caller.list()
    #caller = Interactor(model="ollama:mistral-nemo")
    caller.add_function(run_bash_command)
    caller.add_function(get_current_weather)
    caller.add_function(get_website_data)
    caller.set_system("You are a helpful assistant. Only call tools if one is applicable.")

    console.print("Welcome to the AI Interaction Chatbot! Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in {"exit", "quit"}:
            console.print("Goodbye!")
            break
        caller.interact(user_input, tools=True, stream=True, markdown=True, quiet=False)

if __name__ == "__main__":
    main()
