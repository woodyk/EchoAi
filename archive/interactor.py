#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: interactor.py
# Author: Wadih Khairallah
# Description: Universal AI interaction class with streaming, tool calling, and system prompt override
# Created: 2025-03-14 12:22:57
# Modified: 2025-03-15 15:03:03

import openai
import json
import subprocess
import inspect
import os
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from typing import Dict, Any, Optional, Union

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
        """
        Initialize the universal AI interaction client.

        Args:
            base_url: API base URL (None defaults to OpenAI)
            api_key: API key (None uses env var for OpenAI or "ollama" for Ollama)
            model: Model name (default "gpt-4o")
            tools: Enable (True) or disable (False) tool calling; None for auto-detection
            stream: Enable (True) or disable (False) streaming responses
        """
        if base_url is None and api_key is None:
            base_url = "https://api.openai.com/v1"
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set. Please provide an API key for OpenAI.")

        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.is_ollama = base_url and "11434" in base_url
        self.tools = []
        self.stream = stream
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "If tools are enabled, use them only when the user requests a specific task that matches a tool's purpose, "
                    "based on the tool's name and description. "
                    "For greetings (e.g., 'hello'), simple replies (e.g., 'thank you'), or vague inputs without clear tasks, "
                    "respond directly with text without using tools."
                )
            }
        ]

        print(f"Initializing for {'Ollama' if self.is_ollama else 'OpenAI'} with model: {model}")
        
        # Check if the model supports tool calling
        self.tools_supported = self._check_tool_support()
        if not self.tools_supported:
            print(f"Note: Model '{model}' does not support tool calling.")

        # Determine if tools should be enabled
        if tools is None:
            self.tools_enabled = self.tools_supported
        else:
            self.tools_enabled = tools
            if tools and not self.tools_supported:
                print(f"Warning: Model '{model}' does not support tool calling. Disabling tools for this session.")
                self.tools_enabled = False
        
        print(f"Tool calling: {'Enabled' if self.tools_enabled else 'Disabled'}")
        print(f"Streaming: {'Enabled' if self.stream else 'Disabled'}")
        print("Initialization complete.")

    def _check_tool_support(self) -> bool:
        """Check if the model supports tool calling by attempting a test call."""
        try:
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Please use a tool to tell me the weather in New York."}],
                "stream": False,
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "test_function",
                        "description": "A test function to check tool support",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "The location to test"}
                            },
                            "required": ["location"]
                        }
                    }
                }],
                "tool_choice": "auto"
            }

            response = self.client.chat.completions.create(**params)
            message = response.choices[0].message

            # Check for tool/function call support (works for both Ollama and OpenAI)
            has_tool_support = (
                (hasattr(message, "tool_calls") and message.tool_calls is not None and len(message.tool_calls) > 0) or
                (hasattr(message, "function_call") and message.function_call is not None)
            )

            if has_tool_support:
                print(f"Debug: Model '{self.model}' supports tool calling. Response: {message}")
            else:
                print(f"Debug: Model '{self.model}' does not support tool calling. Response: {message}")

            return has_tool_support

        except Exception as e:
            error_str = str(e).lower()
            if "tool" in error_str or "function" in error_str or "not supported" in error_str:
                print(f"Debug: Model '{self.model}' does not support tool calling due to error: {e}")
                return False
            print(f"Error during tool support check: {e}. Assuming no tool support due to unexpected error.")
            return False

    def set_system(self, prompt: str):
        """Overwrite the system prompt with a new one."""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("System prompt must be a non-empty string.")
        
        self.messages = [msg for msg in self.messages if msg["role"] != "system"]
        self.messages.insert(0, {"role": "system", "content": prompt})
        print(f"System prompt updated to: '{prompt}'")

    def add_function(self, external_callable=None, name=None, description=None):
        """Add a function schema to enable function calling if tools are enabled."""
        if not self.tools_enabled:
            print(f"Warning: Adding function '{name or external_callable.__name__}' but tool calling is disabled.")
            return

        if external_callable is None:
            raise ValueError("You must provide an external_callable to add a function.")

        function_name = name or external_callable.__name__
        docstring = inspect.getdoc(external_callable) or ""
        function_description = description or docstring.split("\n")[0] if docstring else "No description provided."

        signature = inspect.signature(external_callable)
        properties = {}
        required_params = []

        for param_name, param in signature.parameters.items():
            param_type = (
                "number" if param.annotation in [float, int] else
                "string" if param.annotation == str else
                "boolean" if param.annotation == bool else
                "array" if param.annotation == list else
                "object"
            )
            if param.annotation == inspect.Parameter.empty:
                param_type = "string"
            properties[param_name] = {"type": param_type, "description": f"{param_name} parameter"}
            if param.default == inspect.Parameter.empty:
                required_params.append(param_name)

        function_definition = {
            "name": function_name,
            "description": function_description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_params,
                "additionalProperties": False,
            }
        }

        tool_definition = (
            {"type": "function", "function": function_definition} if self.is_ollama
            else function_definition
        )

        self.tools.append(tool_definition)
        setattr(self, function_name, external_callable)
        print(f"Added function: {function_name}")

    def interact(
        self,
        user_input: str = None,
        stream: bool = True,
        markdown: bool = False
    ) -> str:
        """
        Interact with the AI, supporting streaming and optional function calling.

        Args:
            user_input: User message to process
            stream: Enable/disable streaming (None uses class default)
            markdown: Bool to enable markdown output

        Returns:
            Final response content
        """

        if user_input == "" or None:
            return None

        self.messages.append({"role": "user", "content": user_input})

        use_stream = self.stream if stream is None else stream

        try:
            params = {
                "model": self.model,
                "messages": self.messages,
                "stream": use_stream
            }
            if self.tools_enabled:
                if self.is_ollama:
                    params["tools"] = self.tools
                    params["tool_choice"] = "auto"
                else:
                    params["functions"] = self.tools

            if use_stream:
                # Streaming response
                full_content = ""
                tool_calls = []
                function_name = ""
                function_arguments = ""
                tool_call_id = None
                is_collecting_tool_args = False

                if markdown:
                    live = Live(console=console, refresh_per_second=10)
                    live.start()

                response = self.client.chat.completions.create(**params)
                for chunk in response:
                    delta = chunk.choices[0].delta
                    finish_reason = chunk.choices[0].finish_reason

                    if hasattr(delta, 'content') and delta.content is not None:
                        full_content += delta.content
                        if markdown:
                            live.update(Markdown(full_content))
                        else:
                            print(delta.content, end="", flush=True)

                    if self.tools_enabled:
                        if self.is_ollama:
                            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                                tool_call = delta.tool_calls[0]
                                if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                    function_name = tool_call.function.name
                                if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                    function_arguments += tool_call.function.arguments
                                if hasattr(tool_call, 'id') and tool_call.id:
                                    tool_call_id = tool_call.id
                                is_collecting_tool_args = True
                        else:
                            if hasattr(delta, 'function_call') and delta.function_call:
                                function_call = delta.function_call
                                if hasattr(function_call, 'name') and function_call.name:
                                    function_name = function_call.name
                                if hasattr(function_call, 'arguments') and function_call.arguments:
                                    function_arguments += function_call.arguments
                                is_collecting_tool_args = True

                    if finish_reason in ["tool_calls", "function_call"] and is_collecting_tool_args:
                        arguments = json.loads(function_arguments) if function_arguments.strip() else {}
                        func = getattr(self, function_name, None)
                        if not func:
                            raise ValueError(f"Function '{function_name}' not found.")
                        command_result = func(**arguments)
                        #print(f"\nTool result: {json.dumps(command_result, indent=2)}")

                        tool_call_msg = {"role": "assistant", "content": None}
                        if self.is_ollama:
                            tool_call_msg["tool_calls"] = [{
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": json.dumps(arguments)
                                }
                            }]
                        else:
                            tool_call_msg["function_call"] = {
                                "name": function_name,
                                "arguments": json.dumps(arguments)
                            }
                        self.messages.append(tool_call_msg)

                        self.messages.append({
                            "role": "tool" if self.is_ollama else "function",
                            "content": json.dumps(command_result),
                            "tool_call_id": tool_call_id if self.is_ollama else None,
                            "name": function_name if not self.is_ollama else None
                        })

                        # Stream the second response
                        params["messages"] = self.messages
                        second_response = self.client.chat.completions.create(**params)
                        for second_chunk in second_response:
                            second_delta = second_chunk.choices[0].delta
                            if hasattr(second_delta, 'content') and second_delta.content is not None:
                                full_content += second_delta.content

                                if markdown:
                                    live.update(Markdown(full_content))
                                else:
                                    print(second_delta.content, end="", flush=True)
                        break

                self.messages.append({"role": "assistant", "content": full_content})

                try:
                    if live.is_started:
                        live.stop()
                except Exception as e:
                    print(e)

                return full_content

            else:
                # Non-streaming response
                response = self.client.chat.completions.create(**params)
                message = response.choices[0].message
                tool_calls = (
                    message.tool_calls if self.is_ollama and self.tools_enabled
                    else (message.function_call and [message]) if self.tools_enabled else None
                )
                print(f"Model decision: {'Tool call' if tool_calls else 'Direct response'}")
                if tool_calls:
                    print(f"Initial response: Tool call initiated")
                else:
                    print(f"Initial response: {message.content or 'No content'}")

                if tool_calls:
                    tool_call = tool_calls[0]
                    function_name = tool_call.function.name if self.is_ollama else tool_call.function_call.name
                    arguments = json.loads(
                        tool_call.function.arguments if self.is_ollama else tool_call.function_call.arguments
                    )

                    func = getattr(self, function_name, None)
                    if not func:
                        raise ValueError(f"Function '{function_name}' not found.")
                    command_result = func(**arguments)
                    print(f"Tool result: {json.dumps(command_result, indent=2)}")

                    tool_call_msg = {"role": "assistant", "content": None}
                    if self.is_ollama:
                        tool_call_msg["tool_calls"] = [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": json.dumps(arguments)
                            }
                        }]
                    else:
                        tool_call_msg["function_call"] = {
                            "name": function_name,
                            "arguments": json.dumps(arguments)
                        }
                    self.messages.append(tool_call_msg)

                    self.messages.append({
                        "role": "tool" if self.is_ollama else "function",
                        "content": json.dumps(command_result),
                        "tool_call_id": tool_call.id if self.is_ollama else None,
                        "name": function_name if not self.is_ollama else None
                    })

                    params["messages"] = self.messages
                    second_response = self.client.chat.completions.create(**params)
                    final_content = second_response.choices[0].message.content or "No further response."
                else:
                    final_content = message.content or "No response generated."

                self.messages.append({"role": "assistant", "content": final_content})

                if markdown:
                    console.print(Markdown(final_content))
                else:
                    print(f"{final_content}")

                return final_content

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

