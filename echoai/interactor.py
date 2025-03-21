#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: interactor.py
# Author: Wadih Khairallah
# Description: Universal AI interaction class with streaming and tool calling
# Created: 2025-03-14 12:22:57
# Modified: 2025-03-20 15:28:50

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
        model: str = "gpt-4o",
        tools: Optional[bool] = True,
        stream: bool = True
    ):
        """Initialize the AI interaction client."""
        base_url = base_url or "https://api.openai.com/v1"
        api_key = api_key or os.getenv("OPENAI_API_KEY") or self._raise_no_key_error()
        
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.is_ollama = "11434" in base_url
        self.tools = []
        self.stream = stream
        self.messages = [{"role": "system", "content": (
            "You are a helpful assistant. Use tools only for specific tasks matching their purpose, "
            "based on name and description. For greetings, simple replies, or vague inputs, respond directly. "
            "For multi-step requests, execute each tool call in sequence and provide a final summary."
        )}]

        self.tools_supported = self._check_tool_support()
        self.tools_enabled = self.tools_supported if tools is None else tools and self.tools_supported
        
        if not self.tools_supported and tools:
            console.print(f"Warning: Model '{model}' lacks tool support. Tools disabled.")
        elif not self.tools_supported:
            console.print(f"Note: Model '{model}' does not support tools.")

    def _raise_no_key_error(self):
        raise ValueError("OPENAI_API_KEY not set. Provide an API key for OpenAI.")

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
            return bool((message.tool_calls and len(message.tool_calls) > 0) or message.function_call)
        except Exception as e:
            #console.print(f"[yellow]Tool support check failed: {e}. Assuming no support.[/yellow]")
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
            #console.print(f"Warning: Adding '{name or external_callable.__name__}' but tools are disabled.")
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

        tool = (
            {"type": "function", "function": {"name": function_name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}}
            if self.is_ollama else
            {"name": function_name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}
        )
        self.tools.append(tool)
        setattr(self, function_name, external_callable)

    def interact(
            self,
            user_input: Optional[str],
            tools: bool = True,
            stream: bool = True,
            markdown: bool = False
        ) -> Optional[str]:
        """Interact with the AI, handling streaming and multiple tool calls iteratively if supported."""
        if not user_input:
            return None

        if tools:
            self.tools_enabled = True 
        else:
            self.tools_enabled = False

        self.messages.append({"role": "user", "content": user_input})
        use_stream = self.stream if stream is None else stream
        full_content = ""
        live = Live(console=console, refresh_per_second=100) if use_stream and markdown else None

        while True:
            params = {
                "model": self.model,
                "messages": self.messages,
                "stream": use_stream
            }
            # Only include tool-related parameters if the model supports tools
            if self.tools_supported and self.tools_enabled:
                if self.is_ollama:
                    params["tools"] = self.tools
                    params["tool_choice"] = "auto"
                else:
                    params["functions"] = self.tools

            try:
                response = self.client.chat.completions.create(**params)
                tool_calls = []

                if use_stream:
                    if live:
                        live.start()
                    current_call = {"name": "", "arguments": "", "id": None}
                    for chunk in response:
                        delta = chunk.choices[0].delta
                        finish_reason = chunk.choices[0].finish_reason

                        if delta.content:
                            full_content += delta.content
                            if live:
                                live.update(Markdown(full_content))
                            elif not markdown:
                                console.print(delta.content, end="")

                        # Process tool calls only if tools are supported
                        if self.tools_supported and self.tools_enabled:
                            if self.is_ollama and delta.tool_calls:
                                tool_call = delta.tool_calls[0]
                                name = getattr(tool_call, "name", getattr(tool_call.function, "name", None) if hasattr(tool_call, "function") else None)
                                arguments = getattr(tool_call, "arguments", getattr(tool_call.function, "arguments", None) if hasattr(tool_call, "function") else None)
                                if name and not current_call["name"]:
                                    current_call["name"] = name
                                if arguments:
                                    current_call["arguments"] += arguments
                                if hasattr(tool_call, "id") and not current_call["id"]:
                                    current_call["id"] = tool_call.id
                            elif not self.is_ollama and delta.function_call:
                                if delta.function_call.name and not current_call["name"]:
                                    current_call["name"] = delta.function_call.name
                                if delta.function_call.arguments:
                                    current_call["arguments"] += delta.function_call.arguments

                            if finish_reason in ("tool_calls", "function_call") and current_call["name"]:
                                tool_calls.append(current_call)
                                current_call = {"name": "", "arguments": "", "id": None}

                    if live:
                        live.stop()
                else:
                    message = response.choices[0].message
                    # Process tool calls only if tools are supported
                    if self.tools_supported and self.tools_enabled:
                        tool_calls = message.tool_calls if self.is_ollama and self.tools_enabled else ([message] if message.function_call else [])
                    else:
                        tool_calls = []  # No tool calls for unsupported models
                    if not tool_calls:
                        full_content += message.content or "No response."
                        self._render_content(full_content, markdown, live=None)
                        break

                if not tool_calls:
                    break  # Exit if no tool calls are detected

                for call in tool_calls:
                    name = call["name"] if isinstance(call, dict) else (call.function.name if self.is_ollama else call.function_call.name)
                    arguments = call["arguments"] if isinstance(call, dict) else (call.function.arguments if self.is_ollama else call.function_call.arguments)
                    tool_call_id = call["id"] if isinstance(call, dict) else (call.id if self.is_ollama else None)

                    result = self._handle_tool_call(name, arguments, tool_call_id, params, markdown, live)
                    if live:
                        live.start()
                        live.update(Markdown(full_content))
                        live.stop()

            except Exception as e:
                error_msg = f"Error: {e}"
                console.print(f"[red]{error_msg}[/red]")
                full_content += f"\n{error_msg}"
                break

        self.messages.append({"role": "assistant", "content": full_content})
        return full_content

    def _render_content(
            self,
            content: str,
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
        tool_call_id: Optional[str],
        params: dict,
        markdown: bool,
        live: Optional[Live],
        safe: bool = False
    ) -> str:
        """Process a tool call and update message history."""
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

        tool_call_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls" if self.is_ollama else "function_call": [{
                "id": tool_call_id,
                "type": "function",
                "function": {"name": function_name, "arguments": json.dumps(arguments)}
            }] if self.is_ollama else {"name": function_name, "arguments": json.dumps(arguments)}
        }
        self.messages.append(tool_call_msg)
        self.messages.append({
            "role": "tool" if self.is_ollama else "function",
            "content": json.dumps(command_result),
            "tool_call_id": tool_call_id if self.is_ollama else None,
            "name": function_name if not self.is_ollama else None
        })

        # Return the tool result without making an additional API call here
        return json.dumps(command_result)

def run_bash_command(command: str) -> Dict[str, Any]:
    """Execute a Bash command securely."""
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
    """Mock current temperature for a location."""
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
    caller = Interactor(model="gpt-4o")
    caller.add_function(run_bash_command)
    caller.add_function(get_current_weather)
    caller.add_function(get_website_data)
    caller.set_system(
        "You are a helpful assistant"
    )

    console.print("Welcome to the AI Interaction Chatbot! Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in {"exit", "quit"}:
            console.print("Goodbye!")
            break
        caller.interact(user_input, stream=True, markdown=False)

if __name__ == "__main__":
    main()
