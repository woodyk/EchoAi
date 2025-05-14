#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: task_manager.py
# Author: Ms. White
# Purpose: Internal assistant task tracker with optional CLI access
# Created: 2025-04-30
# Modified: 2025-05-14 16:49:07

import os
import json
import uuid
import datetime
from typing import Union
from pathlib import Path

TASK_FILE = os.path.expanduser("~/.echoai/tasks.json")
Path(os.path.dirname(TASK_FILE)).mkdir(parents=True, exist_ok=True)


def task_add(content: str, metadata: dict = None) -> dict:
    """
    Add a new task to the assistant's internal task list.

    Args:
        content (str): Description of the task to track.
        metadata (dict, optional): Additional info like tags or notes.

    Returns:
        dict: { "status": "success", "result": task, "error": None }
    """
    def load():
        if not os.path.exists(TASK_FILE): return []
        with open(TASK_FILE, "r") as f: return json.load(f)

    def save(data):
        with open(TASK_FILE, "w") as f: json.dump(data, f, indent=2)

    tasks = load()
    metadata = metadata or {}
    now = datetime.datetime.now(datetime.UTC)
    new_task = {
        "id": str(uuid.uuid4())[:8],
        "content": content,
        "status": "pending",
        "created": now.isoformat(),
        "updated": None,
        "tag": metadata.get("tag"),
        "notes": metadata.get("notes")
    }
    tasks.append(new_task)
    save(tasks)
    return {"status": "success", "result": new_task, "error": None}


def task_list(filters: dict = None) -> dict:
    """
    List tasks, optionally filtered by {"status": ..., "tag": ...}.

    Args:
        filters (dict, optional): Filter by fields like status or tag.

    Returns:
        dict: { "status": "success", "result": [tasks], "error": None }
    """
    def load():
        if not os.path.exists(TASK_FILE): return []
        with open(TASK_FILE, "r") as f: return json.load(f)

    tasks = load()
    filters = filters or {}
    for key, val in filters.items():
        tasks = [t for t in tasks if t.get(key) == val]
    return {"status": "success", "result": tasks, "error": None}

def task_update(task_id: str, update: Union[str, dict]) -> dict:
    """
    Update an existing task by ID.

    This function supports updating:
      - content (as a plain string), or
      - any combination of: status, tag, notes (via dict)

    Args:
        task_id (str): The ID of the task to update.
        update (str or dict): The new content (string), or a dictionary containing one or more of:
            - "content": str
            - "status": str ("pending", "in-progress", "done")
            - "tag": str
            - "notes": str

    Returns:
        dict: {
            "status": "success" or "error",
            "result": updated_task (if successful),
            "error": error message (if failed)
        }
    """

    def load():
        if not os.path.exists(TASK_FILE): return []
        with open(TASK_FILE, "r") as f: return json.load(f)

    def save(data):
        with open(TASK_FILE, "w") as f: json.dump(data, f, indent=2)

    def find(tasks, tid): return next((t for t in tasks if t["id"] == tid), None)

    tasks = load()
    task = find(tasks, task_id)
    if not task:
        return {"status": "error", "result": None, "error": f"Task ID {task_id} not found"}

    if isinstance(update, dict):
        for key in ["content", "status", "tag", "notes"]:
            if key in update:
                task[key] = update[key]
    else:
        task["content"] = update

    task["updated"] = datetime.datetime.now(datetime.UTC).isoformat()
    save(tasks)
    return {"status": "success", "result": task, "error": None}


def task_delete(task_id: str) -> dict:
    """
    Delete a task by ID.

    Args:
        task_id (str): Unique ID of the task.

    Returns:
        dict: { "status": "success", "result": confirmation, "error": None }
    """
    def load():
        if not os.path.exists(TASK_FILE): return []
        with open(TASK_FILE, "r") as f: return json.load(f)

    def save(data):
        with open(TASK_FILE, "w") as f: json.dump(data, f, indent=2)

    tasks = load()
    filtered = [t for t in tasks if t["id"] != task_id]
    if len(filtered) == len(tasks):
        return {"status": "error", "result": None, "error": f"Task ID {task_id} not found"}
    save(filtered)
    return {"status": "success", "result": f"Deleted task {task_id}", "error": None}


def task_complete(task_id: str) -> dict:
    """
    Mark a task as complete.

    Args:
        task_id (str): ID of the task to complete.

    Returns:
        dict: { "status": "success", "result": updated_task, "error": None }
    """
    return task_update(task_id, {"status": "done"})


# -------------------------------
# CLI Entry Point
# -------------------------------
if __name__ == "__main__":
    import argparse
    from rich.console import Console
    from rich.table import Table
    from rich import print

    console = Console()
    parser = argparse.ArgumentParser(description="EchoAI Task Manager (Internal CLI)")
    parser.add_argument("action", choices=["add", "list", "update", "delete", "complete"], help="Action to perform")
    parser.add_argument("args", nargs="*", help="Arguments for the action")
    args = parser.parse_args()

    result = None
    try:
        if args.action == "add":
            content = args.args[0]
            metadata = json.loads(args.args[1]) if len(args.args) > 1 else {}
            result = task_add(content, metadata)
        elif args.action == "list":
            filters = json.loads(args.args[0]) if args.args else {}
            result = task_list(filters)
        elif args.action == "update":
            task_id = args.args[0]
            update = json.loads(args.args[1]) if len(args.args) > 1 else ""
            result = task_update(task_id, update)
        elif args.action == "delete":
            result = task_delete(args.args[0])
        elif args.action == "complete":
            result = task_complete(args.args[0])
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        exit(1)

    if result and result["status"] == "success":
        if args.action == "list":
            table = Table(title="Task List")
            table.add_column("ID", style="cyan")
            table.add_column("Content", style="white")
            table.add_column("Status", style="green")
            table.add_column("Tag", style="magenta")
            table.add_column("Notes", style="yellow")
            for t in result["result"]:
                table.add_row(t["id"], t["content"], t["status"], str(t.get("tag", "")), str(t.get("notes", "")))
            console.print(table)
        else:
            print(result["result"])
    else:
        console.print(f"[red]Failed:[/red] {result['error']}")

