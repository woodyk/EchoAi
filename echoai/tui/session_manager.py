#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: session_manager.py
# Description: Urwid-based Session Manager TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-05 03:06:47

import urwid
from collections import Counter
from echoai import session as session_api
from echoai.tui.tui_layout import get_theme_palette, DynamicHeader

class SessionManager:
    def __init__(self, theme_name="default"):
        # Load theme
        self.palette, self.theme = get_theme_palette(theme_name)
        # Session API
        self.session_mgr = session_api.Session()
        self.sessions = self.load_sorted_sessions()
        self.filtered_sessions = list(self.sessions)
        self.active_query = ""
        self.selected_sid = None

        # UI state
        self.mode = 'main'
        self.input_text = ""
        self.current_index = 0
        self.preview_box = None
        self.edit_widgets = {}
        self.info_focus = None

        # Header, body, footer
        self.header_obj = DynamicHeader("Select Session")
        header = self.header_obj.get_widget()

        # Build body list
        self.body_widget = urwid.SimpleFocusListWalker(self.build_session_list())
        body = urwid.ListBox(self.body_widget)

        # Footer
        self.footer_text = urwid.Text("", align="center")
        self.footer = urwid.AttrMap(self.footer_text, 'footer')

        # Main frame
        self.main_frame = urwid.Frame(
            header=header,
            body=body,
            footer=self.footer
        )

        # Setup loop
        self.screen = urwid.raw_display.Screen()
        self.screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            self.main_frame,
            self.palette,
            screen=self.screen,
            unhandled_input=self.handle_input
        )

        self.update_footer()

    def load_sorted_sessions(self):
        sessions = self.session_mgr.list()
        return sorted(
            sessions,
            key=lambda s: s.get("updated", s["created"]),
            reverse=True
        )

    def refresh_sessions(self):
        self.sessions = self.load_sorted_sessions()
        if self.active_query:
            self.filtered_sessions = self.session_mgr.search_meta(self.active_query)
        else:
            self.filtered_sessions = list(self.sessions)
        self.current_index = min(self.current_index, len(self.filtered_sessions) - 1)
        self.body_widget[:] = self.build_session_list()

    def build_session_list(self):
        items = []
        for i, s in enumerate(self.filtered_sessions):
            name = s.get("name", "unnamed")
            sid = s.get("id", "")[:8]
            tags = f" [{', '.join(s.get('tags', []))}]" if s.get('tags') else ""
            label = f"{name} ({sid}){tags}"
            prefix = "> " if i == self.current_index else "  "
            style = "highlight" if i == self.current_index else "default"
            items.append(urwid.AttrMap(urwid.Text(prefix + label), style))
        return items

    def build_preview(self, session_id):
        msgs = self.session_mgr.load(session_id)
        lines = []
        role_colors = {
            "user": "prompt",
            "assistant": "output",
            "system": "footer",
            "tool": "input"
        }
        for msg in msgs:
            role = msg.get("role", "unknown").lower()
            content = (msg.get("content") or "").strip()
            role_style = role_colors.get(role, "highlight")
            lines.append((role_style, f"{role}:"))
            for ln in content.splitlines():
                lines.append((None, "  " + ln))
            lines.append((None, ""))

        widgets = []
        for style, txt in lines:
            w = urwid.Text(txt)
            widgets.append(urwid.AttrMap(w, style) if style else w)

        walker = urwid.SimpleFocusListWalker(widgets)
        walker.set_focus(0)
        self.preview_box = urwid.ListBox(walker)
        return self.preview_box

    def build_editable_info_view(self, session_id):
        session = next((s for s in self.sessions if s["id"] == session_id), {})
        name = session.get("name") or ""
        tags = ", ".join(session.get("tags", []))
        summary = session.get("summary") or ""

        self.edit_widgets = {
            "name": urwid.Edit(("footer", "Name: "), name),
            "tags": urwid.Edit(("footer", "Tags: "), tags),
            "summary": urwid.Edit(("footer", "Summary: "), summary),
        }

        lines = [
            urwid.AttrMap(urwid.Text("Session Metadata Editor"), "highlight"),
            urwid.Divider(),
            self.edit_widgets["name"],
            urwid.Divider(),
            self.edit_widgets["tags"],
            urwid.Divider(),
            self.edit_widgets["summary"],
            urwid.Divider(),
            urwid.Text(f"ID:      {session.get('id','') }"),
            urwid.Text(f"Created: {session.get('created','')}"),
            urwid.Text(f"Updated: {session.get('updated','')}"),
            urwid.Divider(),
        ]

        msgs = self.session_mgr.load(session_id)
        counts = Counter(msg.get("role", "") for msg in msgs)
        lines.append(urwid.AttrMap(urwid.Text("Message Stats"), "highlight"))
        lines.append(urwid.Text(f"Total Messages: {len(msgs)}"))
        for role, cnt in sorted(counts.items()):
            lines.append(urwid.Text(f"{role.title()}: {cnt}"))

        self.info_focus = urwid.SimpleFocusListWalker(lines)
        return urwid.ListBox(self.info_focus)

    def update_footer(self):
        prompts = {
            "main": "[↑↓] [enter] load [→] info [v]iew [d]elete [r]ename [n]ew [/] search [esc] exit",
            "preview": "[↑↓] [space] pgdn [esc] back",
            "info": "[tab/↑↓] nav [enter] save [esc] back",
            "delete_confirm": "[y] confirm [n/esc] cancel",
            "search": "[enter] search [esc] cancel",
            "rename": "[enter] confirm [esc] cancel",
            "new": "[enter] create [esc] cancel",
        }
        self.footer_text.set_text(("footer", prompts.get(self.mode, "[esc] back")))

    def return_to_main(self):
        self.refresh_sessions()
        self.mode = "main"
        self.loop.widget = urwid.Frame(
            header=self.header_obj.get_widget(),
            body=urwid.ListBox(self.body_widget),
            footer=self.footer
        )
        self.loop.unhandled_input = self.handle_input
        self.update_footer()

    def build_input_overlay(self, prompt, callback):
        edit = urwid.Edit(("input", f"{prompt}: "), edit_text=self.input_text)
        wrapped = urwid.LineBox(
            urwid.Padding(urwid.AttrMap(edit, "input"), left=1, right=1)
        )
        overlay = urwid.Overlay(
            urwid.Filler(wrapped),
            self.main_frame,
            align="center", width=("relative", 75),
            valign="middle", height=3,
        )
        def handler(key):
            if key == "enter":
                self.input_text = edit.edit_text.strip()
                callback(self.input_text)
                self.return_to_main()
            elif key == "esc":
                self.return_to_main()
        return overlay, handler

    def handle_input(self, key):
        if key == "window resize":
            cols, _ = self.screen.get_cols_rows()
            self.header_obj.resize(cols)
            return

        if self.mode == "main":
            if key in ("up", "k"):
                self.current_index = max(0, self.current_index - 1)
            elif key in ("down", "j"):
                self.current_index = min(len(self.filtered_sessions) - 1, self.current_index + 1)
            elif key == "v":
                self.mode = "preview"
                sid = self.filtered_sessions[self.current_index]["id"]
                self.preview_box = self.build_preview(sid)
                self.loop.widget = urwid.Frame(
                    header=self.header_obj.get_widget(),
                    body=self.preview_box,
                    footer=self.footer
                )
                self.update_footer()
            elif key == "right":
                self.mode = "info"
                sid = self.filtered_sessions[self.current_index]["id"]
                info_view = self.build_editable_info_view(sid)
                self.loop.widget = urwid.Frame(
                    header=self.header_obj.get_widget(),
                    body=info_view,
                    footer=self.footer
                )
                self.update_footer()
            elif key == "/":
                self.mode = "search"
                self.input_text = self.active_query or ""
                overlay, handler = self.build_input_overlay("Search sessions", self.search_sessions)
                self.loop.widget = overlay
                self.loop.unhandled_input = handler
            elif key == "r":
                self.mode = "rename"
                sid = self.filtered_sessions[self.current_index]["id"]
                self.input_text = next((s["name"] for s in self.sessions if s["id"] == sid), "")
                overlay, handler = self.build_input_overlay("Rename session", self.rename_session)
                self.loop.widget = overlay
                self.loop.unhandled_input = handler
            elif key == "n":
                self.mode = "new"
                self.input_text = ""
                overlay, handler = self.build_input_overlay("New session name", self.create_session)
                self.loop.widget = overlay
                self.loop.unhandled_input = handler
            elif key == "d":
                self.mode = "delete_confirm"
                self.update_footer()
            elif key == "enter":
                self.selected_sid = self.filtered_sessions[self.current_index]["id"]
                raise urwid.ExitMainLoop()
            elif key == "esc":
                raise urwid.ExitMainLoop()
            self.body_widget[:] = self.build_session_list()

        elif self.mode == "preview":
            if key == "esc":
                self.return_to_main()
            elif key in (" ", "page down"):
                focus, pos = self.preview_box.get_focus()
                self.preview_box.set_focus(min(len(self.preview_box.body) - 1, pos + 10))

        elif self.mode == "info":
            if key == "esc":
                self.return_to_main()
            elif key in ("tab", "down"):
                pos = self.info_focus.get_focus()[1]
                self.info_focus.set_focus(min(len(self.info_focus) - 1, pos + 1))
            elif key == "up":
                pos = self.info_focus.get_focus()[1]
                self.info_focus.set_focus(max(0, pos - 1))
            elif key == "enter":
                sid = self.filtered_sessions[self.current_index]["id"]
                name = self.edit_widgets["name"].edit_text.strip()
                tags = [t.strip() for t in self.edit_widgets["tags"].edit_text.split(",") if t.strip()]
                summary = self.edit_widgets["summary"].edit_text.strip()
                self.session_mgr.update(sid, "name", name)
                self.session_mgr.update(sid, "tags", tags)
                self.session_mgr.update(sid, "summary", summary)
                self.footer_text.set_text(("footer", f"✓ Saved '{name}'. [esc] to back"))

        elif self.mode == "delete_confirm":
            if key.lower() == "y":
                sid = self.filtered_sessions[self.current_index]["id"]
                self.session_mgr.delete(sid)
                self.return_to_main()
            elif key.lower() in ("n", "esc"):
                self.return_to_main()

        elif self.mode == "search":
            if key.lower() == "esc":
                self.return_to_main()

    def rename_session(self, name):
        if name:
            sid = self.filtered_sessions[self.current_index]["id"]
            self.session_mgr.update(sid, "name", name)
            self.active_query = ""

    def create_session(self, name):
        if name:
            self.session_mgr.create(name=name)
            self.refresh_sessions()

    def search_sessions(self, query):
        self.active_query = query
        self.filtered_sessions = self.session_mgr.search_meta(query)
        self.current_index = 0
        self.body_widget[:] = self.build_session_list()

    def run(self):
        self.loop.run()
        return self.selected_sid


def run_session_manager(theme="default"):
    manager = SessionManager(theme)
    return manager.run()

if __name__ == "__main__":
    sid = run_session_manager("default")
    if sid:
        print(f"Loaded session: {sid}")
