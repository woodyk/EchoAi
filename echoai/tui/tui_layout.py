#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: tui_layout.py
# Description: Shared layout helpers for EchoAI TUIs
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-05 19:23:57

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
        self.top.set_text("┌" + "─" * (width - 2) + "┐")
        self.mid.set_text(f"│{self.title.ljust(width - 2)}│")
        self.bot.set_text("└" + "─" * (width - 2) + "┘")

    def get_widget(self):
        return self.widget

