#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: cyberpunk_claud.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-05-12 20:14:49
# Modified: 2025-05-13 15:48:03

import os
import urwid
import re
import random
import time

from pathlib import Path

from .tools.task_manager import task_list, task_add, task_update, task_delete
from .tui.tui_layout import BevelBox, DynamicHeader

from interactor import Interactor, Session
from .utils.themes import THEMES
from .utils.memory import Memory

def detect_color_mode():
    """Return color mode: 'truecolor', '256', or '16'."""
    colorterm = os.environ.get("COLORTERM", "").lower()
    term = os.environ.get("TERM", "").lower()

    if "truecolor" in colorterm or "24bit" in colorterm:
        return "truecolor"
    elif "256color" in term:
        return "256"
    else:
        return "16"

def padded_overlay_body(widget, padding=(2, 2, 1, 1)):
    """Apply standard overlay padding: (left, right, top, bottom)."""
    left, right, top, bottom = padding
    return urwid.Padding(widget, left=left, right=right)

class ThemeManager:
    """Manage the application themes and color palette"""
    def __init__(self, default_theme_name="default"):
        self.themes = THEMES
        self.current_theme_name = default_theme_name
        self.current_theme = self.themes[default_theme_name]
        self.color_mode = detect_color_mode()  # NEW
        self.callbacks = []
        print(f"[ThemeManager] detected color mode: {self.color_mode}")
        print(f"[Palette] mode={self.color_mode}")

       
    def register_theme_change_callback(self, callback):
        """Register a callback to be called when theme changes"""
        self.callbacks.append(callback)
        
    def get_current_theme(self):
        """Return the current theme dict"""
        return self.current_theme
    
    def get_current_theme_name(self):
        """Return the current theme name"""
        return self.current_theme_name
    
    def set_theme(self, theme_name):
        """Set the current theme by name"""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            # Notify all registered callbacks about theme change
            for callback in self.callbacks:
                callback(self.current_theme)
            return True
        return False
    
    def get_theme_names(self):
        """Return a list of all available theme names"""
        return list(self.themes.keys())

    @staticmethod
    def hex_to_urwid_attr(hex_color: str, mode: str) -> str:
        """Convert HEX (#RRGGBB) to Urwid-compatible color string."""

        standard_16 = {
            (0x00, 0x00, 0x00): 'black',
            (0x80, 0x00, 0x00): 'dark red',
            (0x00, 0x80, 0x00): 'dark green',
            (0x80, 0x80, 0x00): 'brown',
            (0x00, 0x00, 0x80): 'dark blue',
            (0x80, 0x00, 0x80): 'dark magenta',
            (0x00, 0x80, 0x80): 'dark cyan',
            (0xc0, 0xc0, 0xc0): 'light gray',
            (0x80, 0x80, 0x80): 'dark gray',
            (0xff, 0x00, 0x00): 'light red',
            (0x00, 0xff, 0x00): 'light green',
            (0xff, 0xff, 0x00): 'yellow',
            (0x00, 0x00, 0xff): 'light blue',
            (0xff, 0x00, 0xff): 'light magenta',
            (0x00, 0xff, 0xff): 'light cyan',
            (0xff, 0xff, 0xff): 'white',
        }

        def nearest_named(r, g, b):
            return min(
                standard_16.items(),
                key=lambda c: (c[0][0] - r)**2 + (c[0][1] - g)**2 + (c[0][2] - b)**2
            )[1]

        match = re.fullmatch(r"#?([0-9a-fA-F]{6})", hex_color.strip())
        if not match:
            raise ValueError(f"Invalid HEX: {hex_color}")
        r, g, b = (int(match[1][i:i+2], 16) for i in (0, 2, 4))

        if mode == "truecolor":
            return f"#{match[1]}"
        elif mode == "16":
            return nearest_named(r, g, b)
        elif mode in ("256", "88"):
            def to_cube(v, levels):
                scale = [int(round(x * 255 / (levels - 1))) for x in range(levels)]
                return min(scale, key=lambda s: abs(s - v))

            levels = 6 if mode == "256" else 4
            tags = ['0', '5f', '87', 'af', 'd7', 'ff'] if mode == "256" else ['0', '8b', 'cd', 'ff']
            hex_tags = ['0', '6', '8', 'a', 'd', 'f'] if mode == "256" else ['0', '8', 'c', 'f']

            cube_r = to_cube(r, levels)
            cube_g = to_cube(g, levels)
            cube_b = to_cube(b, levels)

            def tag(val):
                for i, t in enumerate(tags):
                    if int(t, 16) == val:
                        return hex_tags[i]
                return '0'

            return f"#{tag(cube_r)}{tag(cube_g)}{tag(cube_b)}"

        raise ValueError(f"Unsupported mode: {mode}")

    def hex_to_urwid_index(self, hex_color: str) -> str:
        """Convert a HEX color string (#RRGGBB) to the nearest 256-color terminal palette index."""
        import re

        match = re.fullmatch(r"#?([0-9a-fA-F]{6})", hex_color.strip())
        if not match:
            raise ValueError(f"Invalid HEX color: {hex_color}")

        r, g, b = (int(match.group(1)[i:i+2], 16) for i in (0, 2, 4))

        # Grayscale
        if r == g == b:
            if r < 8: return "16"
            if r > 248: return "231"
            return str(round(((r - 8) / 247) * 24) + 232)

        # 6x6x6 color cube mapping
        def to_index(c):
            return int(round(c / 255 * 5))

        ri, gi, bi = to_index(r), to_index(g), to_index(b)
        return str(16 + 36 * ri + 6 * gi + bi)

    
    def get_urwid_palette(self):
        """Convert the current theme to urwid palette format"""
        theme = self.current_theme

        def resolve(key, fallback="white"):
            val = theme.get(key)
            if not val or not val.startswith("#"):
                return val or fallback
            try:
                return self.hex_to_urwid_attr(val, self.color_mode)
            except Exception:
                return fallback
        
        palette = [
            ('background', 'default', 'default'),
            ('header', resolve('title', 'yellow'), 'dark blue'),
            ('footer', resolve('footer', 'light cyan'), 'dark blue'),
            ('primary', resolve('prompt', 'light green'), 'default'),
            ('secondary', resolve('highlight', 'light magenta'), 'default'),
            ('highlight', resolve('highlight', 'yellow'), 'dark red'),
            ('warning', resolve('warning', 'light red'), 'default'),
            ('border', resolve('dim', 'dark cyan'), 'default'),
            ('button', 'black', resolve('success', 'light green')),
            ('button_focused', 'black', resolve('highlight', 'yellow')),
            ('edit', resolve('input', 'light green'), 'default'),
            ('edit_focused', 'black', resolve('input', 'light green')),
            ('popup', resolve('title', 'light cyan'), 'default'),
            ('popup_border', resolve('footer', 'light cyan'), 'default'),
            ('popup_title', resolve('highlight', 'yellow'), 'default'),
            ('progress', 'black', resolve('info', 'dark green')),
            ('progress_complete', 'black', resolve('success', 'light green')),
            ('selected', 'black', resolve('highlight', 'light magenta')),
            ('disabled', resolve('dim', 'dark gray'), 'default'),
        ]
        # Temporary permenant theme until we get the truecolor worked out
        URWID_SAFE_PALETTE = [
            # General UI
            ('background',         'default',       'default'),
            ('header',             'yellow',        'default'),
            ('footer',             'light gray',    'default'),
            ('primary',            'light green',   'default'),
            ('secondary',          'light magenta', 'default'),
            ('highlight',          'black',         'light cyan'),   # Used for selection/focus
            ('warning',            'light red',     'default'),
            ('border',             'dark gray',     'default'),
            ('disabled',           'dark gray',     'default'),

            # Buttons and focusable widgets
            ('button',            'light gray',  'default'),
            ('button_focused',    'black',       'light cyan'),
            ('selected',          'black',       'light cyan'),

            # Edit fields
            ('edit',               'light gray',    'default'),
            ('edit_focused',       'black',         'light green'),

            # Popups
            ('popup',              'light cyan',    'default'),
            ('popup_border',       'light gray',    'default'),
            ('popup_title',        'yellow',        'default'),

            # Progress bar
            ('progress',           'black',         'dark green'),
            ('progress_complete',  'black',         'light green'),

            # Used as the base/default style
            ('default',            'light gray',    'default'),
        ]


        palette = URWID_SAFE_PALETTE

        return palette

