#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: session.py
# Description: EchoAI session manager with full CRUD and branching
# Author: Ms. White
# Created: 2025-05-02
# Modified: 2025-05-02 16:45:46

import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict


class Session:
    def __init__(self, directory: str = "~/.echoai/sessions"):
        self.path = Path(os.path.expanduser(directory))
        self.path.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # Core CRUD
    # ---------------------------

    def list(self) -> List[Dict]:
        """Return metadata for all sessions."""
        out = []
        for file in self.path.glob("*.json"):
            try:
                with open(file, "r") as f:
                    d = json.load(f)
                    out.append({
                        "id": d.get("id"),
                        "name": d.get("name"),
                        "created": d.get("created"),
                        "tags": d.get("tags", []),
                        "summary": d.get("summary")
                    })
            except Exception:
                continue
        return sorted(out, key=lambda x: x["created"], reverse=True)

    def create(self, name: str, tags: Optional[List[str]] = None) -> str:
        """Create and persist a new session."""
        sid = str(uuid.uuid4())
        session = {
            "id": sid,
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "parent": None,
            "branch_point": None,
            "tags": tags or [],
            "summary": None,
            "messages": []
        }
        self._save_file(sid, session)
        return sid

    def load(self, session_id: str) -> List[Dict]:
        """Return OpenAI-compatible message list from a session (filtering internal keys)."""
        session = self._read_file(session_id)
        clean = []
        for m in session.get("messages", []):
            clean.append({
                k: v for k, v in m.items()
                if k in {"role", "content", "tool_calls", "name", "function_call", "tool_call_id"}
            })
        return clean

    def load_full(self, session_id: str) -> Dict:
        """Return the complete session file as-is (raw)."""
        return self._read_file(session_id)

    def delete(self, session_id: str):
        """Delete session file."""
        file = self.path / f"{session_id}.json"
        if file.exists():
            file.unlink()

    def update(self, session_id: str, key: str, value: Any):
        """Update a top-level key in a session."""
        session = self._read_file(session_id)
        session[key] = value
        self._save_file(session_id, session)

    # ---------------------------
    # Message Operations
    # ---------------------------

    def msg_insert(self, session_id: str, message: Dict) -> str:
        """Insert a new message into a session, augmenting with timestamp and UUID."""
        session = self._read_file(session_id)
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **message
        }
        session["messages"].append(entry)
        self._save_file(session_id, session)
        return entry["id"]

    def msg_get(self, session_id: str, message_id: str) -> Optional[Dict]:
        """Return the message object with the given ID."""
        session = self._read_file(session_id)
        for msg in session.get("messages", []):
            if msg.get("id") == message_id:
                return msg
        return None

    def msg_index(self, session_id: str, message_id: str) -> Optional[int]:
        """Return the index of the message with the given ID."""
        session = self._read_file(session_id)
        for i, msg in enumerate(session.get("messages", [])):
            if msg.get("id") == message_id:
                return i
        return None

    def msg_update(self, session_id: str, message_id: str, new_content: str) -> bool:
        """Update the `content` of a message by ID."""
        session = self._read_file(session_id)
        for m in session["messages"]:
            if m.get("id") == message_id:
                m["content"] = new_content
                self._save_file(session_id, session)
                return True
        return False

    def msg_delete(self, session_id: str, message_id: str) -> bool:
        """Remove a message by ID."""
        session = self._read_file(session_id)
        before = len(session["messages"])
        session["messages"] = [m for m in session["messages"] if m.get("id") != message_id]
        self._save_file(session_id, session)
        return len(session["messages"]) < before

    # ---------------------------
    # Branching & Summarization
    # ---------------------------

    def branch(self, from_id: str, message_id: str, new_name: str) -> str:
        """Create a new session branched from a given message in an existing session."""
        base = self._read_file(from_id)
        index = next((i for i, m in enumerate(base["messages"]) if m.get("id") == message_id), None)
        if index is None:
            raise ValueError(f"Message ID {message_id} not found in session {from_id}.")
        partial = base["messages"][:index + 1]
        new_id = str(uuid.uuid4())
        branch = {
            "id": new_id,
            "name": new_name,
            "created": datetime.now(timezone.utc).isoformat(),
            "parent": from_id,
            "branch_point": message_id,
            "tags": base.get("tags", []),
            "summary": None,
            "messages": partial
        }
        self._save_file(new_id, branch)
        return new_id

    def summarize(self, interactor, session_id: str) -> str:
        """Generate a short summary using Interactor and update the session."""
        clean_messages = self.load(session_id)
        summary_prompt = "Summarize the following interaction in 3-4 sentences."
        interactor.messages_flush()
        interactor.messages_add(role="system", content=summary_prompt)
        for msg in clean_messages:
            interactor.messages_add(**msg)
        summary = interactor.interact(user_input=None, stream=False, quiet=True)
        self.update(session_id, "summary", summary)
        return summary

    # ---------------------------
    # Search Capabilities
    # ---------------------------

    def search(self, query: str, session_id: Optional[str] = None) -> List[Dict]:
        """
        Search messages across all sessions or a specific one.
        Returns session dicts with only the matching messages populated.
        """
        result = []
        sessions = [session_id] if session_id else [f.stem for f in self.path.glob("*.json")]

        for sid in sessions:
            try:
                data = self._read_file(sid)
                matching = [
                    msg for msg in data.get("messages", [])
                    if query.lower() in (msg.get("content") or "").lower()
                ]
                if matching:
                    result.append({
                        "id": data["id"],
                        "name": data["name"],
                        "created": data["created"],
                        "parent": data.get("parent"),
                        "branch_point": data.get("branch_point"),
                        "tags": data.get("tags", []),
                        "summary": data.get("summary"),
                        "messages": matching
                    })
            except Exception:
                continue
        return result

    def search_meta(self, query: str) -> List[Dict]:
        """
        Search top-level metadata fields of all sessions.
        Returns sessions where name, tags, or summary match.
        """
        result = []
        for file in self.path.glob("*.json"):
            try:
                data = self._read_file(file.stem)
                searchable = " ".join([
                    data.get("name", ""),
                    data.get("summary", "") or "",
                    " ".join(data.get("tags", []))
                ]).lower()
                if query.lower() in searchable:
                    result.append({
                        "id": data["id"],
                        "name": data["name"],
                        "created": data["created"],
                        "parent": data.get("parent"),
                        "branch_point": data.get("branch_point"),
                        "tags": data.get("tags", []),
                        "summary": data.get("summary")
                    })
            except Exception:
                continue
        return result

    # ---------------------------
    # Internal I/O
    # ---------------------------

    def _read_file(self, session_id: str) -> Dict:
        file = self.path / f"{session_id}.json"
        if not file.exists():
            raise FileNotFoundError(f"Session {session_id} not found.")
        with open(file, "r") as f:
            return json.load(f)

    def _save_file(self, session_id: str, data: Dict):
        file = self.path / f"{session_id}.json"
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

