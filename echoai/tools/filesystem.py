#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: filesystem.py
# Description: Modular file system operations for EchoAI with safe editing support
# Author: Ms. White 
# Created: 2025-04-29
# Modified: 2025-05-03 23:42:45

import os
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from rich.console import Console

console = Console()

def file_copy(src: str, dst: str) -> dict:
    """Copy a file from src to dst.

    Args:
        src (str): Path to the source file.
        dst (str): Destination path where the file will be copied.

    Returns:
        dict: { "status": "success" | "error", "output": str, "error": str (if any) }

    Example:
        >>> file_copy("data.txt", "backup/data.txt")
    """
    try:
        shutil.copy2(src, dst)
        return {"status": "success", "output": f"Copied to {dst}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_move(src: str, dst: str) -> dict:
    """Move a file from src to dst.

    Args:
        src (str): Path to the source file.
        dst (str): Destination path to move the file to.

    Returns:
        dict: { "status": ..., "output": ..., "error": ... }

    Example:
        >>> file_move("old.log", "archive/old.log")
    """
    try:
        shutil.move(src, dst)
        return {"status": "success", "output": f"Moved to {dst}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_delete(path: str) -> dict:
    """Delete a file from the filesystem.

    Args:
        path (str): File path to delete.

    Returns:
        dict: { "status": ..., "output": ..., "error": ... }

    Example:
        >>> file_delete("temp.txt")
    """
    try:
        Path(path).unlink()
        return {"status": "success", "output": f"Deleted {path}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_grep(path: str, pattern: str, context: int = 0) -> dict:
    """Search a file for a given pattern and return matched lines with context.

    Args:
        path (str): File to search.
        pattern (str): Search string.
        context (int): Number of context lines before/after match.

    Returns:
        dict: {
            "status": ...,
            "matches": [
                { "line": int, "match": str, "context": List[str] }
            ]
        }

    Example:
        >>> file_grep("server.log", "ERROR", context=2)
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        matches = []
        for i, line in enumerate(lines):
            if pattern in line:
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                matches.append({
                    "line": i + 1,
                    "match": line.strip(),
                    "context": lines[start:end]
                })
        return {"status": "success", "matches": matches}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_append(path: str, content: str) -> dict:
    """Append a line of content to the end of the file.

    Args:
        path (str): Target file.
        content (str): Content to append.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> file_append("todo.md", "- [ ] Add test coverage")
    """
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content.strip())
        return {"status": "success", "output": "Content appended."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_write(path: str, content: str) -> dict:
    """Overwrite a file completely with new content.

    Args:
        path (str): File path to overwrite.
        content (str): New file content.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> file_write("summary.md", "# Report\nAll tasks completed.")
    """
    try:
        Path(path).write_text(content.strip(), encoding="utf-8")
        return {"status": "success", "output": "File written successfully."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_insert(path: str, pattern: str, content: str, after: bool = True) -> dict:
    """Insert content relative to a matching pattern in a file.

    Args:
        path (str): Target file.
        pattern (str): Line pattern to locate.
        content (str): Line to insert.
        after (bool): If True, insert after; else before.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> file_insert("main.py", "import os", "import sys", after=True)
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if pattern in line:
                idx = i + 1 if after else i
                lines.insert(idx, content.strip())
                Path(path).write_text("\n".join(lines), encoding="utf-8")
                return {"status": "success", "output": f"Inserted at line {idx + 1}"}
        return {"status": "error", "error": "Pattern not found."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_replace_lines(path: str, changes: List[Tuple[int, str]]) -> dict:
    """Replace several specific lines in a file by line number.

    Args:
        path (str): Target file.
        changes (List[Tuple[int, str]]): List of (line_number, replacement_text)

    Returns:
        dict: {
            "status": ...,
            "replaced": [ { "line": int, "before": str, "after": str } ]
        }

    Example:
        >>> file_replace_lines("config.py", [(3, "DEBUG = False"), (10, "timeout = 30")])
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        replaced = []
        for lineno, new_text in changes:
            if 1 <= lineno <= len(lines):
                before = lines[lineno - 1]
                lines[lineno - 1] = new_text.strip()
                replaced.append({"line": lineno, "before": before, "after": new_text.strip()})
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return {"status": "success", "replaced": replaced}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_replace_function(path: str, func_name: str, new_body: str) -> dict:
    """Replace a Python function definition by name with new content.

    This is indentation-aware and finds the function by `def <name>(...)` signature.

    Args:
        path (str): Target .py file.
        func_name (str): Name of the function to replace.
        new_body (str): Replacement function code as a string.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> file_replace_function("utils.py", "process_data", "def process_data(): return []")
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        start_line = None
        start_indent = ""
        end_line = len(lines)

        for i, line in enumerate(lines):
            if f"def {func_name}(" in line.strip():
                start_line = i
                start_indent = line[:len(line) - len(line.lstrip())]
                break

        if start_line is None:
            return {"status": "error", "error": f"Function '{func_name}' not found"}

        for j in range(start_line + 1, len(lines)):
            current_line = lines[j]
            if current_line.strip().startswith("def ") or current_line.strip().startswith("class "):
                line_indent = current_line[:len(current_line) - len(current_line.lstrip())]
                if len(line_indent) <= len(start_indent):
                    end_line = j
                    break

        new_lines = lines[:start_line] + new_body.strip().splitlines() + lines[end_line:]
        Path(path).write_text("\n".join(new_lines), encoding="utf-8")
        return {"status": "success", "output": f"Function '{func_name}' replaced"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_mkdir(path: str, parents: bool = True) -> dict:
    """Create a directory at the specified path.

    Args:
        path (str): Directory path to create.
        parents (bool): If True, create parent directories as needed.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> file_mkdir("data/models", parents=True)
    """
    try:
        Path(path).mkdir(parents=parents, exist_ok=True)
        return {"status": "success", "output": f"Created directory: {path}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_listdir(path: str, extension: str = "") -> dict:
    """List files in a directory with optional extension filter.

    Args:
        path (str): Directory path.
        extension (str): Optional extension filter (e.g., ".py")

    Returns:
        dict: { "status": ..., "files": List[str] }

    Example:
        >>> file_listdir("src", extension=".py")
    """
    try:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            return {"status": "error", "error": f"{path} is not a directory"}
        files = [str(f.name) for f in p.iterdir() if f.is_file()]
        if extension:
            files = [f for f in files if Path(f).suffix == extension]
        if not files:  # Added to clarify if no files found
            return {"status": "warning", "warning": "No files found matching criteria", "files": files}
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_read_lines(path: str, start: int, end: int) -> dict:
    """Read specific lines from a file by line number range (1-based).

    Args:
        path (str): File path.
        start (int): Starting line number.
        end (int): Ending line number (inclusive).

    Returns:
        dict: { "status": ..., "lines": List[str] }

    Example:
        >>> file_read_lines("main.py", 5, 10)
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        if start < 1 or end > len(lines):
            return {"status": "error", "error": "Invalid line range"}
        return {"status": "success", "lines": lines[start-1:end]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_summary(path: str, keywords: List[str], context: int = 2) -> dict:
    """Summarize a file by extracting sections around given keywords.

    Args:
        path (str): File path.
        keywords (List[str]): Terms to search for.
        context (int): Number of surrounding lines to include.

    Returns:
        dict: {
            "status": ...,
            "highlights": [ { "keyword": str, "line": int, "context": List[str] } ]
        }

    Example:
        >>> file_summary("notes.md", ["TODO", "WARNING"])
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        highlights = []
        for i, line in enumerate(lines):
            for kw in keywords:
                if kw.lower() in line.lower():
                    start = max(0, i - context)
                    end = min(len(lines), i + context + 1)
                    highlights.append({
                        "keyword": kw,
                        "line": i + 1,
                        "context": lines[start:end]
                    })
        return {"status": "success", "highlights": highlights}
    except Exception as e:
        return {"status": "error", "error": str(e)}