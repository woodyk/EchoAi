#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: theme_selector.py
# Description: Urwid-based Theme Selector TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-05 19:24:24

import urwid
from echoai.utils.themes import THEMES
from echoai.tui.tui_layout import get_theme_palette, DynamicHeader

class SelectableListBox(urwid.ListBox):
    """
    Custom ListBox that intercepts navigation keys to manually update
    the highlighted selection and ensure consistent single-step movement
    within the current view until scrolling is necessary.
    """
    def __init__(self, walker, selector):
        super().__init__(walker)
        self.selector = selector

    def keypress(self, size, key):
        maxcol, maxrow = size
        page = max(1, maxrow - 4)
        n = len(self.selector.items)

        if key in ('up', 'k'):
            self.selector.current = max(0, self.selector.current - 1)
        elif key in ('down', 'j'):
            self.selector.current = min(n - 1, self.selector.current + 1)
        elif key == 'page up':
            self.selector.current = max(0, self.selector.current - page)
        elif key in ('page down', ' '):
            self.selector.current = min(n - 1, self.selector.current + page)
        else:
            return super().keypress(size, key)

        # Update visible items' text and style
        for idx, name in enumerate(self.selector.items):
            prefix = '→ ' if idx == self.selector.current else '  '
            item = self.selector.list_walker[idx]
            item.original_widget.set_text(prefix + name)
            item.set_attr_map({None: 'highlight'} if idx == self.selector.current else {None: 'default'})

        # Scroll focus into view
        self.body.set_focus(self.selector.current)
        return None

class ThemeSelector:
    def __init__(self, theme="default"):
        # load palette & theme
        self.palette, self.theme = get_theme_palette(theme)

        # available theme names
        self.items = sorted(THEMES.keys())

        # default selection based on current theme
        if theme in self.items:
            self.current = self.items.index(theme)
        else:
            self.current = 0

        # header & footer
        self.header_obj = DynamicHeader("Select Theme")
        header = self.header_obj.get_widget()
        self.footer_text = urwid.Text('', align='center')
        footer = urwid.AttrMap(self.footer_text, 'footer')

        # list walker & custom ListBox
        self.list_walker = urwid.SimpleFocusListWalker(self.build_body())
        body = SelectableListBox(self.list_walker, self)
        # ensure default is visible
        self.list_walker.set_focus(self.current)

        # main frame & loop
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

    def build_body(self):
        """Build list items from self.items, highlighting current."""
        widgets = []
        for idx, name in enumerate(self.items):
            prefix = '→ ' if idx == self.current else '  '
            style = 'highlight' if idx == self.current else 'default'
            widgets.append(urwid.AttrMap(urwid.Text(prefix + name), style))
        return widgets

    def update_footer(self):
        self.footer_text.set_text(
            '[↑/↓] move   [PgUp/PgDn/Space] page   [Enter] select   [Esc] cancel'
        )

    def unhandled_input(self, key):
        if key == 'enter':
            raise urwid.ExitMainLoop()
        if key == 'esc':
            self.current = None
            raise urwid.ExitMainLoop()
        if key == 'window resize':
            cols, _ = self.screen.get_cols_rows()
            self.header_obj.resize(cols)
            self.update_footer()
            return
        # navigation is handled in SelectableListBox

    def run(self):
        self.loop.run()
        return self.items[self.current] if (self.current is not None) else None


def run_theme_selector(theme="default"):
    sel = ThemeSelector(theme=theme)
    return sel.run()

if __name__ == '__main__':
    choice = run_theme_selector('default')
    if choice:
        print(f'Selected theme: {choice}')
