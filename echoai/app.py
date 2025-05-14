#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: cyberpunk_claud.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-05-12 20:14:49
# Modified: 2025-05-13 16:35:42

import os
import json
import urwid
import re
import random
import time

from pathlib import Path

from rich.console import Console

from interactor import Interactor, Session
from mrblack import (
    extract_text,
    extract_pii_text,
    extract_pii_file,
    extract_pii_url
)

from .tools.task_manager import task_list, task_add, task_update, task_delete
from .tui.tui_layout import BevelBox, DynamicHeader

from interactor import Interactor, Session
from .utils.themes import THEMES
from .utils.memory import Memory

console = Console()
print = console.print

def detect_color_mode():
    """Return color mode: 'truecolor', '256', or '16'."""
    colorterm = os.environ.get("COLORTERM", "").lower()
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()

    # Check for truecolor support
    if any(x in colorterm for x in ["truecolor", "24bit"]):
        return "truecolor"
    elif any(x in term_program for x in ["iterm", "kitty", "alacritty", "wezterm"]):
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
        self.color_mode = detect_color_mode()
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

    def get_urwid_palette(self):
        """Convert the current theme to urwid palette format"""
        theme = self.current_theme
        
        def resolve(key, fallback_hex="white"): # fallback_hex changed for clarity
            val = theme.get(key)
            # If val is not a valid hex (e.g., None or not starting with '#'),
            # it might be a named color (like 'white') or we use the fallback_hex.
            if not isinstance(val, str) or not val.startswith("#"):
                # If val is a non-hex string (e.g. 'white'), use it.
                # Otherwise, use fallback_hex.
                return val if isinstance(val, str) and not val.startswith("#") else fallback_hex
            return val # It's a valid hex string

        # palette_definitions items are: (name, fg_theme_key, bg_theme_key, fallback_fg_16, fallback_bg_16)
        palette_definitions = [
            # (name,          fg_theme_key, bg_theme_key, fallback_fg_16, fallback_bg_16)
            ('background',    'dim',        'dim',        'black',        'black'),
            ('header',        'title',      'dim',        'yellow',       'black'),
            ('footer',        'footer',     'dim',        'light gray',   'black'),
            
            # Text Colors
            ('primary',       'prompt',     'dim',        'dark cyan',    'black'),
            ('secondary',     'output',     'dim',        'light blue',   'black'),
            ('accent',        'highlight',  'dim',        'yellow',       'black'),
            ('muted',         'dim',        'dim',        'dark gray',    'black'),
            
            # Message Roles
            ('user',          'prompt',     'dim',        'dark cyan',    'black'),
            ('assistant',     'output',     'dim',        'light blue',   'black'),
            ('system',        'info',       'dim',        'dark green',   'black'),
            ('tool',          'success',    'dim',        'light green',  'black'),
            ('code',          'code',       'dim',        'light blue',   'black'),
            
            # Interactive Elements
            ('edit',          'input',      'dim',        'yellow',       'black'),
            ('edit_focused',  'input',      'dim',        'black',        'yellow'),
            ('button',        'prompt',     'dim',        'white',        'dark blue'),
            ('button_focused','highlight',  'dim',        'black',        'yellow'),
            
            # Status Indicators
            ('error',         'error',      'dim',        'light red',    'black'),
            ('warning',       'warning',    'dim',        'yellow',       'black'),
            ('success',       'success',    'dim',        'light green',  'black'),
            ('info',          'info',       'dim',        'light blue',   'black'),
            
            # Borders
            ('border',        'dim',        'dim',        'dark gray',    'black'),
            ('border_focused','highlight',  'dim',        'yellow',       'black'),
        ]
        
        urwid_palette = []
        # palette_definitions items are: (name, fg_theme_key, _bg_theme_key, fg_16, _original_bg_16_fallback)
        # We ignore _bg_theme_key and _original_bg_16_fallback because backgrounds will be 'default'.
        for name, fg_key, _bg_theme_key, fg_16, _original_bg_16_fallback in palette_definitions:
            fg_hex = resolve(fg_key, '#ffffff') # Default to white hex if fg_key missing or invalid

            # For the 'background' style, set its foregrounds to 'default' as well.
            # For other styles, use the resolved foregrounds.
            current_fg_16 = fg_16
            current_fg_hex = fg_hex
            if name == 'background':
                current_fg_16 = 'default'
                current_fg_hex = 'default'
            
            urwid_palette.append((
                name,               # Palette entry name
                current_fg_16,      # Standard foreground (16-color) or 'default'
                'default',          # Standard background (16-color) - ALWAYS 'default'
                '',                 # Mono setting (optional) - Urwid docs suggest empty string for default behavior
                current_fg_hex,     # Foreground high (truecolor/256color) or 'default'
                'default'           # Background high (truecolor/256color) - ALWAYS 'default'
            ))
            
        return urwid_palette

