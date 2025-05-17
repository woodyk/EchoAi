#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: gittools.py
# Description: Local Git management functions for EchoAI
# Author: Wadih Khairallah
# Created: 2025-04-29
# Modified: 2025-05-01 20:42:57

import subprocess
from typing import List, Optional
from rich.console import Console

console = Console()
print = console.print


def _run_git(args: List[str]) -> dict:
    """Internal helper to run a git subprocess command."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        print(f"{result.stdout.strip()}")
        return {"status": "success", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.strip()}")
        return {"status": "error", "error": f"Command '{' '.join(args)}' failed: {e.stderr.strip()}"}


def _validate_repo_path(repo_path: str) -> bool:
    """Validate if the specified repository path exists and is a Git repository."""
    return subprocess.run(["git", "-C", repo_path, "status"], capture_output=True).returncode == 0


def git_init(repo_path: str) -> dict:
    """Initialize a new Git repository.

    Args:
        repo_path (str): Path where the Git repository should be initialized.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "init"])


def git_status(repo_path: str) -> dict:
    """Get the status of a Git repository.

    Args:
        repo_path (str): Path to the Git repository.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "status"])


def git_add(repo_path: str, files: Optional[List[str]] = None) -> dict:
    """Stage one or more files for commit.

    Args:
        repo_path (str): Path to the Git repository.
        files (List[str], optional): List of files to stage. Defaults to all.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    if not _validate_repo_path(repo_path):
        return {"status": "error", "error": f"Repository path '{repo_path}' is not valid or does not point to a Git repo."}
    args = ["git", "-C", repo_path, "add"] + (files if files else ["."])
    return _run_git(args)


def git_commit(repo_path: str, message: str) -> dict:
    """Commit staged changes with a message.

    Args:
        repo_path (str): Path to the Git repository.
        message (str): Commit message.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "commit", "-m", message])


def git_log(repo_path: str, limit: int = 5) -> dict:
    """Get the latest Git commit log.

    Args:
        repo_path (str): Path to the Git repository.
        limit (int): Number of commits to return.

    Returns:
        dict: { "status": ..., "log": ... }
    """
    return _run_git(["git", "-C", repo_path, "log", f"-n{limit}", "--oneline"])


def git_config(repo_path: str, key: str, value: str) -> dict:
    """Set Git config key-value at the repository level.

    Args:
        repo_path (str): Path to the Git repository.
        key (str): Config key (e.g., "user.name").
        value (str): Value to assign.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "config", key, value])


def git_reset(repo_path: str, target: str = "HEAD~1", mode: str = "--hard") -> dict:
    """Reset repository to a previous state.

    Args:
        repo_path (str): Path to the Git repository.
        target (str): Commit ref to reset to (default: HEAD~1).
        mode (str): Reset mode: --soft, --mixed, or --hard.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "reset", mode, target])


def git_merge(repo_path: str, source_branch: str) -> dict:
    """Merge another branch into the current branch.

    Args:
        repo_path (str): Path to the Git repository.
        source_branch (str): Name of the branch to merge into current.

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }
    """
    return _run_git(["git", "-C", repo_path, "merge", source_branch])


def git_push(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """Push committed changes to a remote repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (str): Remote name (e.g., 'origin').
        branch (str): Branch to push (e.g., 'main').

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }
    """
    return _run_git(["git", "-C", repo_path, "push", remote, branch])


def git_pull(repo_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """Pull changes from a remote repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (str): Remote name (e.g., 'origin').
        branch (str): Branch to pull (e.g., 'main').

    Returns:
        dict: { "status": ..., "output": ..., "error": str (if any) }
    """
    return _run_git(["git", "-C", repo_path, "pull", remote, branch])


def git_branch_current(repo_path: str) -> dict:
    """Get the name of the current Git branch.

    Args:
        repo_path (str): Path to the Git repository.

    Returns:
        dict: { "status": ..., "branch": str }
    """
    result = _run_git(["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"])
    if result["status"] == "success":
        return {"status": "success", "branch": result["output"]}
    return result


def git_branch_list(repo_path: str, remote: bool = False) -> dict:
    """List branches in a Git repository.

    Args:
        repo_path (str): Path to the Git repository.
        remote (bool): List remote branches instead of local.

    Returns:
        dict: { "status": ..., "branches": List[str] }
    """
    args = ["git", "-C", repo_path, "branch"]
    if remote:
        args.append("-r")
    result = _run_git(args)
    if result["status"] == "success":
        branches = [b.strip().lstrip("* ") for b in result["output"].splitlines()]
        return {"status": "success", "branches": branches}
    return result


def git_branch_create(repo_path: str, name: str, checkout: bool = True) -> dict:
    """Create a new Git branch, optionally checking it out.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to create.
        checkout (bool): If True, switch to new branch after creation.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    result = _run_git(["git", "-C", repo_path, "branch", name])
    if checkout and result["status"] == "success":
        result = _run_git(["git", "-C", repo_path, "checkout", name])
    return result


def git_checkout(repo_path: str, name: str) -> dict:
    """Switch to a specific Git branch.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to switch to.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "checkout", name])


def git_branch_delete(repo_path: str, name: str, force: bool = False) -> dict:
    """Delete a Git branch by name.

    Args:
        repo_path (str): Path to the Git repository.
        name (str): Branch name to delete.
        force (bool): If True, use '-D' (force delete).

    Returns:
        dict: { "status": ..., "output": ... }
    """
    flag = "-D" if force else "-d"
    return _run_git(["git", "-C", repo_path, "branch", flag, name])


def git_branch_rename(repo_path: str, old: str, new: str) -> dict:
    """Rename a Git branch.

    Args:
        repo_path (str): Path to the Git repository.
        old (str): Old branch name.
        new (str): New branch name.

    Returns:
        dict: { "status": ..., "output": ... }
    """
    return _run_git(["git", "-C", repo_path, "branch", "-m", old, new])


def git_branch_force_delete(repo_path: str, branch: str, fallback: str = "master") -> dict:
    """Force-delete a branch, switching to a fallback branch first if needed.

    Args:
        repo_path (str): Path to the Git repository.
        branch (str): Name of the branch to delete.
        fallback (str): Branch to switch to before deleting if the branch is checked out.

    Returns:
        dict: { "status": ..., "output": ..., "error": ... }
    """
    current = git_branch_current(repo_path)
    if current["status"] == "success" and current["branch"] == branch:
        _ = _run_git(["git", "-C", repo_path, "checkout", fallback])
    return _run_git(["git", "-C", repo_path, "branch", "-D", branch])