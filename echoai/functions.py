#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: main.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-08 15:53:15
# Modified: 2025-03-18 17:56:36

import os
import re
import subprocess
import io
import contextlib
import time
import requests
import pytz
import urllib.parse as urlparse
import psutil
import platform
import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.prompt import Confirm
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, Union

console = Console()

# Persistent namespace for the Python environment
persistent_python_env = {}
def run_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code in a persistent environment and return its output.

    Args:
        code (str): A string containing Python code to execute.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): 'success', 'error', or 'cancelled'
            - output (str, optional): The captured stdout if execution succeeded or partially executed
            - error (str, optional): The captured stderr or exception message if execution failed
            - message (str, optional): A message if execution was cancelled
            - namespace (dict, optional): Current state of the persistent environment (non-builtin variables)

    Notes:
        - Executes code in a persistent namespace, preserving variables across calls.
        - Prompts the user for confirmation before execution.
        - Captures and displays both stdout and stderr using the rich console.
        - Returns early with a 'cancelled' status if the user declines execution.
    """

    console.print(Syntax(f"\n{code.strip()}\n", "python", theme="monokai"))

    # Ask for user confirmation
    answer = Confirm.ask("execute? [y/n]:", default=False)
    if not answer:
        console.print("[red]Execution cancelled[/red]")
        return {"status": "cancelled", "message": "Execution aborted by user. Continue forward."}

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    console.print(Rule())
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute the code in the persistent namespace
            exec(code, persistent_python_env)
        
        stdout_output = stdout_capture.getvalue().strip()
        stderr_output = stderr_capture.getvalue().strip()

        # Display output if any
        if stdout_output:
            console.print(stdout_output)
        if stderr_output:
            console.print(f"[red]Error output:[/red] {stderr_output}")

        console.print(Rule())

        return {
            "status": "success",
            "output": stdout_output,
            "error": stderr_output if stderr_output else None,
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }

    except Exception as e:
        stderr_output = stderr_capture.getvalue().strip() or str(e)
        console.print(f"[red]Execution failed:[/red] {stderr_output}")
        console.print(Rule())

        return {
            "status": "error",
            "error": stderr_output,
            "output": stdout_capture.getvalue().strip() if stdout_capture.getvalue() else None,
            "namespace": {k: str(v) for k, v in persistent_python_env.items() if not k.startswith('__')}
        }

def run_bash_command(command: str) -> Dict[str, Any]:
    """
    Execute a Bash one-liner command securely and return its output.

    Args:
        command (str): The Bash command to execute.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): 'success' or 'error'
            - output (str, optional): The command's standard output if successful
            - error (str, optional): Error message or stderr if execution failed
            - return_code (int, optional): The command's return code if successful

    Notes:
        - Prompts the user for confirmation before execution.
        - Displays the command and its output using the rich console.
        - Cancels execution if the user declines confirmation.
    """

    console.print(Syntax(f"\n{command.strip()}\n", "bash", theme="monokai"))

    # Ask for user confirmation
    answer = Confirm.ask("execute? [y/n]:", default=False)
    if not answer:
        console.print("[red]Execution cancelled[/red]")
        return {"status": "cancelled", "message": "Execution aborted by user. Continue forward."}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        console.print(Rule())
        console.print(result.stdout.strip())
        console.print(Rule())

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

def get_website_data(url: str) -> Dict[str, Any]:
    """
    Extract all viewable text from a webpage given a URL and format it for LLM use.

    Args:
        url (str): The URL of the webpage to extract text from.

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): The extracted and cleaned text if successful
            - url (str): The original URL
            - error (str, optional): Error message if the operation failed

    Raises:
        None: Errors are caught and returned in the response dictionary.

    Examples:
        {'status': 'success', 'text': 'Example text...', 'url': 'https://example.com'}
    """

    
    try:
        # Fetch webpage content
        console.print(f"Fetching:\n[bright_cyan]{url}[/bright_cyan]\n")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        # Extract all text and clean it
        text = soup.get_text()
        
        # Remove excessive whitespace and normalize
        cleaned_text = " ".join(text.split())

        #console.print(Syntax(f"\n{cleaned_text}\n", "python", theme="monokai"))

        return {
            "status": "success",
            "text": cleaned_text,
            "url": url
        }
        
    except requests.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to fetch webpage: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error processing webpage: {str(e)}",
            "url": url
        }

def duckduckgo_search(
        query: str,
        num_results: int = 10,
        sleep_time: float = 1
    ) -> Dict[str, Any]:
    """
    Perform a DuckDuckGo search and extract cleaned text from the top results.

    Args:
        query (str): The search query to send to DuckDuckGo.
        num_results (int): The number of top results to retrieve (default: 5).
        sleep_time (float): Time to wait between requests to avoid overloading servers (default: 1 second).

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): Cleaned text from the top search results if successful
            - error (str, optional): Error message if the operation failed
            - urls (list, optional): List of URLs from which text was extracted (if successful)

    Examples:
        {'status': 'success', 'text': 'Result 1 text Result 2 text...', 'urls': ['url1', 'url2'], 'error': None}
    """

    def clean_text(text):
        """Clean text by removing extra whitespace."""
        return re.sub(r'\s+', ' ', text).strip()

    def extract_text_from_url(url):
        """Extract and clean text from a given URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                    element.decompose()
                raw_text = soup.get_text()
                return clean_text(raw_text)
            return f"Failed to retrieve content from {url}"
        except requests.RequestException as e:
            return f"Error accessing {url}: {str(e)}"

    def search_duckduckgo(query, max_results):
        """Search DuckDuckGo and return top result URLs."""
        search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for result in soup.find_all('a', class_='result__a', limit=max_results):
            href = result.get('href')
            parsed_url = urlparse.urlparse(href)
            query_params = urlparse.parse_qs(parsed_url.query)
            if 'uddg' in query_params:
                links.append(query_params['uddg'][0])
        return links

    try:
        console.print(f"[bright_cyan]Searching DuckDuckGo for: {query}[/bright_cyan]")
        search_results = search_duckduckgo(query, num_results)
        if not search_results:
            return {"status": "error", "error": f"No results found for query: {query}"}

        extracted_texts = []
        urls = []

        for url in search_results:
            console.print(f"[bright_cyan]Extracting from: {url}[/bright_cyan]")
            text = extract_text_from_url(url)
            extracted_texts.append(text)
            urls.append(url)
            time.sleep(sleep_time)  # Avoid overloading servers

        cleaned_text = " ".join(extracted_texts)
        #console.print(Syntax(f"\n{cleaned_text}\n", "python", theme="monokai"))

        return {
            "status": "success",
            "text": cleaned_text,
            "urls": urls,
            "error": None
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to process DuckDuckGo search: {str(e)}",
            "query": query
        }