class ProgressBar(urwid.ProgressBar):
    """Custom progress bar with cyberpunk styling"""
    def __init__(self, normal, complete, current=0, done=100):
        super().__init__(normal, complete, current, done)

class MessageLog:
    """Class to manage terminal messages with timestamps"""
    def __init__(self, widget):
        self.widget = widget
        self.messages = []
    
    def add_message(self, message, style='primary'):
        timestamp = time.strftime("[%H:%M:%S]", time.localtime())
        full_message = f"{timestamp} {message}"
        self.messages.append((style, full_message))
        self._update_widget()
    
    def _update_widget(self):
        text = "\n".join([msg[1] for msg in self.messages])
        self.widget.set_text([(msg[0], msg[1] + "\n") for msg in self.messages])

class NetworkAnalysisOverlay(urwid.WidgetWrap):
    """Network analysis overlay window"""
    def __init__(self, callback):
        self.close_callback = callback
        
        # Create an animated progress bar
        self.progress = ProgressBar('progress', 'progress_complete')
        
        # Network stats
        self.stat_text = urwid.Text([
            ('secondary', "ANALYZING NETWORK TRAFFIC...\n\n"),
            ('primary', "PORTS SCANNED: 0/1024\n"),
            ('primary', "ACTIVE CONNECTIONS: 0\n"),
            ('primary', "DATA PACKETS CAPTURED: 0\n"),
            ('primary', "POTENTIAL VULNERABILITIES: 0\n")
        ])
        
        # Close button
        close_button = urwid.Button("CLOSE")
        urwid.connect_signal(close_button, 'click', self.close)
        close_button = urwid.AttrMap(close_button, 'button', focus_map='button_focused')
        
        # Layout
        pile = urwid.Pile([
            ('pack', self.stat_text),
            ('pack', urwid.Divider('-')),
            ('pack', self.progress),
            ('pack', urwid.Divider()),
            ('pack', close_button)
        ])
        
        fill = urwid.Filler(pile, 'top')
        linebox = urwid.LineBox(fill, title=" NETWORK ANALYSIS ", title_attr='popup_title')
        self._w = urwid.AttrMap(linebox, 'popup_border')
        
        # Start the animation
        self.loop = None  # Will be set later
        self.progress_value = 0
        self.scanned_ports = 0
        self.connections = 0
        self.packets = 0
        self.vulns = 0
    
    def start_animation(self, loop):
        self.loop = loop
        self.loop.set_alarm_in(0.1, self.update_progress)
    
    def update_progress(self, loop, user_data):
        # Update progress
        self.progress_value += random.randint(1, 5)
        if self.progress_value >= 100:
            self.progress_value = 100
        
        # Update stats with random cyberpunk-y values
        self.scanned_ports = int(self.progress_value * 10.24)
        self.connections = random.randint(1, 10) if self.progress_value > 20 else 0
        self.packets = int(self.progress_value * random.randint(10, 50))
        if self.progress_value > 60:
            self.vulns = random.randint(1, 5)
        
        # Update widgets
        self.progress.set_completion(self.progress_value)
        self.stat_text.set_text([
            ('secondary', "ANALYZING NETWORK TRAFFIC...\n\n"),
            ('primary', f"PORTS SCANNED: {self.scanned_ports}/1024\n"),
            ('primary', f"ACTIVE CONNECTIONS: {self.connections}\n"),
            ('primary', f"DATA PACKETS CAPTURED: {self.packets}\n"),
            ('warning' if self.vulns > 0 else 'primary', 
             f"POTENTIAL VULNERABILITIES: {self.vulns}\n")
        ])
        
        # Continue animation
        if self.progress_value < 100:
            self.loop.set_alarm_in(0.1, self.update_progress)
    
    def close(self, button):
        self.close_callback()


