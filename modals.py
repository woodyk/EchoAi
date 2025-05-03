#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: modals.py
# Description: Blessed-based terminal modal library supporting multiple modal types with color support
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-02 22:06:56

from blessed import Terminal
import sys

term = Terminal()

THIN = {
    'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
    'h': '─', 'v': '│'
}

class Modal:
    def __init__(self, x=None, y=None, width=50, height=10, title="Modal", border_color="white"):
        self.width = width
        self.height = height
        self.title = title
        self.border_color = border_color
        self.x = x if x is not None else (term.width - width) // 2
        self.y = y if y is not None else (term.height - height) // 2

    def _capture_region(self):
        region = []
        with term.location():
            for row in range(self.y, self.y + self.height):
                line = term.get_line(row) or ''
                region.append(line[self.x:self.x + self.width].ljust(self.width))
        return region

    def _restore_region(self, region):
        for i, line in enumerate(region):
            sys.stdout.write(term.move(self.y + i, self.x) + line)
        sys.stdout.flush()

    def _draw_border(self):
        color = getattr(term, self.border_color, term.white)
        print(color + term.move(self.y, self.x) + THIN['tl'] + THIN['h'] * (self.width - 2) + THIN['tr'])
        for i in range(1, self.height - 1):
            print(term.move(self.y + i, self.x) + THIN['v'] + ' ' * (self.width - 2) + THIN['v'])
        print(term.move(self.y + self.height - 1, self.x) + THIN['bl'] + THIN['h'] * (self.width - 2) + THIN['br'] + term.normal)

    def _draw_title(self):
        centered = f" {self.title} "
        tx = self.x + (self.width - len(centered)) // 2
        print(term.move(self.y, tx) + term.bold + centered + term.normal)

    def _draw_text(self, message):
        lines = message.splitlines()
        for i, line in enumerate(lines[:self.height - 4]):
            ty = self.y + 2 + i
            tx = self.x + 2
            print(term.move(ty, tx) + line[:self.width - 4])

    def show(self, message, wait_for_enter=True):
        saved = self._capture_region()
        self._draw_border()
        self._draw_title()
        self._draw_text(message)
        sys.stdout.flush()
        if wait_for_enter:
            while True:
                key = term.inkey()
                if key.name in ("KEY_ENTER", "KEY_ESCAPE") or key == "\n":
                    break
        self._restore_region(saved)

class InputModal(Modal):
    def get_input(self, prompt="Enter input:"):
        saved = self._capture_region()
        self._draw_border()
        self._draw_title()
        print(term.move(self.y + 2, self.x + 2) + prompt[:self.width - 4])
        print(term.move(self.y + 4, self.x + 2), end="", flush=True)
        with term.cbreak():
            buffer = ""
            while True:
                ch = term.inkey()
                if ch.name == "KEY_ENTER" or ch == "\n":
                    break
                elif ch.name == "KEY_BACKSPACE":
                    buffer = buffer[:-1]
                elif ch.is_sequence:
                    continue
                else:
                    buffer += ch
                print(term.move(self.y + 4, self.x + 2) + " " * (self.width - 4), end="")
                print(term.move(self.y + 4, self.x + 2) + buffer[:self.width - 4], end="", flush=True)
        self._restore_region(saved)
        return buffer

class ConfirmModal(Modal):
    def ask(self, question="Are you sure?"):
        saved = self._capture_region()
        self._draw_border()
        self._draw_title()
        print(term.move(self.y + 2, self.x + 2) + question[:self.width - 4])
        print(term.move(self.y + 4, self.x + 2) + "[y] Yes    [n] No")
        sys.stdout.flush()
        while True:
            key = term.inkey()
            if key.lower() == 'y':
                self._restore_region(saved)
                return True
            elif key.lower() == 'n':
                self._restore_region(saved)
                return False

# Test harness
if __name__ == "__main__":
    print(term.clear)
    with term.cbreak(), term.hidden_cursor():
        modal = Modal(title="Info", border_color="cyan")
        modal.show("This is a basic modal window.\nPress Enter to continue.")

        input_modal = InputModal(title="Input Required", border_color="green")
        result = input_modal.get_input("What's your name?")

        modal = Modal(title="Result", border_color="magenta")
        modal.show(f"You typed: {result}")

        confirm = ConfirmModal(title="Confirm Action", border_color="yellow")
        if confirm.ask("Do you want to proceed?"):
            modal.show("Confirmed. Proceeding...")
        else:
            modal.show("Cancelled.")