class ProgressBar(urwid.ProgressBar):
    """Custom progress bar with cyberpunk styling"""
    def __init__(self, normal, complete, current=0, done=100):
        super().__init__(normal, complete, current, done)

class SelectableListBox(urwid.ListBox):
    """A ListBox that supports text selection"""
    def __init__(self, body):
        super().__init__(body)
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.clipboard = None

    def mouse_event(self, size, event, button, col, row, focus):
        """Handle mouse events for text selection"""
        if event == 'mouse press':
            if button == 1:  # Left click
                self.is_selecting = True
                self.selection_start = (col, row)
                self.selection_end = (col, row)
                return True
        elif event == 'mouse drag':
            if button == 1 and self.is_selecting:  # Left drag
                self.selection_end = (col, row)
                return True
        elif event == 'mouse release':
            if button == 1:  # Left release
                self.is_selecting = False
                if self.selection_start and self.selection_end:
                    # Get the selected text
                    selected_text = self._get_selected_text()
                    if selected_text:
                        self.clipboard = selected_text
                return True
        return False

    def _get_selected_text(self):
        """Extract the selected text based on selection coordinates"""
        if not self.selection_start or not self.selection_end:
            return None

        start_col, start_row = self.selection_start
        end_col, end_row = self.selection_end

        # Ensure start is before end
        if start_row > end_row or (start_row == end_row and start_col > end_col):
            start_col, start_row, end_col, end_row = end_col, end_row, start_col, start_row

        selected_text = []
        for i in range(start_row, end_row + 1):
            if i < len(self.body):
                widget = self.body[i].original_widget
                text = widget.get_text()[0]  # Get the text content
                if i == start_row:
                    text = text[start_col:]
                if i == end_row:
                    text = text[:end_col]
                selected_text.append(text)

        return '\n'.join(selected_text)

class MessageLog:
    """Class to manage terminal messages with timestamps"""
    def __init__(self, widget):
        self.widget = widget
        self.messages = []
        self.current_stream_message = None
        self.listbox = None  # Will be set when the widget is added to a ListBox
        self.walker = None   # Will store the SimpleListWalker
    
    def set_listbox(self, listbox, walker):
        """Set the ListBox and walker references for auto-scrolling"""
        self.walker = walker
        # Create a new SelectableListBox with the walker
        self.listbox = SelectableListBox(walker)
    
    def add_message(self, message, role="user"):
        timestamp = time.strftime("[%H:%M:%S]", time.localtime())
        # Create a tuple of (style, text) pairs for the timestamp and message
        styled_message = [
            ('info', timestamp + ' '),
            (role, message.strip())
        ]
        self.messages.append(styled_message)
        self._update_widget()
    
    def start_stream(self, role="assistant"):
        """Start a new streaming message"""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime())
        self.current_stream_message = [
            ('info', timestamp + ' '),  # Timestamp in green
            (role, '')                  # Empty message in white
        ]
        self.messages.append(self.current_stream_message)
        self._update_widget()
    
    def update_stream(self, text, role="assistant"):
        """Update the current streaming message"""
        if self.current_stream_message:
            # Keep the timestamp, append to the message part
            current_text = self.current_stream_message[1][1]  # Get current message text
            self.current_stream_message[1] = (role, current_text + text)
            self.messages[-1] = self.current_stream_message
            self._update_widget()
    
    def end_stream(self):
        """End the current streaming message"""
        self.current_stream_message = None
    
    def _update_widget(self):
        # Clear the walker
        self.walker.clear()
        
        # Add each message as a separate Text widget
        for message_parts in self.messages:
            text_widget = urwid.Text(message_parts)
            # Add mouse support to the text widget
            text_widget = urwid.AttrMap(text_widget, None, focus_map='highlight')
            self.walker.append(text_widget)
        
        # Auto-scroll to the bottom
        if self.listbox and self.walker:
            self.listbox.set_focus(len(self.walker) - 1)