def run_bash_command(command: str) -> Dict[str, Any]:
    """Execute a Bash one-liner command securely and return its output."""
    console.print(Markdown(f"```\n{command}\n```\n"))
    answer = Confirm.ask("execute? [y/n]: ")
    if answer:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            console.print(Markdown(f"```\n{result.stdout.strip()}\n```\n"))

            return {
                "status": "success",
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.stderr else None,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timed out."}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        console.print("Execution cancelled")

def get_current_weather(location: str, unit: str = "Celsius") -> Dict[str, Any]:
    """Get the current temperature for a specific location (mock implementation)."""
    return {"location": location, "unit": unit, "temperature": 72}

def main():
    caller = Interactor(model="gpt-4.5-preview")
    # Examples:
    # caller = Interactor(tools=False, stream=False)  # Disable tools and streaming
    #caller = Interactor(base_url="http://localhost:11434/v1", api_key="ollama", model="phi3.5", stream=True)
    #caller = Interactor(base_url="http://localhost:11434/v1", api_key="ollama", model="mistral-nemo")

    caller.add_function(run_bash_command)
    caller.add_function(get_current_weather)

    caller.set_system("You are a helpful assistant")

    print("Welcome to the AI Interaction Chatbot!")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        response = caller.interact(user_input, stream=True, markdown=True)

if __name__ == "__main__":
    main()
