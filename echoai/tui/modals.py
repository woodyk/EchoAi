#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: modals.py
# Description: Theme-aware TUI modal library for EchoAI with sync and async support
# Author: Ms. White
# Created: 2025-05-04
# Modified: 2025-05-11 15:41:03

import urwid
import asyncio
import datetime
from threading import Thread
from time import time, sleep
from typing import Optional

from echoai.tui.tui_layout import get_theme_palette, BevelBox


class _BlockingLoop(urwid.MainLoop):
    def __init__(self, widget, palette, key_handler, screen=None):
        screen = screen or urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        screen.set_mouse_tracking(False)
        super().__init__(widget, palette, unhandled_input=self._handle, screen=screen)
        self._key_handler = key_handler

    def _handle(self, key: str):
        if isinstance(key, tuple) and key[0].startswith("mouse"):
            return
        if self._key_handler:
            self._key_handler(key)

class Modal:
    def __init__(self, theme: str = "default"):
        self.theme_name = theme
        self.palette, self.theme = get_theme_palette(theme)

    def _overlay(self, body, width, height, attr="prompt"):
        frame = urwid.AttrMap(BevelBox(body), attr)
        return urwid.Overlay(frame, urwid.SolidFill(), align="center", width=width, valign="middle", height=height)

    def _run_modal(self, widget, width, height, attr="prompt", handler=None):
        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        screen.set_mouse_tracking(False)
        loop = _BlockingLoop(self._overlay(widget, width, height, attr), self.palette, handler, screen)
        loop.run()

    def _run_modal_with_timeout(self, widget, width, height, attr, handler, timeout, default_result):
        result = [None]
        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        screen.set_mouse_tracking(False)

        overlay = self._overlay(widget, width, height, attr)
        loop = _BlockingLoop(overlay, self.palette, None, screen)

        def wrapped_handler(key):
            if isinstance(key, tuple) and key[0].startswith("mouse"):
                return
            if result[0] is None:
                handler(key, result)

        loop._unhandled_input = wrapped_handler
        loop.screen.start()

        start = time()
        try:
            loop.draw_screen()
            while result[0] is None and time() - start < timeout:
                keys = screen.get_input()
                for key in keys:
                    loop.process_input([key])
                loop.draw_screen()
                sleep(0.05)

            return result[0] if result[0] is not None else default_result
        finally:
            screen.stop()

    def toast(self, text: str, duration: float = 2.0):
        text_widget = urwid.Text(text, align="center")
        filler = urwid.Filler(text_widget)
        box = BevelBox(filler)
        mapped = urwid.AttrMap(box, "info")

        overlay = urwid.Overlay(
            mapped,
            urwid.SolidFill(),
            align="right", width=len(text) + 6, right=2,
            valign="top", height=5, top=1
        )

        loop = urwid.MainLoop(overlay, palette=self.palette, screen=urwid.raw_display.Screen())
        loop.screen.set_terminal_properties(colors=256)
        loop.screen.set_mouse_tracking(False)

        def exit_on_timer(loop, user_data):
            raise urwid.ExitMainLoop()

        loop.set_alarm_in(duration, exit_on_timer)
        loop.run()

    def confirm(self, text: str, timeout: Optional[float] = None) -> bool:
        result = [None]
        body = urwid.Filler(urwid.Pile([
            urwid.Text(text, align="center"),
            urwid.Divider(),
            urwid.Text(("footer", "[y] yes   [n] no   [esc] cancel"), align="center")
        ]))
        frame = BevelBox(body)
        decorated = urwid.AttrMap(frame, "prompt")

        overlay = urwid.Overlay(
            decorated,
            urwid.SolidFill(),
            align="center", width=50,
            valign="middle", height=7
        )

        def unhandled(key):
            if key == "y":
                result[0] = True
                raise urwid.ExitMainLoop()
            elif key in ("n", "esc"):
                result[0] = False
                raise urwid.ExitMainLoop()

        def on_timeout(loop, data):
            if result[0] is None:
                result[0] = False
                raise urwid.ExitMainLoop()

        loop = urwid.MainLoop(overlay, palette=self.palette, unhandled_input=unhandled)
        loop.screen.set_terminal_properties(colors=256)
        if timeout:
            loop.set_alarm_in(timeout, on_timeout)
        loop.run()
        return result[0]

    def input(self, prompt: str, timeout: Optional[float] = None) -> Optional[str]:
        result = [None]
        edit = urwid.Edit(multiline=False)
        body = urwid.Filler(urwid.Pile([
            urwid.Text(prompt, align="center"),
            urwid.Divider(),
            urwid.Padding(edit, left=2, right=2),
            urwid.Divider(),
            urwid.Text(("footer", "[enter] submit   [esc] cancel"), align="center"),
        ]))
        frame = BevelBox(body)
        decorated = urwid.AttrMap(frame, "prompt")

        overlay = urwid.Overlay(
            decorated,
            urwid.SolidFill(),
            align="center", width=60,
            valign="middle", height=8
        )

        def unhandled(key):
            if key == "enter":
                result[0] = edit.edit_text.strip()
                raise urwid.ExitMainLoop()
            elif key == "esc":
                result[0] = None
                raise urwid.ExitMainLoop()

        def on_timeout(loop, data):
            if result[0] is None:
                result[0] = None
                raise urwid.ExitMainLoop()

        loop = urwid.MainLoop(overlay, palette=self.palette, unhandled_input=unhandled)
        loop.screen.set_terminal_properties(colors=256)
        if timeout:
            loop.set_alarm_in(timeout, on_timeout)
        loop.run()
        return result[0]

    def choose(self, prompt: str, options: list[str]) -> Optional[str]:
        result = [None]
        radio_buttons = []
        group = []

        for opt in options:
            rb = urwid.RadioButton(group, opt, state=False)
            radio_buttons.append(rb)

        walker = urwid.SimpleFocusListWalker(radio_buttons)
        listbox = urwid.ListBox(walker)
        listbox._command_map["enter"] = None

        def keys(k):
            if k == "enter":
                for rb in radio_buttons:
                    if rb.get_state():
                        result[0] = rb.get_label()
                        break
                raise urwid.ExitMainLoop()
            elif k == "esc":
                raise urwid.ExitMainLoop()

        pile = urwid.Pile([
            urwid.Text(prompt, align="center"),
            urwid.Divider(),
            urwid.BoxAdapter(listbox, height=min(len(options), 10)),
            urwid.Divider(),
            urwid.Text(("footer", "[up/down] select  [enter] confirm  [esc] cancel"), align="center"),
        ])

        self._run_modal(pile, 60, height='pack', attr="prompt", handler=keys)
        return result[0]

    def input_multiline(self, prompt: str) -> Optional[str]:
        result = [None]
        edit = urwid.Edit(multiline=True)
        box = urwid.Padding(urwid.AttrMap(edit, "input"), left=2, right=2)

        def keys(k):
            if k == "ctrl d": result[0] = edit.edit_text; raise urwid.ExitMainLoop()
            elif k == "esc": raise urwid.ExitMainLoop()

        pile = urwid.Pile([
            urwid.Text(prompt, align="center"),
            urwid.Divider(),
            box,
            urwid.Divider(),
            urwid.Text(("footer", "[ctrl-d] submit  [esc] cancel"), align="center"),
        ])
        self._run_modal(pile, 60, height='pack', attr="prompt", handler=keys)
        return result[0]

    def password(self, prompt: str) -> Optional[str]:
        result = [None]
        pw = urwid.Edit(mask="•")

        def keys(k):
            if k == "enter": result[0] = pw.edit_text; raise urwid.ExitMainLoop()
            elif k == "esc": raise urwid.ExitMainLoop()

        pile = urwid.Pile([
            urwid.Text(prompt, align="center"),
            urwid.Divider(),
            urwid.Padding(urwid.AttrMap(pw, "input"), left=2, right=2),
            urwid.Divider(),
            urwid.Text(("footer", "[enter] submit  [esc] cancel"), align="center"),
        ])
        self._run_modal(pile, 60, 8, attr="prompt", handler=keys)
        return result[0]

    def info(self, text: str): self._notify("info", text)
    def warning(self, text: str): self._notify("warning", text)
    def error(self, text: str): self._notify("error", text)

    def _notify(self, kind: str, text: str):
        def keys(_): raise urwid.ExitMainLoop()
        body = urwid.Filler(urwid.Text((kind, text), align="center"), valign="middle")
        self._run_modal(body, len(text) + 8, 5, attr=kind, handler=keys)

    def checklist(self, prompt: str, options: list[str]) -> list[str]:
        result = []
        checkboxes = [urwid.CheckBox(opt, state=False) for opt in options]
        walker = urwid.SimpleFocusListWalker(checkboxes)
        listbox = urwid.ListBox(walker)
        listbox._command_map['enter'] = None

        def keys(k):
            if k == "enter":
                for cb in checkboxes:
                    if cb.get_state():
                        result.append(cb.get_label())
                raise urwid.ExitMainLoop()
            elif k == "esc":
                raise urwid.ExitMainLoop()

        pile = urwid.Pile([
            urwid.Text(prompt, align="center"),
            urwid.Divider(),
            urwid.BoxAdapter(listbox, height=min(len(options), 10)),
            urwid.Divider(),
            urwid.Text(("footer", "[space] toggle  [enter] confirm  [esc] cancel"), align="center")
        ])
        self._run_modal(pile, 60, height='pack', attr="prompt", handler=keys)
        return result

    async def confirm_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.confirm, *args, **kwargs)

    async def input_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.input, *args, **kwargs)

    async def password_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.password, *args, **kwargs)

    async def choose_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.choose, *args, **kwargs)

    async def checklist_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.checklist, *args, **kwargs)


# ── Self-Test ───────────────────────────────────────

if __name__ == "__main__":
    ui = Modal(theme="default")
    ui.toast("Launching modal test...", duration=1.5)

    if not ui.confirm("Run all modal tests?", timeout=10):
        exit()

    print("→ input:", ui.input("Enter your name:"))
    print("→ password:", ui.password("Enter secret:"))
    print("→ multiline:", ui.input_multiline("Describe yourself:"))
    print("→ single choice:", ui.choose("Pick one:", ["Dog", "Cat", "Bird"]))
    print("→ checklist:", ui.checklist("Select all:", ["Red", "Green", "Blue"]))

    print("→ timed confirm:", ui.confirm("Respond Y/N within 5s", timeout=5))
    print("→ timed input:", ui.input("Type fast!", timeout=5))

    ui.info("This is info")
    ui.warning("This is a warning")
    ui.error("This is an error")

    if ui.confirm("End test?", timeout=6):
        print("Goodbye.")