class SelectableText(urwid.Text):
    """A text widget that supports selection"""
    def __init__(self, text):
        super().__init__(text)
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.clipboard = None

    def mouse_event(self, size, event, button, col, row, focus):
        """Handle mouse events for text selection"""
        if event == 'mouse press':
            if button == 1:  # Left click
                self.is_selecting = True
                self.selection_start = col
                self.selection_end = col
                return True
        elif event == 'mouse drag':
            if button == 1 and self.is_selecting:  # Left drag
                self.selection_end = col
                return True
        elif event == 'mouse release':
            if button == 1:  # Left release
                self.is_selecting = False
                if self.selection_start is not None and self.selection_end is not None:
                    # Get the selected text
                    selected_text = self._get_selected_text()
                    if selected_text:
                        self.clipboard = selected_text
                return True
        return False

    def _get_selected_text(self):
        """Extract the selected text based on selection coordinates"""
        if self.selection_start is None or self.selection_end is None:
            return None

        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)

        # Get the text content
        text = self.get_text()[0]
        return text[start:end]

    def render(self, size, focus=False):
        """Render the text with selection highlighting"""
        canvas = super().render(size, focus)
        
        if self.is_selecting and self.selection_start is not None and self.selection_end is not None:
            start = min(self.selection_start, self.selection_end)
            end = max(self.selection_start, self.selection_end)
            
            # Apply selection highlighting
            for i in range(start, end):
                if i < len(canvas.text[0]):
                    canvas.text[0][i] = ('highlight', canvas.text[0][i][1])
        
        return canvas

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
    def __init__(self, callback, sessions):
        self.callback = callback
        self.sessions = sorted(sessions, key=lambda x: x.get('name', '').lower())
        self.focus_index = 0
        self.active_query = ""

        self.status = urwid.Text(('footer', ""))
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.update_session_list()

        header = urwid.Text(('header', " "), align='center')
        footer = urwid.Text(('footer', " [↑↓] move   [/] search   [Enter] select   [Esc] cancel"), align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" SESSION MANAGER ", title_attr='header')
        super().__init__(urwid.AttrMap(boxed, 'border'))

    def update_session_list(self):
        self.walker.clear()
        for idx, session in enumerate(self.sessions):
            name = session.get('name', 'Unnamed Session')
            sid = session.get('id', '')[:8]
            prefix = "→ " if idx == self.focus_index else "  "
            # Use button/button_focused for consistent styling
            style = 'button_focused' if idx == self.focus_index else 'button'
            text = f"{prefix}{name} ({sid})"
            self.walker.append(urwid.AttrMap(urwid.Text(text), style))
        if self.sessions:
            self.listbox.focus_position = self.focus_index

    def keypress(self, size, key):
        if key in ('up', 'k'):
            self.focus_index = max(0, self.focus_index - 1)
        elif key in ('down', 'j'):
            self.focus_index = min(len(self.sessions) - 1, self.focus_index + 1)
        elif key == '/':
            self.prompt_search()
            return
        elif key == 'enter':
            if self.sessions:
                selected = self.sessions[self.focus_index]
                self.callback(action='session_selected', message=selected['id'])
            else:
                self.callback(message="No sessions available.")
            return
        elif key == 'esc':
            self.callback(message="Session selection cancelled.")
            return
        else:
            return super().keypress(size, key)

        # Redraw list
        for idx, session in enumerate(self.sessions):
            name = session.get('name', 'Unnamed Session')
            sid = session.get('id', '')[:8]
            prefix = "→ " if idx == self.focus_index else "  "
            style = 'button_focused' if idx == self.focus_index else 'button'
            text = f"{prefix}{name} ({sid})"
            self.walker[idx].original_widget.set_text(text)
            self.walker[idx].set_attr_map({None: style})
        self.listbox.focus_position = self.focus_index

    def prompt_search(self):
        edit = urwid.Edit(('input', "Search: "), edit_text=self.active_query)
        edit_map = urwid.AttrMap(edit, 'input')
        linebox = urwid.LineBox(urwid.Padding(edit_map, left=1, right=1), title_attr='header')

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
        self._w = urwid.AttrMap(self._w, 'border')
        urwid.connect_signal(edit, 'change', lambda *_: None)
        self._w.keypress = handle_search_input

    def apply_search(self, query):
        self.active_query = query
        if query:
            q = query.lower()
            self.sessions = [s for s in self.sessions if q in s.get('name', '').lower()]
        else:
            self.sessions = sorted(sessions, key=lambda x: x.get('name', '').lower())
        self.focus_index = 0
        self.update_session_list()