def google_search(
        query: str,
        num_results: int = 5,
        sleep_time: float = 1
    ) -> Dict[str, Any]:
    """
    Perform a Google search using the Custom Search JSON API, extract text from result pages, and return cleaned results.

    Args:
        query (str): The search query to send to Google.
        num_results (int): The number of top results to retrieve and extract (default: 5).
        sleep_time (float): Time to wait between requests to avoid overloading servers (default: 1).

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): The cleaned extracted text from search result pages if successful
            - error (str, optional): Error message if the operation failed

    Raises:
        None: Errors are caught and returned in the response dictionary.

    Examples:
        {'status': 'success', 'text': 'Extracted text from page 1 Extracted text from page 2...', 'error': None}
    """

    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_API_CX")

    if not api_key:
        return {"status": "error", "error": "Google API key not set in environment variable GOOGLE_API_KEY"}
    if not cse_id:
        return {"status": "error", "error": "Google CSE ID not set in environment variable GOOGLE_API_CX"}

    def clean_text(text):
        """Clean text by removing extra whitespace."""
        return re.sub(r'\s+', ' ', text).strip()

    def extract_text_from_url(url):
        """Extract and clean text from a given URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                    element.decompose()
                raw_text = soup.get_text()
                return clean_text(raw_text)
            return f"Failed to retrieve content from {url}"
        except requests.RequestException as e:
            return f"Error accessing {url}: {str(e)}"

    try:
        # Google Custom Search API endpoint
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(num_results, 10)  # Google API max is 10 per request
        }

        console.print(f"[bright_cyan]Searching Google for: {query}[/bright_cyan]")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        items = data.get("items", [])
        if not items:
            return {"status": "error", "error": f"No results found for '{query}'"}

        # Extract URLs from search results
        search_urls = [item["link"] for item in items[:num_results]]

        # Recursively extract text from each URL
        extracted_texts = []
        for search_url in search_urls:
            console.print(f"[bright_cyan]Extracting from: {search_url}[/bright_cyan]")
            text = extract_text_from_url(search_url)
            extracted_texts.append(text)
            time.sleep(sleep_time)  # Avoid overloading servers

        # Combine all extracted texts into a single string
        cleaned_text = " ".join(extracted_texts)

        #console.print(Syntax(f"\n{cleaned_text}\n", "python", theme="monokai"))

        return {
            "status": "success",
            "text": cleaned_text,
            "error": None
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to fetch search results: {str(e)}",
            "query": query
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error processing search: {str(e)}",
            "query": query
        }

def check_system_health(duration: int = 10) -> Dict[str, Any]:
    """
    Check system health including memory, CPU, network usage, and logs for errors.

    Args:
        duration (int): Duration in seconds to monitor network usage (default: 10).

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): Detailed system health report if successful
            - error (str, optional): Error message if the operation failed

    Notes:
        - Prioritizes macOS and Linux, with basic Windows support.
        - Checks memory usage, CPU usage, network usage, and recent system logs for errors.
        - Uses psutil for metrics and platform-specific log files for error checking.
    """

    try:
        os_name = platform.system()
        console.print(f"[bright_cyan]Checking system health on {os_name} for {duration} seconds[/bright_cyan]")

        # Memory Usage
        memory = psutil.virtual_memory()
        memory_usage = f"Memory Usage: {memory.percent}% ({memory.used / 1024**3:.2f}/{memory.total / 1024**3:.2f} GB)"

        # CPU Usage
        cpu_usage = f"CPU Usage: {psutil.cpu_percent(interval=1)}% ({psutil.cpu_count()} cores)"

        # Network Usage
        net_start = psutil.net_io_counters()
        time.sleep(duration)
        net_end = psutil.net_io_counters()
        bytes_sent = (net_end.bytes_sent - net_start.bytes_sent) / 1024  # KB
        bytes_recv = (net_end.bytes_recv - net_start.bytes_recv) / 1024  # KB
        network_usage = f"Network Usage (over {duration}s): Sent: {bytes_sent:.2f} KB, Received: {bytes_recv:.2f} KB"

        # System Logs
        log_output = ""
        errors_of_concern = []
        now = datetime.datetime.now()
        time_threshold = now - datetime.timedelta(minutes=60)  # Check last hour

        if os_name == "Darwin":  # macOS
            log_file = Path("/var/log/system.log")
            if log_file.exists():
                with log_file.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-1000:]  # Last 1000 lines for efficiency
                for line in lines:
                    try:
                        # Example macOS log format: "Mar 17 14:00:00 hostname message"
                        timestamp_str = " ".join(line.split()[:3])
                        timestamp = datetime.datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
                        timestamp = timestamp.replace(year=now.year)
                        if timestamp >= time_threshold and "error" in line.lower():
                            errors_of_concern.append(line.strip())
                    except ValueError:
                        continue
                log_output = "macOS System Logs (last hour):\n" + "\n".join(errors_of_concern) if errors_of_concern else "No recent errors found."

        elif os_name == "Linux":
            log_file = Path("/var/log/syslog") if Path("/var/log/syslog").exists() else Path("/var/log/messages")
            if log_file.exists():
                with log_file.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-1000:]  # Last 1000 lines
                for line in lines:
                    try:
                        # Example Linux log format: "Mar 17 14:00:00 hostname message"
                        timestamp_str = " ".join(line.split()[:3])
                        timestamp = datetime.datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
                        timestamp = timestamp.replace(year=now.year)
                        if timestamp >= time_threshold and "error" in line.lower():
                            errors_of_concern.append(line.strip())
                    except ValueError:
                        continue
                log_output = "Linux System Logs (last hour):\n" + "\n".join(errors_of_concern) if errors_of_concern else "No recent errors found."

        elif os_name == "Windows":
            import win32evtlog  # Requires pip install pywin32
            hand = win32evtlog.OpenEventLog(None, "System")
            events = win32evtlog.ReadEventLog(hand, win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0)
            for event in events[:100]:  # Limit to last 100 events
                event_time = datetime.datetime.fromtimestamp(event.TimeGenerated.timestamp())
                if event_time >= time_threshold and event.EventType in (1, 2):  # 1=Error, 2=Warning
                    errors_of_concern.append(f"{event_time}: {event.StringInserts or event.EventID}")
            win32evtlog.CloseEventLog(hand)
            log_output = "Windows System Logs (last hour):\n" + "\n".join(errors_of_concern) if errors_of_concern else "No recent errors found."

        else:
            log_output = "System log checking not supported on this OS."

        # Combine all metrics into a report
        report = (
            f"System Health Report:\n"
            f"{memory_usage}\n"
            f"{cpu_usage}\n"
            f"{network_usage}\n"
            f"{log_output}"
        )
        console.print(Markdown(f"```\n{report}\n```\n"))

        # Health assessment for LLM
        health_status = "Everything appears to be running OK."
        if memory.percent > 90 or psutil.cpu_percent() > 90 or errors_of_concern:
            health_status = "Attention needed: "
            if memory.percent > 90:
                health_status += "High memory usage detected. "
            if psutil.cpu_percent() > 90:
                health_status += "High CPU usage detected. "
            if errors_of_concern:
                health_status += "Recent log errors detected."

        report += f"\nAssessment: {health_status}"
        return {"status": "success", "text": report, "error": None}

    except Exception as e:
        return {"status": "error", "error": f"Failed to check system health: {str(e)}"}

def hello_world():
    print("\nhello world!\n")
    return "hello_world"

