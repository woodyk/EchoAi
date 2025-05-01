#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: gittools.py
# Description: Local Git management functions for EchoAI
# Author: Ms. White 
# Created: 2025-04-29
# Modified: 2025-05-01 14:32:53

import subprocess
from pathlib import Path
from typing import List, Optional

def git_init(repo_path: str) -> dict:
    """Initialize a new Git repository.

    Args:
        repo_path (str): Path where the Git repository should be initialized.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_init("/tmp/myrepo")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "init"], capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_status(repo_path: str) -> dict:
    """Get the status of a Git repository.

    Args:
        repo_path (str): Path to the Git repository.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_status("/tmp/myrepo")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "status"], capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_add(repo_path: str, files: Optional[List[str]] = None) -> dict:
    """Stage one or more files for commit.

    Args:
        repo_path (str): Path to the Git repository.
        files (List[str], optional): List of files to stage. Defaults to all.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_add("/tmp/myrepo", ["file1.txt"])
    """
    try:
        args = ["git", "-C", repo_path, "add"]
        args += files if files else ["."]
        subprocess.run(args, capture_output=True, text=True, check=True)
        return {"status": "success", "output": "Files staged successfully."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_commit(repo_path: str, message: str) -> dict:
    """Commit staged changes with a message.

    Args:
        repo_path (str): Path to the Git repository.
        message (str): Commit message.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_commit("/tmp/myrepo", "Initial commit")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "commit", "-m", message],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_log(repo_path: str, limit: int = 5) -> dict:
    """Get the latest Git commit log.

    Args:
        repo_path (str): Path to the Git repository.
        limit (int): Number of commits to return.

    Returns:
        dict: { "status": ..., "log": ... }

    Example:
        >>> git_log("/tmp/myrepo", 3)
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "log", f"-n{limit}", "--oneline"],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "log": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_config(repo_path: str, key: str, value: str) -> dict:
    """Set Git config key-value at the repository level.

    Args:
        repo_path (str): Path to the Git repository.
        key (str): Config key (e.g., "user.name").
        value (str): Value to assign.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_config("/tmp/myrepo", "user.name", "Ms. White")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "config", key, value],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": f"Set {key} = {value}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_reset(repo_path: str, target: str = "HEAD~1", mode: str = "--hard") -> dict:
    """Reset repository to a previous state.

    Args:
        repo_path (str): Path to the Git repository.
        target (str): Commit ref to reset to (default: HEAD~1).
        mode (str): Reset mode: --soft, --mixed, or --hard.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_reset("/tmp/myrepo", "HEAD~2", "--hard")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "reset", mode, target],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_merge(repo_path: str, source_branch: str) -> dict:
    """Merge another branch into the current branch.

    Args:
        repo_path (str): Path to the Git repository.
        source_branch (str): Name of the branch to merge into current.

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }

    Example:
        >>> git_merge("/tmp/myrepo", "feature-branch")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "merge", source_branch],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}
