#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: interactor.py
# Author: Wadih Khairallah
# Description: Universal AI interaction class
#              with streaming, tool calling,
#              dynamic model switching, async support,
#              and comprehensive error handling
# Created: 2025-03-14 12:22:57
# Modified: 2025-04-30 20:00:51

import os
import re
import openai
import json
import subprocess
import inspect
import argparse
import tiktoken
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Callable
from rich import print
from rich.prompt import Confirm
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.syntax import Syntax
from rich.rule import Rule
from openai import OpenAIError, RateLimitError, APIConnectionError

console = Console()
log = console.log

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class Interactor:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "openai:gpt-4o-mini",
        tools: Optional[bool] = True,
        stream: bool = True,
        context_length: int = 128000,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the universal AI interaction client.

        Args:
            base_url: Optional base URL for the API. If None, uses the provider's default URL.
            api_key: Optional API key. If None, attempts to use environment variables based on provider.
            model: Model identifier in format "provider:model_name" (e.g., "openai:gpt-4o-mini").
            tools: Enable (True) or disable (False) tool calling; None for auto-detection based on model support.
            stream: Enable (True) or disable (False) streaming responses.
            context_length: Maximum number of tokens to maintain in conversation history.
            max_retries: Maximum number of retries for failed API calls.
            retry_delay: Initial delay (in seconds) for exponential backoff retries.

        Raises:
            ValueError: If provider is not supported or API key is missing for non-Ollama providers.
        """
        self.stream = stream
        self.tools = []
        self.history = []
        self.context_length = context_length
        self.encoding = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
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
            "google": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
                "api_key": api_key or os.getenv("GEMINI_API_KEY") or None
            },
        }
        """
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
        """
        self.system = self.messages_system("You are a helpful Assistant.")
        self._setup_client(model, base_url, api_key)
        self.tools_enabled = self.tools_supported if tools is None else tools and self.tools_supported
        self._setup_encoding()

    def _setup_client(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Set up or update the client and model configuration using providers dict.

        Args:
            model: Model identifier in format "provider:model_name".
            base_url: Optional base URL for the API. If None, uses the provider's default URL.
            api_key: Optional API key. If None, attempts to use environment variables based on provider.

        Raises:
            ValueError: If provider is not supported or API key is missing for non-Ollama providers.
        """
        provider, model_name = model.split(":", 1)
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers: {list(self.providers.keys())}")

        provider_config = self.providers[provider]
        effective_base_url = base_url or provider_config["base_url"]
        effective_api_key = api_key or provider_config["api_key"]

        if not effective_api_key and provider != "ollama":
            raise ValueError(f"API key not provided and not found in environment for {provider.upper()}_API_KEY")

        self.client = openai.OpenAI(base_url=effective_base_url, api_key=effective_api_key)
        self.async_client = openai.AsyncOpenAI(base_url=effective_base_url, api_key=effective_api_key)
        self.model = model_name
        self.provider = provider
        self.tools_supported = self._check_tool_support()
        if not self.tools_supported:
            logger.warning(f"Tool calling not supported for {provider}:{model_name}")

    def _check_tool_support(self) -> bool:
        """Test if the model supports tool calling.

        Performs a test call to the model with a simple tool to determine if it supports tool calling.

        Returns:
            bool: True if the model supports tool calling, False otherwise.
        """
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
        except Exception as e:
            logger.error(f"Failed to check tool support: {e}")
            return False

    def add_function(
        self,
        external_callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Register a function for tool calling.

        Args:
            external_callable: The function to register for tool calling.
            name: Optional custom name for the function. If None, uses the function's name.
            description: Optional description of the function. If None, extracts from docstring.

        Raises:
            ValueError: If external_callable is None.
        """
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

    def get_functions(self) -> List[Dict[str, Any]]:
        """Get the list of registered functions for tool calling.

        Returns:
            List[Dict[str, Any]]: List of registered functions.
        """
        return self.tools

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

        if providers is None:
            providers_to_list = self.providers
        elif isinstance(providers, str):
            providers_to_list = {providers: self.providers.get(providers)}
        elif isinstance(providers, list):
            providers_to_list = {p: self.providers.get(p) for p in providers}
        else:
            return []

        invalid_providers = [p for p in providers_to_list if p not in self.providers]
        if invalid_providers:
            logger.error(f"Invalid providers: {invalid_providers}")
            return []

        regex_pattern = None
        if filter:
            try:
                regex_pattern = re.compile(filter, re.IGNORECASE)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return []

        for provider_name, config in providers_to_list.items():
            try:
                client = openai.OpenAI(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
                response = client.models.list()
                for model_data in response:
                    model_id = f"{provider_name}:{model_data.id}"
                    if regex_pattern is None or regex_pattern.search(model_id):
                        models.append(model_id)
            except Exception as e:
                logger.error(f"Failed to list models for {provider_name}: {e}")
                pass

        return sorted(models, key=str.lower)

    async def _retry_with_backoff(self, func: Callable, *args, **kwargs):
        """Execute a function with retry logic and exponential backoff.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: If all retries fail.
        """
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (RateLimitError, APIConnectionError, aiohttp.ClientError) as e:
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries} retries failed: {e}")
                    raise
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {delay}s due to {e}")
                await asyncio.sleep(delay)
            except OpenAIError as e:
                logger.error(f"OpenAI error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

    def interact(
        self,
        user_input: Optional[str],
        quiet: bool = False,
        tools: bool = True,
        stream: bool = True,
        markdown: bool = False,
        model: Optional[str] = None,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Interact with the AI, handling streaming and multiple tool calls iteratively.

        Args:
            user_input: The user's input message to send to the AI.
            quiet: If True, suppresses console output.
            tools: Enable (True) or disable (False) tool calling for this interaction.
            stream: Enable (True) or disable (False) streaming responses for this interaction.
            markdown: If True, renders responses as markdown in the console.
            model: Optional model to use for this interaction, overriding the current model.
            output_callback: Optional callback to handle each token output (for web streaming, etc.).

        Returns:
            str: The AI's response, or None if user_input is empty.
        """
        return asyncio.run(self.interact_async(
            user_input=user_input,
            quiet=quiet,
            tools=tools,
            stream=stream,
            markdown=markdown,
            model=model,
            output_callback=output_callback
        ))

    async def interact_async(
        self,
        user_input: Optional[str],
        quiet: bool = False,
        tools: bool = True,
        stream: bool = True,
        markdown: bool = False,
        model: Optional[str] = None,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Asynchronously interact with the AI, handling streaming and tool calls.

        Args:
            user_input: The user's input message to send to the AI.
            quiet: If True, suppresses console output.
            tools: Enable (True) or disable (False) tool calling for this interaction.
            stream: Enable (True) or disable (False) streaming responses for this interaction.
            markdown: If True, renders responses as markdown in the console.
            model: Optional model to use for this interaction, overriding the current model.
            output_callback: Optional callback to handle each token output.

        Returns:
            str: The AI's response, or None if user_input is empty.
        """
        if not user_input:
            logger.warning("Empty user input provided")
            return None

        if self.encoding:
            input_tokens = len(self.encoding.encode(user_input))
            if input_tokens > self.context_length:
                logger.error(f"User input exceeds max context length: {self.context_length}")
                print(f"[red]User Input exceeds max context length:[/red] {self.context_length}")
                return None

        if model:
            provider, model_name = model.split(":", 1)
            if provider != self.provider or model_name != self.model:
                self._setup_client(model)
                self._setup_encoding()
            self.provider = provider
            self.model = model_name

        self.tools_enabled = tools and self.tools_supported
        self.history.append({"role": "user", "content": user_input})
        if self._cycle_messages():
            logger.error("Context length exceeded after cycling messages")
            return None

        use_stream = self.stream if stream is None else stream
        content = ""
        live = Live(console=console, refresh_per_second=100) if use_stream and markdown and not quiet else None

        while True:
            params = {
                "model": self.model,
                "messages": self.history,
                "stream": use_stream
            }
            if self.tools_supported and self.tools_enabled:
                params["tools"] = self.tools
                params["tool_choice"] = "auto"

            try:
                response = await self._retry_with_backoff(
                    self.async_client.chat.completions.create,
                    **params
                )
                tool_calls = []

                if use_stream:
                    if live:
                        live.start()
                    tool_calls_dict = {}
                    async for chunk in response:
                        delta = chunk.choices[0].delta
                        finish_reason = chunk.choices[0].finish_reason

                        if delta.content:
                            content += delta.content
                            if output_callback:
                                output_callback(delta.content)
                            elif live:
                                live.update(Markdown(content))
                            elif not markdown and not quiet:
                                print(delta.content, end="")

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
                        if output_callback:
                            output_callback(message.content or "No response.")
                        elif not quiet:
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
                self.history.append(assistant_msg)

                if output_callback:
                    for call in tool_calls:
                        name = call["function"]["name"] if isinstance(call, dict) else call.function.name
                        notification = json.dumps({
                            "type": "tool_call",
                            "tool_name": name,
                            "status": "started"
                        })
                        output_callback(notification)

                for call in tool_calls:
                    name = call["function"]["name"] if isinstance(call, dict) else call.function.name
                    arguments = call["function"]["arguments"] if isinstance(call, dict) else call.function.arguments
                    tool_call_id = call["id"] if isinstance(call, dict) else call.id
                    result = await self._handle_tool_call_async(
                        name, arguments, tool_call_id, params, markdown, live, output_callback=output_callback
                    )
                    self.history.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call_id
                    })

                    if output_callback:
                        notification = json.dumps({
                            "type": "tool_call",
                            "tool_name": name,
                            "status": "completed"
                        })
                        output_callback(notification)

            except Exception as e:
                error_msg = f"Error during interaction: {e}"
                logger.error(error_msg)
                if not quiet:
                    print(f"[red]{error_msg}[/red]")
                content += f"\n{error_msg}"
                break

        full_content = content
        self.history.append({"role": "assistant", "content": full_content})
        return full_content

    def _render_content(
        self, content: str,
        markdown: bool,
        live: Optional[Live]
    ):
        """Render content based on streaming and markdown settings.

        Args:
            content: The text content to render.
            markdown: If True, renders content as markdown.
            live: Optional Live context for updating content in real-time.
        """
        if markdown and live:
            live.update(Markdown(content))
        elif not markdown:
            print(content, end="")

    async def _handle_tool_call_async(
        self,
        function_name: str,
        function_arguments: str,
        tool_call_id: str,
        params: dict,
        markdown: bool,
        live: Optional[Live],
        safe: bool = False,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Process a tool call asynchronously and return the result.

        Args:
            function_name: Name of the function to call.
            function_arguments: JSON string containing the function arguments.
            tool_call_id: Unique identifier for this tool call.
            params: Parameters used for the original API call.
            markdown: If True, renders content as markdown.
            live: Optional Live context for updating content in real-time.
            safe: If True, prompts for confirmation before executing the tool call.
            output_callback: Optional callback to handle the tool call result.

        Returns:
            The result of the function call.

        Raises:
            ValueError: If the function is not found.
        """
        arguments = json.loads(function_arguments or "{}")
        func = getattr(self, function_name, None)
        if not func:
            raise ValueError(f"Function '{function_name}' not found.")

        if live:
            live.stop()

        print(f"Running {function_name}...\n")
        if output_callback:
            notification = json.dumps({
                "type": "tool_call",
                "tool_name": function_name,
                "status": "started"
            })
            output_callback(notification)

        command_result = (
            {"status": "cancelled", "message": "Tool call aborted by user"}
            if safe and not Confirm.ask(
                f"[bold yellow]Proposed tool call:[/bold yellow] {function_name}({json.dumps(arguments, indent=2)})\n[bold cyan]Execute? [y/n]: [/bold cyan]",
                default=False
            )
            else await asyncio.get_event_loop().run_in_executor(None, lambda: func(**arguments))
        )
        if safe and command_result["status"] == "cancelled":
            print("[red]Tool call cancelled by user[/red]")
        if live:
            live.start()

        if output_callback:
            notification = json.dumps({
                "type": "tool_call",
                "tool_name": function_name,
                "status": "completed"
            })
            output_callback(notification)

        return command_result

    def _setup_encoding(self):
        """Set up the token encoding based on the current model."""
        try:
            if self.provider == "openai":
                self.encoding = tiktoken.encoding_for_model(self.model)
            else:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to setup encoding: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count the number of tokens in a list of messages."""
        if not self.encoding:
            self._setup_encoding()

        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(str(value)))
                if key == "name":
                    num_tokens += -1
            num_tokens += 2
        return num_tokens

    def _cycle_messages(self):
        """Remove oldest non-system messages to stay within context length."""
        exceeded_context = False
        while self._count_tokens(self.history) > self.context_length:
            for i, msg in enumerate(self.history):
                if msg["role"] != "system":
                    self.history.pop(i)
                    break

        if len(self.history) <= 1:
            print(f"[red]Context length exceeded:[/red] {self.context_length}")
            exceeded_context = True

        return exceeded_context

    def messages_add(
        self,
        role: Optional[str] = None,
        content: Optional[str] = None
    ) -> list:
        """Manage messages in the conversation history."""
        if role is None and content is None:
            return self.history

        if content is None and role is not None:
            raise ValueError("Content must be provided when role is specified")
        if not content:
            raise ValueError("Content cannot be empty")
        if not isinstance(content, str):
            raise ValueError("Content must be a string")

        if role == "system":
            self.messages_system(content)
            return self.history

        if role is not None:
            self.history.append({"role": role, "content": content})
            return self.history

        return self.history

    def messages_system(self, prompt: str):
        """Set a new system prompt."""
        if not isinstance(prompt, str) or not prompt:
            return self.system

        filtered_messages = []
        for message in self.history:
            if message["role"] != "system":
                filtered_messages.append(message)
        self.history = filtered_messages

        system_message = {
            "role": "system",
            "content": prompt
        }

        self.history.insert(0, system_message)
        self.system = prompt

        return self.system

    def messages_get(self) -> list:
        """Retrieve the current message list."""
        return self.history

    def messages_flush(self) -> list:
        """Clear all messages while preserving the system prompt."""
        self.history = []
        self.messages_system(self.system)
        return self.history

    def messages_length(self) -> int:
        """Calculate the total token count for the message history."""
        if not self.encoding:
            return 0

        total_tokens = 0
        for message in self.history:
            if message.get("content"):
                total_tokens += len(self.encoding.encode(message["content"]))
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    if tool_call.get("function"):
                        total_tokens += len(self.encoding.encode(tool_call["function"].get("name", "")))
                        total_tokens += len(self.encoding.encode(tool_call["function"].get("arguments", "")))
        return total_tokens

def run_bash_command(command: str) -> Dict[str, Any]:
    """Run a simple bash command (e.g., 'ls -la ./' to list files) and return the output."""
    print(Syntax(f"\n{command}\n", "bash", theme="monokai"))
    if not Confirm.ask("execute? [y/n]: ", default=False):
        return {"status": "cancelled"}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        print(Rule(), result.stdout.strip(), Rule())
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
        print(f"Fetching: {url}")
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
    """Run the interactor as a standalone AI chat client."""
    parser = argparse.ArgumentParser(description='AI Chat Client')
    parser.add_argument('--model', default='openai:gpt-4o-mini',
                        help='Model identifier in format "provider:model_name"')
    parser.add_argument('--base-url', help='Base URL for API (optional)')
    parser.add_argument('--api-key', help='API key (optional)')
    parser.add_argument('--stream', action='store_true', default=True,
                        help='Enable response streaming (default: True)')
    parser.add_argument('--markdown', action='store_true', default=False,
                        help='Enable markdown rendering (default: False)')
    parser.add_argument('--tools', action='store_true', default=True,
                        help='Enable tool calling (default: True)')

    args = parser.parse_args()

    try:
        caller = Interactor(
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            tools=args.tools,
            stream=args.stream,
            context_length=500
        )

        caller.add_function(run_bash_command)
        caller.add_function(get_current_weather)
        caller.add_function(get_website_data)
        print(caller.list())

        caller.system = caller.messages_system(
            "You are a helpful assistant. Only call tools if one is applicable."
        )

        print("[bold green]Interactor Class[/bold green]")

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in {"/exit", "/quit"}:
                    break
                elif not user_input:
                    continue

                response = caller.interact(
                    user_input,
                    tools=args.tools,
                    stream=args.stream,
                    markdown=args.markdown
                )

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to initialize chat client: {e}")
        print(f"[red]Failed to initialize chat client: {str(e)}[/red]")
        return 1

    return 0

if __name__ == "__main__":
    main()
