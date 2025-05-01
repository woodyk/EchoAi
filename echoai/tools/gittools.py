#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: gittools.py
# Description: Local Git management functions for EchoAI
# Author: Wadih Khairallah
# Created: 2025-04-29
# Modified: 2025-05-01 14:40:44

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



def git_push(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """Push committed changes to a remote repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (str): Remote name (e.g., 'origin').
        branch (str): Branch to push (e.g., 'main').

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }

    Example:
        >>> git_push("/projects/myrepo", remote="origin", branch="main")
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "push", remote, branch],
            capture_output=True, text=True, check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}



def git_pull(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """Pull changes from a remote repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (str): Remote name (e.g., 'origin').
        branch (str): Branch to pull (e.g., 'main').

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }

    Example:
        >>> git_pull("/projects/myrepo", remote="origin", branch="main")
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "pull", remote, branch],
            capture_output=True, text=True, check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}



def git_branch_current(repo_path: str) -> dict:
    """Get the name of the current Git branch.

    Args:
        repo_path (str): Path to the Git repository.

    Returns:
        dict: { "status": ..., "branch": str }

    Example:
        >>> git_branch_current("/project")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "branch": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_branch_list(repo_path: str, remote: bool = False) -> dict:
    """List branches in a Git repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (bool): List remote branches instead of local.

    Returns:
        dict: { "status": ..., "branches": List[str] }

    Example:
        >>> git_branch_list("/repo", remote=False)
    """
    try:
        cmd = ["git", "-C", repo_path, "branch"]
        if remote:
            cmd.append("-r")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        branches = [b.strip().lstrip("* ") for b in result.stdout.splitlines()]
        return {"status": "success", "branches": branches}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_branch_create(repo_path: str, name: str, checkout: bool = True) -> dict:
    """Create a new Git branch, optionally checking it out.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to create.
        checkout (bool): If True, switch to new branch after creation.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_branch_create("/repo", "feature-x")
    """
    try:
        subprocess.run(["git", "-C", repo_path, "branch", name],
                       capture_output=True, text=True, check=True)
        if checkout:
            subprocess.run(["git", "-C", repo_path, "checkout", name],
                           capture_output=True, text=True, check=True)
        return {"status": "success", "output": f"Branch '{name}' created."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_checkout(repo_path: str, name: str) -> dict:
    """Switch to a specific Git branch.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to switch to.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_checkout("/repo", "develop")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "checkout", name],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_branch_delete(repo_path: str, name: str, force: bool = False) -> dict:
    """Delete a Git branch by name.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to delete.
        force (bool): If True, use '-D' (force delete).

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_branch_delete("/repo", "old-feature", force=True)
    """
    try:
        flag = "-D" if force else "-d"
        result = subprocess.run(["git", "-C", repo_path, "branch", flag, name],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}


def git_branch_rename(repo_path: str, old: str, new: str) -> dict:
    """Rename a Git branch.

    Args:
        repo_path (str): Path to the Git repository.
        old (str): Old branch name.
        new (str): New branch name.

    Returns:
        dict: { "status": ..., "output": ... }

    Example:
        >>> git_branch_rename("/repo", "dev", "dev-archive")
    """
    try:
        result = subprocess.run(["git", "-C", repo_path, "branch", "-m", old, new],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}



def git_branch_force_delete(repo_path: str, branch: str, fallback: str = "master") -> dict:
    """Force-delete a branch, switching to a fallback branch first if needed.

    Args:
        repo_path (str): Path to the Git repository.
        branch (str): Name of the branch to delete.
        fallback (str): Branch to switch to before deleting if the branch is checked out.

    Returns:
        dict: { "status": ..., "output": ..., "error": ... }

    Example:
        >>> git_branch_force_delete("/repo", "feature-xyz", fallback="main")
    """
    try:
        # Get current branch
        result = subprocess.run(["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()

        if current_branch == branch:
            subprocess.run(["git", "-C", repo_path, "checkout", fallback],
                           capture_output=True, text=True, check=True)

        result = subprocess.run(["git", "-C", repo_path, "branch", "-D", branch],
                                capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}
