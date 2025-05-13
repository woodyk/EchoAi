#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: tui_layout.py
# Description: Shared layout helpers for EchoAI TUIs
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-12 23:49:13

import urwid
from echoai.utils.themes import THEMES

def get_theme_palette(theme_name="default"):
    theme = THEMES.get(theme_name, THEMES["default"])
    def hex_to_urwid(name, hexval):
        hexval = hexval.lstrip("#")
        if len(hexval) != 6:
            return (name, 'default', 'default')
        r, g, b = tuple(int(hexval[i:i+2], 16) for i in (0, 2, 4))
        code = 16 + (36 * (r // 43)) + (6 * (g // 43)) + (b // 43)
        return (name, 'default', 'default', '', f'h{code}', '')
    palette = [hex_to_urwid(k, v) for k, v in theme.items()]
    return palette, theme

class BevelBox(urwid.WidgetDecoration):
    def __init__(self, original_widget, title=None, title_attr='popup_title'):
        self.original_widget = original_widget
        self.title = title
        self.title_attr = title_attr

    def selectable(self):
        return self.original_widget.selectable()

    def keypress(self, size, key):
        return self.original_widget.keypress(size, key)

    def render(self, size, focus=False):
        # Determine dimensions
        if isinstance(size, tuple):
            maxcol = size[0]
            size_inner = (maxcol - 2,)
            if len(size) == 2:
                maxrow = size[1]
                size_inner = (maxcol - 2, maxrow - 2)
        else:
            maxcol = size
            size_inner = (maxcol - 2,)

        # Prepare top border with title
        if self.title:
            title_str = f" {self.title} "
            centered = title_str.center(maxcol - 2, "─")
            top = urwid.Text((self.title_attr, f"╭{centered}╮"))
        else:
            top = urwid.Text(('border', f"╭{'─' * (maxcol - 2)}╮"))

        bottom = urwid.Text(('border', f"╰{'─' * (maxcol - 2)}╯"))

        # Padding and layout
        inner = urwid.Padding(self.original_widget, left=1, right=1)
        layout = urwid.Pile([
            ('pack', top),
            ('weight', 1, inner),
            ('pack', bottom),
        ])
        return layout.render(size, focus)

class BevelBox(urwid.WidgetDecoration):
    def __init__(self, original_widget, title=None, title_attr='popup_title'):
        self.original_widget = original_widget
        self.title = title
        self.title_attr = title_attr

    def selectable(self):
        return self.original_widget.selectable()

    def keypress(self, size, key):
        return self.original_widget.keypress(size, key)

    def render(self, size, focus=False):
        if isinstance(size, tuple) and len(size) == 2:
            maxcol, maxrow = size
        else:
            maxcol = size[0]

        if self.title:
            title_str = f" {self.title} "
            centered = title_str.center(maxcol - 2, "─")
            top = urwid.Text((self.title_attr, f"╭{centered}╮"))
        else:
            top = urwid.Text(('border', f"╭{'─' * (maxcol - 2)}╮"))

        bottom = urwid.Text(('border', f"╰{'─' * (maxcol - 2)}╯"))

        padded = urwid.Padding(self.original_widget, left=1, right=1)
        layout = urwid.Pile([
            ('pack', top),
            ('weight', 1, padded),
            ('pack', bottom),
        ])

        return layout.render(size, focus)


class DynamicHeader:
    def __init__(self, title=""):
        self.title = title
        self.top = urwid.Text("")
        self.mid = urwid.Text("")
        self.bot = urwid.Text("")
        self.widget = urwid.Pile([
            urwid.AttrMap(self.top, 'prompt'),
            urwid.AttrMap(self.mid, 'prompt'),
            urwid.AttrMap(self.bot, 'prompt'),
        ])
        self.resize()

    def resize(self, width=None):
        if width is None:
            width = urwid.raw_display.Screen().get_cols_rows()[0]
        self.top.set_text("╭" + "─" * (width - 2) + "╮")
        self.mid.set_text(f"│{self.title.ljust(width - 2)}│")
        self.bot.set_text("╰" + "─" * (width - 2) + "╯")

    def get_widget(self):
        return self.widget