class SessionManagerOverlay(urwid.WidgetWrap):
    pass

class ToolManagerOverlay(urwid.WidgetWrap):
    pass

class FileExplorerOverlay(urwid.WidgetWrap):
    def __init__(self, callback, start_path=None):
        self.callback = callback
        self.current_path = Path(start_path or os.getcwd()).resolve()
        self.entries = []
        self.focus_index = 0

        self.header = urwid.Text("", align='center')
        self.status = urwid.Text("", align='left')

        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.update_entries()

        container = urwid.Pile([
            ('pack', self.header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', urwid.Text(" [↑↓] move   [Enter] open/select   [Esc] cancel", align='center')),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(container), title=" FILE EXPLORER ", title_attr='popup_title')
        super().__init__(urwid.AttrMap(boxed, 'popup_border'))

    def update_entries(self):
        try:
            children = sorted(self.current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            if self.current_path.parent != self.current_path:
                self.entries = [self.current_path.parent] + children
            else:
                self.entries = children
        except Exception as e:
            self.status.set_text(f"Error: {e}")
            self.entries = []

        self.focus_index = 0
        self.header.set_text(('highlight', f"{self.current_path}"))
        self.walker.clear()

        for idx, path in enumerate(self.entries):
            label = path.name if path.name != '' else str(path)
            if path == self.current_path.parent:
                label = '..'
            display = label + ('/' if path.is_dir() and label != '..' else '')
            prefix = '→ ' if idx == self.focus_index else '  '
            text = urwid.Text(prefix + display)
            attr = 'highlight' if idx == self.focus_index else 'default'
            self.walker.append(urwid.AttrMap(text, attr))

        self.listbox.focus_position = self.focus_index

    def keypress(self, size, key):
        if key in ('up',):
            self.focus_index = max(0, self.focus_index - 1)
        elif key in ('down',):
            self.focus_index = min(len(self.entries) - 1, self.focus_index + 1)
        elif key == 'enter':
            selected = self.entries[self.focus_index]
            if selected.name == '..' or selected.is_dir():
                self.current_path = selected.resolve()
                self.update_entries()
                return
            elif selected.is_file():
                self.callback(action='file_selected', message=str(selected.resolve()))
                return
        elif key == 'esc':
            self.callback(message="File selection cancelled.")
            return
        else:
            return super().keypress(size, key)

        # Redraw entries with new focus
        for i, entry in enumerate(self.entries):
            label = entry.name if entry.name != '' else str(entry)
            if entry == self.current_path.parent:
                label = '..'
            display = label + ('/' if entry.is_dir() and label != '..' else '')
            prefix = '→ ' if i == self.focus_index else '  '
            self.walker[i].original_widget.set_text(prefix + display)
            self.walker[i].set_attr_map({None: 'highlight' if i == self.focus_index else 'default'})
        self.listbox.focus_position = self.focus_index

    def _cancel(self, _button):
        self.callback(message="File selection cancelled.")

class MemoryManagerOverlay(urwid.WidgetWrap):
    pass

class PromptManagerOverlay(urwid.WidgetWrap):
    pass

class SettingsOverlay(urwid.WidgetWrap):
    pass

class ModelSelectorOverlay(urwid.WidgetWrap):
    def __init__(self, callback, models, default_model=None):
        self.callback = callback
        self.models_original = sorted(models)
        self.filtered_models = list(self.models_original)
        self.active_query = ""
        self.focus_index = 0

        if default_model in self.filtered_models:
            self.focus_index = self.filtered_models.index(default_model)

        self.status = urwid.Text("")
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)
        self.update_model_list()

        header = urwid.Text(('highlight', ""), align='center')
        footer = urwid.Text(" [↑↓] move   [/] search   [Enter] select   [Esc] cancel", align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" MODEL SELECTOR ", title_attr='popup_title')
        super().__init__(urwid.AttrMap(boxed, 'popup_border'))

    def update_model_list(self):
        self.walker.clear()
        for idx, name in enumerate(self.filtered_models):
            prefix = "→ " if idx == self.focus_index else "  "
            style = 'highlight' if idx == self.focus_index else 'default'
            self.walker.append(urwid.AttrMap(urwid.Text(prefix + name), style))
        if self.filtered_models:
            self.listbox.focus_position = self.focus_index

    def keypress(self, size, key):
        if key in ('up', 'k'):
            self.focus_index = max(0, self.focus_index - 1)
        elif key in ('down', 'j'):
            self.focus_index = min(len(self.filtered_models) - 1, self.focus_index + 1)
        elif key == '/':
            self.prompt_search()
            return
        elif key == 'enter':
            if self.filtered_models:
                selected = self.filtered_models[self.focus_index]
                self.callback(action='model_selected', message=selected)
            else:
                self.callback(message="No models available.")
            return
        elif key == 'esc':
            self.callback(message="Model selection cancelled.")
            return
        else:
            return super().keypress(size, key)

        # Redraw list
        for idx, name in enumerate(self.filtered_models):
            prefix = "→ " if idx == self.focus_index else "  "
            style = 'highlight' if idx == self.focus_index else 'default'
            self.walker[idx].original_widget.set_text(prefix + name)
            self.walker[idx].set_attr_map({None: style})
        self.listbox.focus_position = self.focus_index

    def prompt_search(self):
        edit = urwid.Edit(("input", "Search: "), edit_text=self.active_query)
        edit_map = urwid.AttrMap(edit, 'input')
        linebox = urwid.LineBox(urwid.Padding(edit_map, left=1, right=1))

        def handle_search_input(key):
            if key == 'enter':
                query = edit.edit_text.strip()
                self.apply_search(query)
                self._w = self.overlay  # restore original overlay
            elif key == 'esc':
                self._w = self.overlay  # cancel search

        self.overlay = self._w
        self._w = urwid.Overlay(
            urwid.Filler(linebox),
            self.overlay,
            align='center', width=('relative', 50),
            valign='middle', height=3
        )
        self._w = urwid.AttrMap(self._w, 'popup_border')
        urwid.connect_signal(edit, 'change', lambda *_: None)
        self._w.keypress = handle_search_input

    def apply_search(self, query):
        self.active_query = query
        if query:
            q = query.lower()
            self.filtered_models = [m for m in self.models_original if q in m.lower()]
        else:
            self.filtered_models = list(self.models_original)
        self.focus_index = 0
        self.update_model_list()

class TaskManagerOverlay(urwid.WidgetWrap):
    def __init__(self, callback):
        self.close_callback = callback
        self.tasks = []
        self.filtered = []
        self.focus_index = 0
        self.mode = "view"
        self.query = ""
        self.sort_asc = False
        self.show_done = True
        self.edit_widgets = {}

        self.status = urwid.Text("")
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.load_tasks()
        self.render_tasks()

        #header = urwid.Text(('highlight', " TASK MANAGER "), align='center')
        header = urwid.Text(('highlight', ""), align='center')
        footer = urwid.Text(" [↑↓] move   [n] new   [d] delete   [m] mark   [/] search   [c] completed   [s] sort   [Enter] edit   [Esc] exit", align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, urwid.Padding(self.listbox, left=2, right=2)),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" TASK MANAGER ", title_attr='popup_title')
        self._w = urwid.AttrMap(boxed, 'popup_border')

    def load_tasks(self):
        result = task_list()
        self.tasks = result.get('result', [])
        self.apply_filters()

    def apply_filters(self):
        tasks = self.tasks
        if not self.show_done:
            tasks = [t for t in tasks if t.get("status", "").lower() != "done"]
        if self.query:
            q = self.query.lower()
            tasks = [t for t in tasks if q in (t.get("content", "") + t.get("notes", "") + t.get("tag", "")).lower()]
        tasks.sort(key=lambda t: t.get("created", ""), reverse=not self.sort_asc)
        self.filtered = tasks
        if self.filtered:
            self.focus_index = min(self.focus_index, len(self.filtered) - 1)
        else:
            self.focus_index = 0

    def render_tasks(self):
        self.walker.clear()
        for i, t in enumerate(self.filtered):
            label = (t.get("content") or "").strip().splitlines()[0][:50]
            tag = t.get("tag", "")
            sid = t.get("id", "")
            status = t.get("status", "")
            line = f"{label} [{status}]{' ' + tag if tag else ''} ({sid})"
            prefix = "→ " if i == self.focus_index else "  "
            style = 'highlight' if i == self.focus_index else 'default'
            self.walker.append(urwid.AttrMap(urwid.Text(prefix + line), style))
        if self.filtered:
            self.listbox.focus_position = self.focus_index

    def keypress(self, size, key):
        if self.mode == "view":
            if key in ("up", "k"):
                self.focus_index = max(0, self.focus_index - 1)
            elif key in ("down", "j"):
                self.focus_index = min(len(self.filtered) - 1, self.focus_index + 1)
            elif key == "n":
                self.prompt_new()
                return
            elif key == "d":
                self.mode = "delete"
                self.status.set_text("Confirm delete [y/n]")
                return
            elif key == "m":
                self.toggle_status()
                return
            elif key == "/":
                self.prompt_search()
                return
            elif key == "c":
                self.show_done = not self.show_done
            elif key == "s":
                self.sort_asc = not self.sort_asc
            elif key == "enter":
                self.enter_edit_mode()
                return
            elif key == "esc":
                self.close_callback(message="Task Manager closed.")
                return
            self.apply_filters()
            self.render_tasks()

        elif self.mode == "delete":
            if key.lower() == "y":
                task_delete(self.filtered[self.focus_index]["id"])
                self.load_tasks()
                self.render_tasks()
                self.status.set_text("✓ Deleted")
                self.mode = "view"
            elif key.lower() in ("n", "esc"):
                self.status.set_text("")
                self.mode = "view"

        elif self.mode == "edit":
            if key in ("tab", "down"):
                pos = self.edit_focus.get_focus()[1]
                self.edit_focus.set_focus(min(len(self.edit_focus) - 1, pos + 1))
            elif key == "up":
                pos = self.edit_focus.get_focus()[1]
                self.edit_focus.set_focus(max(0, pos - 1))
            elif key == "enter":
                self.save_edits()
            elif key == "esc":
                self.mode = "view"
                self.load_tasks()
                self.render_tasks()
                self._w = self.original_overlay

        elif self.mode == "new":
            if key == "enter":
                text = self.new_task_edit.edit_text.strip()
                if text:
                    task_add(text)
                    self.status.set_text("✓ Task added")
                self.mode = "view"
                self._w = self.original_overlay
                self.load_tasks()
                self.render_tasks()
            elif key == "esc":
                self.mode = "view"
                self._w = self.original_overlay
                self.status.set_text("")

        elif self.mode == "search":
            if key == "enter":
                self.query = self.search_edit.edit_text.strip()
                self.mode = "view"
                self._w = self.original_overlay
                self.load_tasks()
                self.render_tasks()
            elif key == "esc":
                self.mode = "view"
                self._w = self.original_overlay
                self.status.set_text("")

    def toggle_status(self):
        task = self.filtered[self.focus_index]
        tid = task["id"]
        status = task.get("status", "").lower()
        new = "pending" if status == "done" else "done"
        task_update(tid, {"status": new})
        self.status.set_text(f"✓ Task marked {new}")
        self.load_tasks()
        self.render_tasks()

    def prompt_new(self):
        self.new_task_edit = urwid.Edit(("input", "New task: "))
        self.mode = "new"
        self.original_overlay = self._w
        overlay = urwid.LineBox(urwid.Padding(self.new_task_edit, left=1, right=1))
        self._w = urwid.Overlay(urwid.Filler(overlay), self.original_overlay, align='center', width=50, valign='middle', height=3)

    def prompt_search(self):
        self.search_edit = urwid.Edit(("input", "Search: "), edit_text=self.query)
        self.mode = "search"
        self.original_overlay = self._w
        overlay = urwid.LineBox(urwid.Padding(self.search_edit, left=1, right=1))
        self._w = urwid.Overlay(urwid.Filler(overlay), self.original_overlay, align='center', width=50, valign='middle', height=3)

    def enter_edit_mode(self):
        task = self.filtered[self.focus_index]
        tid = task["id"]
        self.edit_widgets = {
            'content': urwid.Edit(('prompt', "Content: "), task.get("content", "")),
            'tag': urwid.Edit(('prompt', "Tag: "), task.get("tag", "")),
            'notes': urwid.Edit(('prompt', "Notes:\n"), task.get("notes", ""), multiline=True),
            'done': urwid.CheckBox("Done", state=(task.get("status", "").lower() == "done"))
        }

        pile_items = [
            urwid.Text(f"ID: {tid}"),
            urwid.AttrMap(self.edit_widgets['content'], 'input'),
            urwid.AttrMap(self.edit_widgets['tag'], 'input'),
            urwid.AttrMap(self.edit_widgets['notes'], 'input'),
            urwid.AttrMap(self.edit_widgets['done'], 'input'),
        ]

        edit_listbox = urwid.ListBox(urwid.SimpleFocusListWalker(pile_items))
        footer = urwid.Text(" [↑↓/Tab] move   [Enter] save   [Esc] cancel", align='center')

        layout = urwid.Pile([
            ('weight', 1, urwid.Padding(edit_listbox, left=2, right=2)),  # ✅ Box widget in weight
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        self.original_overlay = self._w
        self._w = urwid.AttrMap(
            urwid.LineBox(padded_overlay_body(layout), title=" EDIT TASK ", title_attr='popup_title'),
            'popup_border'
        )

        self.edit_focus = edit_listbox.body
        self.mode = "edit"


    def save_edits(self):
        task = self.filtered[self.focus_index]
        tid = task["id"]
        task_update(tid, {
            "content": self.edit_widgets['content'].edit_text.strip(),
            "tag": self.edit_widgets['tag'].edit_text.strip(),
            "notes": self.edit_widgets['notes'].edit_text.strip(),
            "status": "done" if self.edit_widgets['done'].get_state() else "pending"
        })
        self.status.set_text("✓ Changes saved")
        self.mode = "view"
        self._w = self.original_overlay
        self.load_tasks()
        self.render_tasks()


class ThemeManagerOverlay(urwid.WidgetWrap):
    """Theme selection overlay window"""
    def __init__(self, callback, theme_manager):
        self.close_callback = callback
        self.theme_manager = theme_manager
        self.focus_index = 0

        self.current_theme = self.theme_manager.get_current_theme_name()
        self.theme_names = self.theme_manager.get_theme_names()

        self.status = urwid.Text("")
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.update_theme_list()

        #header = urwid.Text(('highlight', " SELECT A THEME "), align='center')
        header = urwid.Text(('highlight', " "), align='center')
        footer = urwid.Text(" [↑↓] move   [Enter] apply theme   [Esc] cancel", align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" THEME MANAGER ", title_attr='popup_title')
        super().__init__(urwid.AttrMap(boxed, 'popup_border'))

    def update_theme_list(self):
        self.walker.clear()
        for idx, name in enumerate(self.theme_names):
            label = f"→ {name}" if idx == self.focus_index else f"  {name}"
            attr = 'highlight' if idx == self.focus_index else 'default'
            self.walker.append(urwid.AttrMap(urwid.Text(label), attr))

        self.listbox.focus_position = self.focus_index

    def keypress(self, size, key):
        if key == 'up':
            self.focus_index = max(0, self.focus_index - 1)
        elif key == 'down':
            self.focus_index = min(len(self.theme_names) - 1, self.focus_index + 1)
        elif key == 'enter':
            selected_theme = self.theme_names[self.focus_index]
            if self.theme_manager.set_theme(selected_theme):
                self.close_callback(message=f"Theme changed to {selected_theme}")
            else:
                self.close_callback(message=f"Failed to apply theme: {selected_theme}")
            return
        elif key == 'esc':
            self.close_callback(message="Theme selection cancelled.")
            return
        else:
            return super().keypress(size, key)

        # Re-render with new focus
        for idx, name in enumerate(self.theme_names):
            label = f"→ {name}" if idx == self.focus_index else f"  {name}"
            self.walker[idx].original_widget.set_text(label)
            self.walker[idx].set_attr_map({None: 'highlight' if idx == self.focus_index else 'default'})
        self.listbox.focus_position = self.focus_index


class DeckConfigOverlay(urwid.WidgetWrap):
    """System configuration overlay"""
    def __init__(self, callback):
        self.close_callback = callback
        
        # System settings options
        self.options = [
            ('CPU OVERCLOCK', [
                ('STANDARD', True),
                ('PERFORMANCE', False),
                ('EXTREME', False)
            ]),
            ('FIREWALL MODE', [
                ('PASSIVE', False),
                ('ACTIVE', True),
                ('AGGRESSIVE', False)
            ]),
            ('NEURAL INTERFACE', [
                ('DISABLED', False),
                ('BASIC', True),
                ('ENHANCED', False)
            ]),
            ('POWER PROFILE', [
                ('BALANCED', True),
                ('PERFORMANCE', False),
                ('STEALTH', False)
            ])
        ]
        
        # Create radio buttons for each option
        self.option_widgets = []
        for option_name, choices in self.options:
            title = urwid.Text(('secondary', option_name))
            group = []
            choice_widgets = []
            
            for choice_name, state in choices:
                radio = urwid.RadioButton(group, choice_name, state)
                radio = urwid.AttrMap(radio, 'primary', focus_map='selected')
                choice_widgets.append(radio)
            
            option_pile = urwid.Pile([title] + choice_widgets)
            self.option_widgets.append(option_pile)
        
        # Save and close buttons
        save_button = urwid.Button("SAVE CHANGES")
        urwid.connect_signal(save_button, 'click', self.save_changes)
        save_button = urwid.AttrMap(save_button, 'button', focus_map='button_focused')
        
        close_button = urwid.Button("CANCEL")
        urwid.connect_signal(close_button, 'click', self.close)
        close_button = urwid.AttrMap(close_button, 'button', focus_map='button_focused')
        
        button_columns = urwid.Columns([save_button, close_button], dividechars=2)
        
        # Combine all options in a pile
        all_options = urwid.Pile(self.option_widgets + [urwid.Divider(), button_columns])
        
        # Create the final layout
        fill = urwid.Filler(all_options, 'top')
        linebox = urwid.LineBox(fill, title=" DECK CONFIGURATION ", title_attr='popup_title')
        self._w = urwid.AttrMap(linebox, 'popup_border')
    
    def save_changes(self, button):
        # In a real app, you'd save these settings
        self.close_callback(message="Configuration updated successfully.")
    
    def close(self, button=None):
        self.close_callback()

class HelpOverlay(urwid.WidgetWrap):
    """Help overlay with keyboard shortcuts and system info"""
    def __init__(self, callback):
        self.close_callback = callback
        
        # Help content
        self.help_text = urwid.Text([
            ('secondary', "KEYBOARD SHORTCUTS\n"),
            ('primary', "ESC+Q - Exit application\n"),
            ('primary', "TAB - Switch focus between panels\n"),
            ('primary', "F1 - Show this help screen\n"),
            ('primary', "F2 - Show main menu\n"),
            ('primary', "ESC+ENTER - Submit multiline command\n"),
            ('primary', "ENTER - Add new line in command input\n"),
            
            ('secondary', "SYSTEM COMMANDS\n"),
            ('primary', "scan - Scan network for intrusions\n"),
            ('primary', "status - Display system status\n"),
            ('primary', "clear - Clear terminal output\n"),
            ('primary', "help - Show this help screen\n"),
            ('primary', "config - Open deck configuration\n"),
            ('primary', "connect [address] - Connect to a remote system\n\n"),
            
            ('secondary', "ABOUT N3T-RUNNER v0.9.2\n"),
            ('primary', "A cyberpunk-themed terminal interface built with urwid.\n"),
            ('primary', "Features:\n"),
            ('primary', "- Multi-panel interface with tab navigation\n"),
            ('primary', "- Command-line input with command history\n"),
            ('primary', "- Overlay windows for configuration and tools\n"),
            ('primary', "- Real-time system monitoring\n"),
            ('primary', "- Animated interface elements\n"),
        ])
        
        # Close button
        close_button = urwid.Button("CLOSE")
        urwid.connect_signal(close_button, 'click', self.close)
        close_button = urwid.AttrMap(close_button, 'button', focus_map='button_focused')
        
        # Layout
        pile = urwid.Pile([
            ('pack', self.help_text),
            ('pack', urwid.Divider()),
            ('pack', close_button)
        ])
        
        fill = urwid.Filler(pile, 'top')
        boxed = urwid.LineBox(padded_overlay_body(fill), title=" HELP ", title_attr='popup_title')
        self._w = urwid.AttrMap(boxed, 'popup_border')
    
    def close(self, button=None):
        self.close_callback()

class MainMenuOverlay(urwid.WidgetWrap):
    """Main system menu overlay"""
    def __init__(self, callback):
        self.close_callback = callback
        
        # Menu options
        menu_items = [
            ("System Status", self.system_status),
            ("Network Scan", self.network_scan),
            ("Deck Configuration", self.deck_config),
            ("Data Archives", self.data_archives),
            ("Help", self.show_help),
            ("Exit Application", self.exit_app)
        ]
        
        # Create buttons for each menu option
        button_list = []
        for name, func in menu_items:
            button = urwid.Button(name)
            urwid.connect_signal(button, 'click', func)
            button = urwid.AttrMap(button, 'button', focus_map='button_focused')
            button_list.append(button)
        
        # Layout
        pile = urwid.Pile(button_list)
        fill = urwid.Filler(pile, 'top')
        boxed = urwid.LineBox(padded_overlay_body(fill), title=" MAIN MENU ", title_attr='popup_title')
        self._w = urwid.AttrMap(boxed, 'popup_border')
 
    def system_status(self, button):
        self.close_callback(action="status")
    
    def network_scan(self, button):
        self.close_callback(action="network_scan")
    
    def deck_config(self, button):
        self.close_callback(action="config")
    
    def data_archives(self, button):
        self.close_callback(action="archives")
    
    def show_help(self, button):
        help_overlay = HelpOverlay(self.close_overlay)
        self.show_overlay(help_overlay)
    
    def exit_app(self, button):
        self.close_callback(action="exit")

class MadlineApp:
    def __init__(self, theme_name=None):
        # Initialize theme manager
        self.theme_manager = ThemeManager(theme_name or "default")
        self.theme_manager.register_theme_change_callback(self.on_theme_changed)

        # Set up the loop with proper exception handling
        self.screen = urwid.raw_display.Screen()

        if self.theme_manager.color_mode == "truecolor":
            self.screen.set_terminal_properties(colors=16777216)
        elif self.theme_manager.color_mode == "256":
            self.screen.set_terminal_properties(colors=256)
        else:
            self.screen.set_terminal_properties(colors=16)

        # Modifier key toggles
        self.escape_pressed = False
        self.control_pressed = False

        # Header
        self.header_text = urwid.Text(('header', ' [ MADLINE ] :: SYS::TERMINAL :: CONNECT_STATUS::ACTIVE '), align='center')
        self.header = urwid.AttrMap(self.header_text, 'header')
        
        # Footer with system status
        self.footer_text = urwid.Text(('footer', ' [CTRL+Q] Exit | [F1] Help | [F2] Menu | [TAB] Switch Panel | SYSTEM::ONLINE | SECURE_MODE::ACTIVE '))
        self.footer = urwid.AttrMap(self.footer_text, 'footer')
        
        # Main content area - this is a box widget
        self.txt_content = urwid.Text("")
        # Message log to manage terminal output
        self.message_log = MessageLog(self.txt_content)
        self.message_log.add_message("Welcome to N3T-RUNNER terminal.")
        self.message_log.add_message("Initializing cyberdeck systems...")
        
        # Wrap it in a ListBox to make it scrollable and boxable
        self.txt_list = urwid.ListBox(urwid.SimpleListWalker([self.txt_content]))
        self.txt_content_box = urwid.LineBox(self.txt_list, title='TERMINAL OUTPUT', title_attr='secondary')
        
        # Command history
        self.command_history = []
        self.history_position = 0
        
        # Menu buttons with proper attribute maps and callbacks
        self.menu_items = [
            urwid.AttrMap(urwid.Button('DECK CONFIG', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('MAIN MENU', on_press=self.show_main_menu), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('NETWORK SCAN', on_press=self.show_network_scan), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('MODELS', on_press=lambda btn: self.show_model_selector()), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('FILES', on_press=lambda btn: self.show_file_explorer()), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('THEMES', on_press=self.show_theme_manager), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('PROMPTS', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('SETTINGS', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('SESSIONS', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('TOOLS', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
            urwid.AttrMap(urwid.Button('TASKS', on_press=lambda btn: self.show_task_manager()), 'button', focus_map='button_focused'),

            urwid.AttrMap(urwid.Button('MEMORY', on_press=self.show_deck_config), 'button', focus_map='button_focused'),
        ]
        
        # Menu area - using ListBox for proper box sizing
        self.menu_listbox = urwid.ListBox(urwid.SimpleListWalker(self.menu_items))
        self.menu_box = urwid.LineBox(self.menu_listbox, title='SYSTEM MENU', title_attr='secondary')
        self.menu_area = urwid.AttrMap(self.menu_box, 'border')
        
        # Terminal input with command processing
        self.edit = urwid.Edit(('secondary', '> '), multiline=False, wrap='any')
        self.edit.set_edit_text("")  # Initialize with empty text

        urwid.connect_signal(self.edit, 'change', self.on_input_change)
        self.edit_mapped = urwid.AttrMap(self.edit, 'edit', focus_map='edit_focused')
        self.edit_box = urwid.LineBox(self.edit_mapped, title='COMMAND LINE', title_attr='secondary')
        self.edit_area = urwid.AttrMap(self.edit_box, 'border')
        
        # Status line with cyber aesthetics
        self.event_text = [] 
        self.status_text = urwid.Text(('warning', f'[ {' '.join(str(i) for i in self.event_text)} ]'))
        
        # Main layout - right side contents
        self.right_content = [
            ('weight', 8, self.txt_content_box),
            ('pack', self.status_text),
            ('weight', 2, self.edit_area)
        ]
        self.right_pile = urwid.Pile(self.right_content)
        
        # Set up focus tracking to enable tab navigation
        self.left_is_focused = False  # Start with right side focused
        
        # Now create the main columns with proper sizing
        self.main_columns = urwid.Columns([
            ('weight', 1, self.menu_area),
            ('weight', 4, self.right_pile)
        ], dividechars=1)

        # Set default focus
        self.main_columns.focus_position = 1  # Focus right column
        self.right_pile.focus_position = 2  # Focus the edit widget
        
        # Final frame with a Fill as the body to ensure proper sizing
        self.frame = urwid.Frame(
            header=self.header,
            body=urwid.AttrMap(self.main_columns, 'background'),
            footer=self.footer
        )
        
        # Top-level overlay for popup windows
        self.overlay = None
        self.original_widget = self.frame
        

        self.loop = urwid.MainLoop(
            self.frame,
            self.theme_manager.get_urwid_palette(),
            screen=self.screen,
            unhandled_input=self.handle_key
        )

        print(f"[MainLoop] terminal colors set to: {self.screen.colors}")


    def on_theme_changed(self, theme):
        """Callback when the theme changes to update the UI"""
        # Update the palette in the main loop
        self.loop.screen.register_palette(self.theme_manager.get_urwid_palette())
        self.loop.screen.clear()


    
    # Input handling
    def on_input_change(self, widget, text):
        # Will be used for auto-complete in the future
        pass
    
    def process_command(self, command):
        # Add to history
        self.command_history.append(command)
        self.history_position = len(self.command_history)
        
        # Process commands
        cmd_parts = command.split()
        if not cmd_parts:
            return
        
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        if cmd == "help":
            self.show_help()
        elif cmd == "clear":
            self.message_log = MessageLog(self.txt_content)
            self.message_log.add_message("Terminal cleared.")
        elif cmd == "scan" or cmd == "network":
            self.show_network_scan()
        elif cmd == "config":
            self.show_deck_config()
        elif cmd == "theme":
            if args and args[0] in self.theme_manager.get_theme_names():
                if self.theme_manager.set_theme(args[0]):
                    self.message_log.add_message(f"Theme changed to {args[0]}")
                else:
                    self.message_log.add_message(f"Failed to apply theme: {args[0]}", "warning")
            else:
                self.show_theme_manager()
        elif cmd == "status":
            self.message_log.add_message("System Status: ONLINE")
            self.message_log.add_message("CPU: 42% | RAM: 1.7 GB / 8 GB | NETWORK: ACTIVE")
            self.message_log.add_message("Firewall: ACTIVE | Intrusion Detection: ENABLED")
            self.message_log.add_message("Last breach attempt: 13 minutes ago (BLOCKED)")
            self.message_log.add_message(f"Theme: {self.theme_manager.get_current_theme_name()}")
        elif cmd == "connect":
            if args:
                self.message_log.add_message(f"Establishing connection to {args[0]}...", "secondary")
                self.loop.set_alarm_in(1, self.fake_connection_result)
            else:
                self.message_log.add_message("Error: Connection address required.", "warning")
        elif cmd == "exit":
            raise urwid.ExitMainLoop()
        else:
            self.message_log.add_message(f"Unknown command: {cmd}", "warning")
    
    def fake_connection_result(self, loop, user_data):
        # Simulate a connection result after a delay
        result = random.choice([
            ("Connection established. Handshake successful.", "primary"),
            ("Connection failed. Target system not responding.", "warning"),
            ("Connection blocked by firewall. Access denied.", "warning")
        ])
        self.message_log.add_message(result[0], result[1])
    
    # Tab navigation handling
    def toggle_focus(self):
        self.left_is_focused = not self.left_is_focused
        if self.left_is_focused:
            self.main_columns.focus_position = 0  # Focus left column
        else:
            self.main_columns.focus_position = 1  # Focus right column
            self.right_pile.focus_position = 2  # Focus the edit widget
    
    # Key handling
    def handle_key(self, key):
        if self.overlay:  # If an overlay is active, let it handle keys
            if key == 'esc':
                self.close_overlay()
                return True
            return False
        
        if key == 'kjkjkjkj' and self.escape_pressed:
            self.event_text.append("EXITING...")
            self.status_text.set_text(('warning', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
            raise urwid.ExitMainLoop() 
        elif key == 'tab':
            self.toggle_focus()
            return True
        elif key == 'f1':
            self.show_help()
            return True
        elif key == 'f2':
            self.show_main_menu()
            return True
        elif key == 'esc' and not self.left_is_focused:
            # Toggle escape state
            if self.escape_pressed == True:
                self.escape_pressed = False
                self.event_text.remove("ESCAPE ACTIVE")
            else:
                self.escape_pressed = True
                self.event_text.append("ESCAPE ACTIVE")
            self.status_text.set_text(('warning', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
            return True
        elif key == 'enter' and not self.left_is_focused:
            if self.escape_pressed:
                # Submit command when escape is toggled on
                command = self.edit.edit_text
                if command:
                    self.message_log.add_message(f"> {command}", "secondary")
                    self.process_command(command)
                    self.edit.set_edit_text("")  # Clear the input
                # Reset escape state
                self.escape_pressed = False
                self.event_text.remove("ESCAPE ACTIVE")
            else:
                # Add a newline when escape is not toggled
                self.edit.insert_text('\n')

            self.status_text.set_text(('warning', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
            return True
        elif key == 'up' and not self.left_is_focused and self.command_history:
            # Command history navigation - previous command
            if self.history_position > 0:
                self.history_position -= 1
                self.edit.set_edit_text(self.command_history[self.history_position])
            return True
        elif key == 'down' and not self.left_is_focused and self.command_history:
            # Command history navigation - next command
            if self.history_position < len(self.command_history) - 1:
                self.history_position += 1
                self.edit.set_edit_text(self.command_history[self.history_position])
            elif self.history_position == len(self.command_history) - 1:
                self.history_position = len(self.command_history)
                self.edit.set_edit_text("")
            return True
        return False

    def handle_model_selector_result(self, message=None, action=None):
        self.close_overlay(message)
        if action == 'model_selected':
            self.message_log.add_message(f"Model selected: {message}")

    def handle_file_explorer_result(self, message=None, action=None):
        self.close_overlay(message)
        if action == 'file_selected' and message:
            self.message_log.add_message(f"Selected file: {message}")
    
    # Overlay management
    def show_overlay(self, overlay_widget):
        self.overlay = overlay_widget
        overlay = urwid.Overlay(
            self.overlay,
            self.frame,
            align='center',
            width=('relative', 80),
            valign='middle',
            height=('relative', 80),
        )
        self.loop.widget = overlay
    
    def close_overlay(self, message=None, action=None):
        self.loop.widget = self.frame
        self.overlay = None
        
        if message:
            self.message_log.add_message(message)
        
        if action:
            if action == "exit":
                raise urwid.ExitMainLoop()
            elif action == "network_scan":
                self.show_network_scan()
            elif action == "config":
                self.show_deck_config()
            elif action == "help":
                self.show_help()
            elif action == "status":
                self.process_command("status")
            elif action == "archives":
                self.message_log.add_message("Accessing data archives...")
                self.message_log.add_message("Access denied: Insufficient clearance level.", "warning")


    # Specific overlay displays
    def show_help(self, button=None):
        help_overlay = HelpOverlay(self.close_overlay)
        self.show_overlay(help_overlay)
    
    def show_main_menu(self, button=None):
        menu_overlay = MainMenuOverlay(self.close_overlay)
        self.show_overlay(menu_overlay)

    def show_task_manager(self):
        task_overlay = TaskManagerOverlay(self.close_overlay)
        self.show_overlay(task_overlay)

    def show_model_selector(self):
        models = Interactor().list_models()
        overlay = ModelSelectorOverlay(callback=self.handle_model_selector_result, models=models)
        self.show_overlay(overlay)

    def show_theme_manager(self, button=None):
        theme_overlay = ThemeManagerOverlay(self.close_overlay, self.theme_manager)
        self.show_overlay(theme_overlay)

    def show_file_explorer(self, button=None, start_path=None):
        if isinstance(start_path, urwid.Button):  # swap if misordered
            button, start_path = start_path, None
        explorer = FileExplorerOverlay(callback=self.handle_file_explorer_result, start_path=start_path)
        self.show_overlay(explorer)

    def show_network_scan(self, button=None):
        self.message_log.add_message("Initiating network scan...")
        network_overlay = NetworkAnalysisOverlay(self.close_overlay)
        self.show_overlay(network_overlay)
        network_overlay.start_animation(self.loop)
    
    def show_deck_config(self, button=None):
        self.message_log.add_message("Opening deck configuration...")
        config_overlay = DeckConfigOverlay(self.close_overlay)
        self.show_overlay(config_overlay)
    
    def run(self):
        # Start the glitchy cyberpunk boot sequence
        self.loop.set_alarm_in(1, self.update_boot_sequence, 0)
        self.loop.run()
    
    # Boot sequence animation
    def update_boot_sequence(self, loop, step):
        boot_messages = [
            "Initializing neural interface...",
            "Loading core protocols...",
            "Establishing secure connection to mainframe...",
            "Bypassing ICE security...",
            "Reading memory banks...",
            "Injecting runtime hooks...",
            "Activating neural-link protection...",
            "Scanning for hostile agents...",
            "System online. Ready for input."
        ]
        
        if step < len(boot_messages):
            self.message_log.add_message(boot_messages[step])
            next_delay = random.uniform(0.3, 1.0)  # Random delay for cyber effect
            self.loop.set_alarm_in(next_delay, self.update_boot_sequence, step + 1)

if __name__ == "__main__":
    app = MadlineApp()
    app.run()
