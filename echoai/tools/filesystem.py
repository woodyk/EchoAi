#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: filesystem.py
# Description: Modular file system operations for EchoAI with safe editing support
# Author: Ms. White
# Created: 2025-04-29
# Modified: 2025-05-01 20:43:11
# Updated: 2025-05-01

import os
import shutil
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()
print = console.print


def _resolve_path(path: str) -> Path:
    """Normalize and resolve a user-provided path."""
    return Path(path).expanduser().resolve()


def file_copy(src: str, dst: str) -> dict:
    """Copy a file from src to dst."""
    print(f"copy: {src} -> {dst}")
    try:
        shutil.copy2(_resolve_path(src), _resolve_path(dst))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_move(src: str, dst: str) -> dict:
    """Move a file from src to dst."""
    print(f"move: {src} -> {dst}")
    try:
        shutil.move(_resolve_path(src), _resolve_path(dst))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_delete(path: str) -> dict:
    """Delete a file from the filesystem."""
    print(f"delete: {path}")
    try:
        _resolve_path(path).unlink()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_append(path: str, content: str) -> dict:
    """Append a line of content to the end of the file."""
    print(f"append: {path}")
    try:
        with open(_resolve_path(path), "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_write(path: str, content: str) -> dict:
    """Overwrite a file completely with new content."""
    print(f"write: {path}")
    try:
        _resolve_path(path).write_text(content, encoding="utf-8")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_insert(path: str, match: str, content: str, before: bool = False) -> dict:
    """Insert content relative to a matching pattern in a file."""
    print(f"insert: {path}")
    try:
        p = _resolve_path(path)
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if match in line:
                index = i if before else i + 1
                lines.insert(index, content)
                break
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_replace_lines(path: str, replacements: dict) -> dict:
    """Replace several specific lines in a file by line number."""
    print(f"replace_lines: {path}")
    try:
        p = _resolve_path(path)
        lines = p.read_text(encoding="utf-8").splitlines()
        for lineno, newtext in replacements.items():
            if 0 <= lineno - 1 < len(lines):
                lines[lineno - 1] = newtext
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_replace_function(path: str, function_name: str, new_content: str) -> dict:
    """Replace a Python function definition by name with new content."""
    print(f"replace_function: {path} -> {function_name}")
    try:
        p = _resolve_path(path)
        lines = p.read_text(encoding="utf-8").splitlines()
        start, end = None, None
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and function_name in line.split("(")[0]:
                start = i
                indent = len(line) - len(line.lstrip())
                end = i + 1
                while end < len(lines):
                    if lines[end].strip() and (len(lines[end]) - len(lines[end].lstrip())) <= indent:
                        break
                    end += 1
                break
        if start is None or end is None:
            return {"status": "error", "error": f"Function '{function_name}' not found"}
        new_block = new_content.strip().splitlines()
        lines[start:end] = new_block
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_mkdir(path: str) -> dict:
    """Create a directory at the specified path."""
    print(f"mkdir: {path}")
    try:
        _resolve_path(path).mkdir(parents=True, exist_ok=True)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_listdir(path: str, ext: Optional[str] = None) -> dict:
    """List files in a directory with optional extension filter."""
    print(f"listdir: {path}")
    try:
        p = _resolve_path(path)
        files = [f.name for f in p.iterdir() if f.is_file()]
        if ext:
            files = [f for f in files if f.endswith(ext)]
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_read_lines(path: str, start: int, end: int) -> dict:
    """Read specific lines from a file by line number range (1-based)."""
    print(f"read_lines: {path} : {start} -> {end}")
    try:
        lines = _resolve_path(path).read_text(encoding="utf-8").splitlines()
        selected = lines[start - 1:end]
        return {"status": "success", "lines": selected}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_grep(path: str, pattern: str, context: int = 2) -> dict:
    """Search a file for a given pattern and return matched lines with context."""
    print(f"grep: {path} : {pattern} : {context}")
    try:
        lines = _resolve_path(path).read_text(encoding="utf-8").splitlines()
        matches = []
        for i, line in enumerate(lines):
            if pattern in line:
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                matches.append({
                    "line": i + 1,
                    "snippet": lines[start:end]
                })
        return {"status": "success", "matches": matches}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_summary(path: str, keywords: list[str], context: int = 3) -> dict:
    """Summarize a file by extracting sections around given keywords."""
    print(f"summary: {path} : {keywords} : {context}")
    try:
        lines = _resolve_path(path).read_text(encoding="utf-8").splitlines()
        results = []
        for i, line in enumerate(lines):
            if any(keyword.lower() in line.lower() for keyword in keywords):
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                results.append({
                    "line": i + 1,
                    "snippet": lines[start:end]
                })
        return {"status": "success", "summary": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_exists(path: str) -> dict:
    """Check whether a file exists."""
    print(f"exists: {path}")
    try:
        exists = _resolve_path(path).is_file()
        return {"status": "success", "exists": exists}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def file_head_tail(path: str, lines: int = 10, tail: bool = False) -> dict:
    """Get the first or last N lines of a file."""
    print(f"head_tail: {path} : {lines} : {tail}")
    try:
        all_lines = _resolve_path(path).read_text(encoding="utf-8").splitlines()
        result = all_lines[-lines:] if tail else all_lines[:lines]
        return {"status": "success", "lines": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

