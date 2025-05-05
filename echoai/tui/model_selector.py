#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: model_selector.py
# Description: Urwid-based AI Model Selector TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-05 19:22:46

import urwid
from echoai.utils.interactor import Interactor
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
        n = len(self.selector.filtered_models)

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
        for idx, name in enumerate(self.selector.filtered_models):
            prefix = '→ ' if idx == self.selector.current else '  '
            item = self.selector.list_walker[idx]
            item.original_widget.set_text(prefix + name)
            item.set_attr_map({None: 'highlight'} if idx == self.selector.current else {None: 'default'})

        # Scroll focus into view
        self.body.set_focus(self.selector.current)
        return None

class ModelSelector:
    def __init__(self, theme="default", default_model=None):
        # load theme
        self.palette, self.theme = get_theme_palette(theme)

        # fetch & sort models alphabetically
        self.models_original = sorted(Interactor().list_models())
        self.active_query = ""
        self.filtered_models = list(self.models_original)

        # default selection
        if default_model and default_model in self.filtered_models:
            self.current = self.filtered_models.index(default_model)
        else:
            self.current = 0

        # header & footer
        self.header_obj = DynamicHeader("Select AI Model")
        header = self.header_obj.get_widget()
        self.footer_text = urwid.Text('', align='center')
        footer = urwid.AttrMap(self.footer_text, 'footer')

        # list walker & custom ListBox
        self.list_walker = urwid.SimpleFocusListWalker(self.build_body())
        body = SelectableListBox(self.list_walker, self)
        # ensure initial default is visible
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
        """Build list items from filtered_models, highlighting the current."""
        items = []
        for idx, name in enumerate(self.filtered_models):
            prefix = "→ " if idx == self.current else "  "
            style = 'highlight' if idx == self.current else 'default'
            items.append(urwid.AttrMap(urwid.Text(prefix + name), style))
        return items

    def update_footer(self):
        self.footer_text.set_text(
            "[↑/↓] move   [PgUp/PgDn/Space] page   [/] search   [Enter] select   [Esc] cancel"
        )

    def build_input_overlay(self, prompt, callback):
        edit = urwid.Edit(("input", f"{prompt}: "), edit_text=self.active_query)
        wrapped = urwid.LineBox(
            urwid.Padding(urwid.AttrMap(edit, 'input'), left=1, right=1)
        )
        overlay = urwid.Overlay(
            urwid.Filler(wrapped),
            self.frame,
            align='center', width=('relative', 75),
            valign='middle', height=3
        )
        def handler(key):
            if key == 'enter':
                self.active_query = edit.edit_text.strip()
                callback(self.active_query)
                self.loop.widget = self.frame
                self.loop.unhandled_input = self.unhandled_input
                self.update_footer()
            elif key == 'esc':
                self.loop.widget = self.frame
                self.loop.unhandled_input = self.unhandled_input
                self.update_footer()
        return overlay, handler

    def search_models(self, query):
        if query:
            q = query.lower()
            self.filtered_models = [m for m in self.models_original if q in m.lower()]
        else:
            self.filtered_models = list(self.models_original)
        # clamp current index
        self.current = min(self.current, len(self.filtered_models) - 1) if self.filtered_models else 0
        self.list_walker[:] = self.build_body()

    def unhandled_input(self, key):
        if key == '/':
            overlay, handler = self.build_input_overlay("Search models", self.search_models)
            self.loop.widget = overlay
            self.loop.unhandled_input = handler
            return
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
        # navigation handled by SelectableListBox

    def run(self):
        self.loop.run()
        return (
            self.filtered_models[self.current] if (self.current is not None and self.filtered_models) else None
        )


def run_model_selector(theme="default", model=None):
    sel = ModelSelector(theme=theme, default_model=model)
    return sel.run()

if __name__ == '__main__':
    choice = run_model_selector('default', "openai:gpt-4o-mini")
    if choice:
        print(f'Selected model: {choice}')