class ToolManagerOverlay(urwid.WidgetWrap):
    pass

class FileExplorerOverlay(urwid.WidgetWrap):
    def __init__(self, callback, start_path=None):
        self.callback = callback
        self.current_path = Path(start_path or os.getcwd()).resolve()
        self.entries = []
        self.focus_index = 0

        self.header = urwid.Text(('header', ""), align='center')
        self.status = urwid.Text(('footer', ""), align='left')

        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.update_entries()

        container = urwid.Pile([
            ('pack', self.header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', urwid.Text(('footer', " [↑↓] move   [Enter] open/select   [Esc] cancel"), align='center')),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(container), title=" FILE EXPLORER ", title_attr='header')
        super().__init__(urwid.AttrMap(boxed, 'border'))

    def update_entries(self):
        try:
            children = sorted(self.current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            if self.current_path.parent != self.current_path:
                self.entries = [self.current_path.parent] + children
            else:
                self.entries = children
        except Exception as e:
            self.status.set_text(('error', f"Error: {e}"))
            self.entries = []

        self.focus_index = 0
        self.header.set_text(('header', f"{self.current_path}"))
        self.walker.clear()

        for idx, path in enumerate(self.entries):
            label = path.name if path.name != '' else str(path)
            if path == self.current_path.parent:
                label = '..'
            display = label + ('/' if path.is_dir() and label != '..' else '')
            prefix = '→ ' if idx == self.focus_index else '  '
            # Use button/button_focused for consistent styling with theme selector
            style = 'button_focused' if idx == self.focus_index else 'button'
            text = urwid.Text(prefix + display)
            self.walker.append(urwid.AttrMap(text, style))

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
            # Use button/button_focused for consistent styling with theme selector
            style = 'button_focused' if i == self.focus_index else 'button'
            self.walker[i].original_widget.set_text(prefix + display)
            self.walker[i].set_attr_map({None: style})
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

        # Set focus to the current model
        if default_model in self.filtered_models:
            self.focus_index = self.filtered_models.index(default_model)

        self.status = urwid.Text(('footer', ""))
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)
        self.update_model_list()

        header = urwid.Text(('header', " "), align='center')
        footer = urwid.Text(('footer', " [↑↓] move   [/] search   [Enter] select   [Esc] cancel"), align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" MODEL SELECTOR ", title_attr='header')
        super().__init__(urwid.AttrMap(boxed, 'border'))

    def update_model_list(self):
        self.walker.clear()
        for idx, name in enumerate(self.filtered_models):
            prefix = "→ " if idx == self.focus_index else "  "
            # Use button/button_focused for consistent styling
            style = 'button_focused' if idx == self.focus_index else 'button'
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
            style = 'button_focused' if idx == self.focus_index else 'button'
            self.walker[idx].original_widget.set_text(prefix + name)
            self.walker[idx].set_attr_map({None: style})
        self.listbox.focus_position = self.focus_index

    def prompt_search(self):
        edit = urwid.Edit(('input', "Search: "), edit_text=self.active_query)
        edit_map = urwid.AttrMap(edit, 'input')
        linebox = urwid.LineBox(urwid.Padding(edit_map, left=1, right=1), title_attr='header')

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
        self._w = urwid.AttrMap(self._w, 'border')
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

        self.status = urwid.Text(('footer', ""))
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.load_tasks()
        self.render_tasks()

        header = urwid.Text(('header', " "), align='center')
        footer = urwid.Text(('footer', " [↑↓] move   [n] new   [d] delete   [m] mark   [/] search   [c] completed   [s] sort   [Enter] edit   [Esc] exit"), align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, urwid.Padding(self.listbox, left=2, right=2)),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" TASK MANAGER ", title_attr='header')
        self._w = urwid.AttrMap(boxed, 'border')

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
            # Use button/button_focused for consistent styling
            style = 'button_focused' if i == self.focus_index else 'button'
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
        self.new_task_edit = urwid.Edit(('input', "New task: "))
        self.mode = "new"
        self.original_overlay = self._w
        overlay = urwid.LineBox(urwid.Padding(self.new_task_edit, left=1, right=1), title_attr='header')
        self._w = urwid.Overlay(urwid.Filler(overlay), self.original_overlay, align='center', width=50, valign='middle', height=3)

    def prompt_search(self):
        self.search_edit = urwid.Edit(('input', "Search: "), edit_text=self.query)
        self.mode = "search"
        self.original_overlay = self._w
        overlay = urwid.LineBox(urwid.Padding(self.search_edit, left=1, right=1), title_attr='header')
        self._w = urwid.Overlay(urwid.Filler(overlay), self.original_overlay, align='center', width=50, valign='middle', height=3)

    def enter_edit_mode(self):
        task = self.filtered[self.focus_index]
        tid = task["id"]
        self.edit_widgets = {
            'content': urwid.Edit(('input', "Content: "), task.get("content", "")),
            'tag': urwid.Edit(('input', "Tag: "), task.get("tag", "")),
            'notes': urwid.Edit(('input', "Notes:\n"), task.get("notes", ""), multiline=True),
            'done': urwid.CheckBox("Done", state=(task.get("status", "").lower() == "done"))
        }

        pile_items = [
            urwid.Text(('header', f"ID: {tid}")),
            urwid.AttrMap(self.edit_widgets['content'], 'input'),
            urwid.AttrMap(self.edit_widgets['tag'], 'input'),
            urwid.AttrMap(self.edit_widgets['notes'], 'input'),
            urwid.AttrMap(self.edit_widgets['done'], 'input'),
        ]

        edit_listbox = urwid.ListBox(urwid.SimpleFocusListWalker(pile_items))
        footer = urwid.Text(('footer', " [↑↓/Tab] move   [Enter] save   [Esc] cancel"), align='center')

        layout = urwid.Pile([
            ('weight', 1, urwid.Padding(edit_listbox, left=2, right=2)),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        self.original_overlay = self._w
        self._w = urwid.AttrMap(
            urwid.LineBox(padded_overlay_body(layout), title=" EDIT TASK ", title_attr='header'),
            'border'
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
    def __init__(self, callback, theme_manager, default_theme):
        self.close_callback = callback
        self.theme_manager = theme_manager
        self.focus_index = 0

        # Get theme names and set focus to current theme
        self.theme_names = self.theme_manager.get_theme_names()
        if default_theme in self.theme_names:
            self.focus_index = self.theme_names.index(default_theme)
        else:
            # If current theme not found, use the theme manager's current theme
            current_theme = self.theme_manager.get_current_theme_name()
            if current_theme in self.theme_names:
                self.focus_index = self.theme_names.index(current_theme)

        self.status = urwid.Text(('footer', ""))
        self.walker = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)

        self.update_theme_list()

        header = urwid.Text(('header', " "), align='center')
        footer = urwid.Text(('footer', " [↑↓] move   [Enter] apply theme   [Esc] cancel"), align='center')

        layout = urwid.Pile([
            ('pack', header),
            ('weight', 1, self.listbox),
            ('pack', self.status),
            ('pack', footer),
            ('pack', urwid.Divider()),
        ])

        boxed = urwid.LineBox(padded_overlay_body(layout), title=" THEME MANAGER ", title_attr='header')
        super().__init__(urwid.AttrMap(boxed, 'border'))

    def update_theme_list(self):
        self.walker.clear()
        for idx, name in enumerate(self.theme_names):
            prefix = "→ " if idx == self.focus_index else "  "
            # Use button/button_focused for consistent styling
            style = 'button_focused' if idx == self.focus_index else 'button'
            self.walker.append(urwid.AttrMap(urwid.Text(prefix + name), style))

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
            prefix = "→ " if idx == self.focus_index else "  "
            style = 'button_focused' if idx == self.focus_index else 'button'
            self.walker[idx].original_widget.set_text(prefix + name)
            self.walker[idx].set_attr_map({None: style})
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
    
    def show_help(self, button=None):
        help_overlay = HelpOverlay(self.close_overlay)
        self.show_overlay(help_overlay)
    
    def exit_app(self, button):
        self.close_callback(action="exit")

class MadlineApp:
    def __init__(self, theme_name=None):
        # Prep our Interactor object
        self.config = {}
        self.CONFIG_DIR = Path.home() / ".echoai"
        self.CONFIG_FILE = self.CONFIG_DIR / "config"
        self.prompt_history = self.CONFIG_DIR / ".history"
        self.default_config = {
            "model": "openai:gpt-4o",
            "system_prompt": "You are a helpful assistant.",
            "username": "User",
            "markdown": True,
            "theme": "default",
            "stream": True,
            "tools": True,
            "memory": False
        }

        self._init_directories()
        self._load_config()
        self.user_history = []

        # Prep Session Config
        self.session_dir = self.CONFIG_DIR / "sessions"
        self.session = Session(directory=self.session_dir)
        self._refresh_session_lookup()
        self.session_id_lookup = {}

        # Prep Memory Config
        self.memory = None
        self.memory_enabled = None
        self.memory_db_path = self.CONFIG_DIR / "echoai_db"

        # Initialize Interactor
        self.ai = Interactor(
            model=self.config.get("model", self.default_config["model"]),
            context_length=120000,
            session_enabled=False,
            session_path=self.session_dir,
        )
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(theme_name or "default")
        self.theme_manager.register_theme_change_callback(self.on_theme_changed)

        # Set up the screen with proper color support
        self.screen = urwid.display.raw.Screen()
        self.screen.set_mouse_tracking(False)
        self.screen.register_palette(self.theme_manager.get_urwid_palette())
        
        # Configure screen for truecolor support BEFORE creating MainLoop
        if self.theme_manager.color_mode == "truecolor":
            self.screen.set_terminal_properties(colors=2**24)  # 24-bit color
        elif self.theme_manager.color_mode == "256":
            self.screen.set_terminal_properties(colors=256)
        else:
            self.screen.set_terminal_properties(colors=16)

        self.screen.reset_default_terminal_palette()

        # Modifier key toggles
        self.escape_pressed = False
        self.control_pressed = False

        # Header
        self.header_text = urwid.Text(('header', ' [ MADLINE ] :: SYS::TERMINAL :: CONNECT_STATUS::ACTIVE '), align='center')
        self.header = urwid.AttrMap(self.header_text, 'header')
        
        # Footer with system status
        self.footer_text = urwid.Text(('footer', ' [CTRL+C] Exit | [F1] Help | [F2] Menu | [TAB] Switch Panel | SYSTEM::ONLINE | SECURE_MODE::ACTIVE '), align='center')
        self.footer = urwid.AttrMap(self.footer_text, 'footer')
        
        # Main content area - this is a box widget
        self.txt_content = urwid.Text("")
        # Message log to manage terminal output
        self.message_log = MessageLog(self.txt_content)
        
        # Create the walker and listbox
        self.txt_walker = urwid.SimpleListWalker([])
        self.txt_list = urwid.ListBox(self.txt_walker)
        self.message_log.set_listbox(self.txt_list, self.txt_walker)
        
        # Add initial messages
        self.message_log.add_message("Welcome to MadLine AI Terminal.", role="title")
        self.message_log.add_message("Initializing cyberdeck systems...", role="system")
        
        # Create the boxed widget
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
        self.menu_area = urwid.AttrMap(self.menu_box, 'border', focus_map='border_focused')
        
        # Terminal input with command processing and mouse support
        self.edit = urwid.Edit(('user', '> '), multiline=False, wrap='any')
        self.edit.set_edit_text("")  # Initialize with empty text
        self.edit.selection_start = None
        self.edit.selection_end = None
        self.edit.is_selecting = False

        urwid.connect_signal(self.edit, 'change', self.on_input_change)
        self.edit_mapped = urwid.AttrMap(self.edit, 'edit', focus_map='edit_focused')
        
        # Create a ListBox to handle scrolling for the edit widget
        self.edit_walker = urwid.SimpleListWalker([self.edit_mapped])
        self.edit_listbox = urwid.ListBox(self.edit_walker)
        
        # Create a Filler to give the ListBox a fixed height
        self.edit_filler = urwid.Filler(self.edit_listbox, height=('relative', 100))
        
        # Create the boxed widget with the scrollable edit area
        self.edit_box = urwid.LineBox(
            self.edit_filler,
            title='COMMAND LINE',
            title_attr='secondary',
            tlcorner='┌', tline='─', lline='│',
            trcorner='┐', blcorner='└', rline='│',
            bline='─', brcorner='┘'
        )
        self.edit_area = urwid.AttrMap(self.edit_box, 'border', focus_map='border_focused')
        
        # Status line with cyber aesthetics
        self.event_text = [] 
        self.status_text = urwid.Text(('error', f'[ {' '.join(str(i) for i in self.event_text)} ]'))
        
        # Main layout - right side contents
        self.right_content = [
            ('weight', 10, self.txt_content_box),  # Terminal output area
            ('pack', self.status_text),           # Status line
            ('weight', 2, self.edit_area)         # Command input area - reduced weight
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
        

        # Create MainLoop AFTER screen configuration, initially with an empty palette
        self.loop = urwid.MainLoop(
            self.frame,
            [],  # Initialize with an empty palette
            screen=self.screen,
            unhandled_input=self.handle_key,
            handle_mouse=False  # Disable mouse handling in MainLoop
        )

        # Now, register the actual palette

        print(f"[MainLoop] terminal colors set to: {self.screen.colors}")

    def _init_directories(self):
        if not self.CONFIG_DIR.exists():
            self.CONFIG_DIR.mkdir(exist_ok=True)

    def _load_config(self):
        if self.CONFIG_FILE.exists():
            with self.CONFIG_FILE.open("r") as file_object:
                config_from_file = json.load(file_object)
            self.config = self.default_config.copy()
            self.config.update(config_from_file)
        else:
            self.config = self.default_config.copy()
            self.save_config(self.config)

    def _save_config(self, new_config):
        current_config = self.default_config.copy()
        if self.CONFIG_FILE.exists():
            with self.CONFIG_FILE.open("r") as file_object:
                current_config.update(json.load(file_object))
        current_config.update(new_config)
        with self.CONFIG_FILE.open("w") as file_object:
            json.dump(current_config, file_object, indent=4)
        self.load_config()

    def _refresh_session_lookup(self):
        self.session_id_lookup = {
            f"{s.get('name', 'unnamed')} ({s['id'][:8]})": s["id"]
            for s in self.session.list()
        }

    def on_theme_changed(self, theme):
        """Callback when the theme changes to update the UI"""
        # Update the palette in the main loop
        self.loop.screen.register_palette(self.theme_manager.get_urwid_palette())
        self.loop.screen.clear()


    
    # Input handling
    def on_input_change(self, widget, text):
        # Will be used for auto-complete in the future
        pass


    
    def process_user_input(self, user_input):
        """Process user input"""
        if user_input is None or user_input.strip() == "":
            return

        user_input = user_input.lstrip('> ').lstrip()
        # Add to history
        self.user_history.append(user_input)

        if not isinstance(self.ai.session_id, str):
            self.ai.session_id = None

        self.ai.messages_system(self.config["system_prompt"] + "\n")

        if self.memory_enabled:
            self.memory.add("user: " + user_input)

        # Display user input without the "> " prefix
        self.message_log.add_message(user_input, role="user")

        # Start a new streaming message
        self.message_log.start_stream()
        
        def stream_callback(token):
            """Callback for handling streaming tokens"""
            self.message_log.update_stream(token)
            # Force a redraw of the UI
            self.loop.draw_screen()

        with self.ai.interact(
            user_input,
            raw=True,
            model=self.config["model"],
            tools=self.config["tools"],
            stream=self.config["stream"],
            markdown=self.config["markdown"],
            session_id=self.ai.session_id,
        ) as response:
            for chunk in response:
                stream_callback(chunk)
        
        # End the streaming message
        self.message_log.end_stream()

        if self.memory_enabled:
            self.memory.add("assistant: " + response)
    
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
        
        # Add copy/paste support
        if key == 'ctrl c':
            # Copy selected text
            if hasattr(self.edit, 'selection_start') and self.edit.selection_start:
                start = min(self.edit.selection_start, self.edit.selection_end)
                end = max(self.edit.selection_start, self.edit.selection_end)
                selected_text = self.edit.edit_text[start:end]
                self.edit.clipboard = selected_text
            return True
        elif key == 'ctrl v':
            # Paste from clipboard
            if hasattr(self.edit, 'clipboard'):
                self.edit.insert_text(self.edit.clipboard)
            return True
        
        if key == 'kjkjkjkj' and self.escape_pressed:
            self.event_text.append("EXITING...")
            self.status_text.set_text(('error', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
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
            self.status_text.set_text(('error', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
            return True
        elif key == 'enter' and not self.left_is_focused:
            if self.escape_pressed:
                user_input = self.edit.edit_text.lstrip('> ').lstrip()
                self.edit.set_edit_text("")
                if user_input:
                    self.process_user_input(user_input)
                self.escape_pressed = False
                self.event_text.remove("ESCAPE ACTIVE")
            else:
                self.edit.insert_text('\n')

            self.status_text.set_text(('error', f"[ {' '.join(str(i) for i in self.event_text)} ]"))
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
        overlay = ModelSelectorOverlay(
            callback=self.handle_model_selector_result,
            models=models,
            default_model=self.config.get("model", self.default_config["model"])
        )
        self.show_overlay(overlay)

    def show_theme_manager(self, button=None):
        theme_overlay = ThemeManagerOverlay(
            self.close_overlay,
            self.theme_manager,
            default_theme=self.config.get("theme", self.default_config["theme"])
        )
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
        ]
        
        if step < len(boot_messages):
            self.message_log.add_message(boot_messages[step])
            next_delay = random.uniform(0.3, 1.0)  # Random delay for cyber effect
            self.loop.set_alarm_in(next_delay, self.update_boot_sequence, step + 1)

if __name__ == "__main__":
    app = MadlineApp()
    app.run()
