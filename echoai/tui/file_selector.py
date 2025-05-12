#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: file_selector.py
# Description: Urwid-based File Browser TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-XX
# Modified: 2025-05-11 15:53:29

import os
from pathlib import Path
import urwid

from echoai.tui.tui_layout import get_theme_palette, DynamicHeader

class SelectableListBox(urwid.ListBox):
    """
    Custom ListBox that intercepts navigation keys to update the highlighted
    selection one step at a time, scrolling only when the cursor hits the edge.
    """
    def __init__(self, walker, selector):
        super().__init__(walker)
        self.selector = selector

    def keypress(self, size, key):
        maxcol, maxrow = size
        page = max(1, maxrow - 4)
        n = len(self.selector.entries)

        if key in ('up',):
            self.selector.current = max(0, self.selector.current - 1)
        elif key in ('down',):
            self.selector.current = min(n - 1, self.selector.current + 1)
        elif key in ('page up',):
            self.selector.current = max(0, self.selector.current - page)
        elif key in ('page down', ' '):
            self.selector.current = min(n - 1, self.selector.current + page)
        else:
            return super().keypress(size, key)

        for idx, entry in enumerate(self.selector.entries):
            text = entry.name + ('/' if entry.is_dir() and entry.name != '..' else '')
            prefix = '→ ' if idx == self.selector.current else '  '
            widget = self.selector.walker[idx]
            widget.original_widget.set_text(prefix + text)
            widget.set_attr_map({None: 'highlight'} if idx == self.selector.current else {None: 'default'})
        self.body.set_focus(self.selector.current)
        return None

class FileSelector:
    def __init__(self, theme="default", path=None):
        # Load theme palette and store theme name
        self.palette, self.theme = get_theme_palette(theme)

        # Start directory
        self.current_dir = Path(path or os.getcwd())
        self.entries = []
        self.current = 0
        self.selected_path = None

        # Header / footer
        self.header_obj = DynamicHeader(f"Select File – {self.current_dir}")
        header = self.header_obj.get_widget()
        self.footer_text = urwid.Text('', align='center')
        footer = urwid.AttrMap(self.footer_text, 'footer')

        # Build initial list
        self.update_entries()
        self.walker = urwid.SimpleFocusListWalker(self.build_body())
        body = SelectableListBox(self.walker, self)

        # Frame & loop
        self.frame = urwid.Frame(header=header, body=body, footer=footer)
        self.screen = urwid.raw_display.Screen()
        self.screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            self.frame,
            self.palette,
            screen=self.screen,
            unhandled_input=self.unhandled_input
        )

        self.update_footer()
        self.walker.set_focus(self.current)

    def update_entries(self):
        parent = self.current_dir.parent if self.current_dir.parent != self.current_dir else None
        entries = []
        if parent:
            entries.append(Path('..'))
        for p in sorted(self.current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            entries.append(p)
        self.entries = entries
        self.current = min(self.current, len(self.entries) - 1)

    def build_body(self):
        items = []
        for idx, entry in enumerate(self.entries):
            name = entry.name if entry.name != '' else '..'
            display = name + ('/' if entry.is_dir() and name != '..' else '')
            prefix = '→ ' if idx == self.current else '  '
            txt = urwid.Text(prefix + display)
            attr = 'highlight' if idx == self.current else 'default'
            items.append(urwid.AttrMap(txt, attr))
        return items

    def update_list(self):
        self.update_entries()
        self.walker[:] = self.build_body()
        self.walker.set_focus(self.current)
        self.header_obj.title = f"Select File – {self.current_dir}"
        cols, _ = self.screen.get_cols_rows()
        self.header_obj.resize(cols)

    def update_footer(self):
        self.footer_text.set_text(
            "[↑↓] move   [PgUp/PgDn/Space] page   [Enter] open/select   [Esc] cancel"
        )

    def unhandled_input(self, key):
        if key == 'window resize':
            cols, _ = self.screen.get_cols_rows()
            self.header_obj.resize(cols)
            return

        if key == 'enter':
            choice = self.entries[self.current]
            if choice.name == '..':
                self.current_dir = self.current_dir.parent
                self.update_list()
                return
            if choice.is_dir():
                self.current_dir = choice
                self.update_list()
                return
            self.selected_path = str(choice.resolve())
            raise urwid.ExitMainLoop()

        if key == 'esc':
            self.selected_path = None
            raise urwid.ExitMainLoop()

    def run(self):
        self.loop.run()
        return self.selected_path

def run_file_selector(theme="default", path=None):
    sel = FileSelector(theme=theme, path=path)
    return sel.run()

if __name__ == "__main__":
    path = run_file_selector("default")
    if path:
        print(path)

