#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: file_selector.py
# Description: Urwid-based File Browser TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-XX
# Modified: 2025-05-03 21:16:14

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
        # define page size as rows minus header/footer (3+1)
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

        # refresh visuals
        for idx, entry in enumerate(self.selector.entries):
            text = entry.name + ('/' if entry.is_dir() and entry.name != '..' else '')
            prefix = '→ ' if idx == self.selector.current else '  '
            widget = self.selector.walker[idx]
            widget.original_widget.set_text(prefix + text)
            widget.set_attr_map({None: 'highlight'} if idx == self.selector.current else {None: 'default'})
        # ensure focus
        self.body.set_focus(self.selector.current)
        return None

class FileSelector:
    def __init__(self, theme_name="default", path=None):
        # Load theme
        self.palette, self.theme = get_theme_palette(theme_name)

        # Start directory
        self.current_dir = Path(path or os.getcwd())
        # List of Path entries (including a ".." at index 0)
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
        # position focus on current
        self.walker.set_focus(self.current)

    def update_entries(self):
        """Scan current_dir and refresh self.entries (with '..' first)."""
        # always include parent link
        parent = self.current_dir.parent if self.current_dir.parent != self.current_dir else None
        entries = []
        if parent:
            # represent as Path('..') for logic
            entries.append(Path('..'))
        # list directories then files
        for p in sorted(self.current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            entries.append(p)
        self.entries = entries
        # clamp index
        self.current = min(self.current, len(self.entries)-1)

    def build_body(self):
        """Build walker items from self.entries, honoring self.current."""
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
        """Rebuild walker after changing directory."""
        self.update_entries()
        # refresh walker contents
        self.walker[:] = self.build_body()
        self.walker.set_focus(self.current)
        # update header text
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

        if key in ('enter',):
            choice = self.entries[self.current]
            # handle ".."
            if choice.name == '..':
                # go up
                self.current_dir = self.current_dir.parent
                self.update_list()
                return
            # directory
            if choice.is_dir():
                self.current_dir = choice
                self.update_list()
                return
            # file
            self.selected_path = str(choice.resolve())
            raise urwid.ExitMainLoop()

        if key in ('esc',):
            self.selected_path = None
            raise urwid.ExitMainLoop()

    def run(self):
        self.loop.run()
        return self.selected_path

def run_file_selector(theme="default", path=None):
    sel = FileSelector(theme, path)
    return sel.run()

if __name__ == "__main__":
    path = run_file_selector("default")
    if path:
        print(path)

