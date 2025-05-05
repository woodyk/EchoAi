#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: showcase.py
# Description: Urwid Showcase TUI demonstrating core widgets & layouts for EchoAI
# Author: Ms. White
# Created: 2025-05-04

"""
Urwid Showcase application for EchoAI.

Drop into echoai/tui/ then run:

    python -m echoai.tui.showcase
        — or —
    /showcase   (after adding a /showcase command in main.py)

Navigation
----------
  ↑/↓ or k/j   Move selection
  ENTER        Open demo
  ESC / q      Back / Quit
"""

from __future__ import annotations

import urwid

from echoai.tui.tui_layout import get_theme_palette, DynamicHeader  # your helpers


class ShowcaseApp:
    """Main menu router for all demo scenes."""

    def __init__(self, theme_name: str = "default") -> None:
        # Theme palette
        self.palette, self.theme = get_theme_palette(theme_name)

        # Menu items: (label, route)
        self.menu_items = [
            ("Basic Widgets", "basic_widgets"),
            ("Columns & Pile", "layout"),
            ("Edit & Forms", "edit"),
            ("ListBox & Scrolling", "listbox"),
            ("Progress Bar", "progress"),
            ("Overlay / Dialog", "overlay"),
            ("Quit", "quit"),
        ]
        self.active_index = 0
        self.previous_widget = None

        # Header / Footer
        self.header_obj = DynamicHeader("Urwid Showcase – Select Demo")
        header = self.header_obj.get_widget()
        self.footer = urwid.AttrMap(
            urwid.Text(self._footer_text("menu"), align="center"), "footer"
        )

        # Body (menu)
        self.body_walker = urwid.SimpleFocusListWalker(self._build_menu())
        body = urwid.ListBox(self.body_walker)

        # Frame / MainLoop
        self.frame = urwid.Frame(header=header, body=body, footer=self.footer)
        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            self.frame,
            self.palette,
            screen=screen,
            unhandled_input=self._handle_menu_input,
        )

    # ── helpers ──────────────────────────────────────────────────────────

    def _footer_text(self, mode: str) -> str:
        return {
            "menu": "[↑↓] select  [enter] open  [q] quit",
            "demo": "[esc] back  [q] quit",
            "progress": "Progress demo – auto‑updates  [esc] back",
        }.get(mode, "")

    def _build_menu(self):
        widgets = []
        for i, (label, _) in enumerate(self.menu_items):
            prefix = "> " if i == self.active_index else "  "
            style = "highlight" if i == self.active_index else "default"
            widgets.append(urwid.AttrMap(urwid.Text(prefix + label), style))
        return widgets

    def _refresh_menu(self):
        self.body_walker[:] = self._build_menu()
        self.footer.base_widget.set_text(self._footer_text("menu"))

    # ── menu input ───────────────────────────────────────────────────────

    def _handle_menu_input(self, key: str):
        if key in ("up", "k"):
            self.active_index = max(0, self.active_index - 1)
            self._refresh_menu()
        elif key in ("down", "j"):
            self.active_index = min(len(self.menu_items) - 1, self.active_index + 1)
            self._refresh_menu()
        elif key == "enter":
            _, route = self.menu_items[self.active_index]
            if route == "quit":
                raise urwid.ExitMainLoop()
            self._open_demo(route)
        elif key.lower() == "q":
            raise urwid.ExitMainLoop()

    # ── scene routing ────────────────────────────────────────────────────

    def _open_demo(self, route: str):
        widget = getattr(self, f"_demo_{route}")()
        self.previous_widget = self.frame.body
        self.frame.body = widget
        self.loop.unhandled_input = getattr(
            self, f"_handle_{route}_input", self._handle_demo_input
        )
        self.footer.base_widget.set_text(
            self._footer_text("progress" if route == "progress" else "demo")
        )

    def _return_to_menu(self):
        self.frame.body = self.previous_widget
        self.loop.unhandled_input = self._handle_menu_input
        self._refresh_menu()

    def _handle_demo_input(self, key: str):
        if key in ("esc", "q"):
            self._return_to_menu()

    # ── demos ────────────────────────────────────────────────────────────

    def _demo_basic_widgets(self):
        buttons = urwid.Columns(
            [
                urwid.Padding(
                    urwid.AttrMap(urwid.Button("OK"), "button"), left=2, right=2
                ),
                urwid.Padding(
                    urwid.AttrMap(urwid.Button("Cancel"), "button"), left=2, right=2
                ),
            ]
        )
        checks = urwid.Pile(
            [urwid.CheckBox("Feature A", state=True), urwid.CheckBox("Feature B")]
        )
        radios = urwid.Pile(
            [
                urwid.RadioButton([], "Option 1", state=True),
                urwid.RadioButton([], "Option 2"),
                urwid.RadioButton([], "Option 3"),
            ]
        )
        pile = urwid.Pile(
            [
                urwid.Text(("highlight", "Basic Widgets")),
                urwid.Divider(),
                buttons,
                urwid.Divider(),
                checks,
                urwid.Divider(),
                radios,
            ]
        )
        return urwid.Filler(urwid.Padding(pile, left=2, right=2), valign="top")

    def _demo_layout(self):
        left = urwid.ListBox(
            urwid.SimpleFocusListWalker([urwid.Text(f"Item {i}") for i in range(1, 11)])
        )
        right = urwid.Pile(
            [
                urwid.Text(("highlight", "Right top"), align="center"),
                urwid.Divider(),
                urwid.Text("Resizable panes showcase.", align="center"),
            ]
        )
        cols = urwid.Columns([(20, left), urwid.LineBox(right)], dividechars=1)
        return cols

    def _demo_edit(self):
        edits = [
            urwid.Edit(("prompt", "Name: ")),
            urwid.Edit(("prompt", "Email: "), edit_text="user@example.com"),
            urwid.Edit(("prompt", "Comment:\n"), multiline=True),
        ]
        pile = urwid.Pile(edits + [urwid.Divider(), urwid.Text("ESC to return.")])
        return urwid.Filler(urwid.Padding(pile, left=2, right=2), valign="top")

    def _demo_listbox(self):
        walker = urwid.SimpleFocusListWalker(
            [urwid.Text(f"Line {i}") for i in range(1, 101)]
        )
        return urwid.ListBox(walker)

    # progress demo with timer
    def _demo_progress(self):
        self._progress = urwid.ProgressBar(
            "progress_normal", "progress_complete", current=0, done=100
        )
        pile = urwid.Pile(
            [
                urwid.Text(("highlight", "Progress Bar")),
                urwid.Divider(),
                self._progress,
            ]
        )
        self._pcnt = 0
        self.loop.set_alarm_in(0.1, self._tick_progress)
        return urwid.Filler(pile, valign="top")

    def _tick_progress(self, loop, _):
        if self._pcnt >= 100:
            return
        self._pcnt += 2
        self._progress.set_completion(self._pcnt)
        loop.set_alarm_in(0.1, self._tick_progress)

    def _handle_progress_input(self, key):
        self._handle_demo_input(key)

    # overlay / dialog demo
    def _demo_overlay(self):
        self._overlay_base = urwid.Filler(
            urwid.Text("Press ENTER for dialog."), valign="top"
        )
        return self._overlay_base

    def _handle_overlay_input(self, key):
        if key == "enter":
            dialog = urwid.LineBox(
                urwid.Filler(
                    urwid.Text("Modal dialog\n(any key to close)"), valign="middle"
                )
            )
            overlay = urwid.Overlay(dialog, self._overlay_base, "center", 40, "middle", 7)
            self.frame.body = overlay
            self.loop.unhandled_input = self._handle_dialog_input
        elif key in ("esc", "q"):
            self._return_to_menu()

    def _handle_dialog_input(self, _key):
        self._return_to_menu()

    # ── run ──────────────────────────────────────────────────────────────

    def run(self):
        self.loop.run()


def run_showcase(theme: str = "default"):
    ShowcaseApp(theme).run()


if __name__ == "__main__":
    run_showcase()

