"""Shared panel chrome, responsive actions, and focus routing for the TUI."""

import urwid


class ActionButton(urwid.Button):
    """A disabled action stays visible and cannot be activated by mouse or keyboard."""
    def __init__(self, label, callback, enabled=True):
        self.enabled = enabled
        super().__init__(label, on_press=lambda _: callback() if self.enabled else None)

    def selectable(self):
        return self.enabled

    def keypress(self, size, key):
        return super().keypress(size, key) if self.enabled else key

    def mouse_event(self, size, event, button, col, row, focus):
        return super().mouse_event(size, event, button, col, row, focus) if self.enabled else False


class ActionBar(urwid.GridFlow):
    """Equal-width, centered action cells that wrap together as the terminal narrows."""
    CELL_WIDTH = 16

    def __init__(self, actions, invoke):
        self.buttons = {}
        cells = []
        for action in actions:
            label, callback = action[:2]
            enabled = action[2] if len(action) > 2 else True
            button = ActionButton(label, lambda callback=callback: invoke(callback), enabled)
            self.buttons[label] = button
            cells.append(urwid.AttrMap(button, "button" if enabled else "disabled", "button_focused"))
        super().__init__(cells, cell_width=self.CELL_WIDTH, h_sep=2, v_sep=1, align="center")

    def indices(self):
        return [i for i, (widget, _) in enumerate(self.contents) if widget.selectable()]


class PanelBody(urwid.WidgetWrap):
    def __init__(self, widget, key_handler):
        self.key_handler = key_handler
        super().__init__(widget)

    def keypress(self, size, key):
        return self.key_handler(self._w.keypress, size, key)


class Panel(urwid.WidgetWrap):
    """One border, padding, scrollable body, status, help, and pinned action bar."""
    HINT = "Tab: next · Shift+Tab: previous · Esc: cancel"

    def __init__(self, title, widgets, close, actions=(), close_label="Close", body=None):
        self.title = title
        self.close = close
        self.close_label = close_label
        self.status = urwid.Text("")
        self.hint = urwid.Text(("footer", self.HINT), align="center")
        self.walker = urwid.SimpleFocusListWalker(list(widgets))
        self.listbox = urwid.ListBox(self.walker)
        self.body = body if body is not None else self.listbox
        self.footer = urwid.Pile([])
        self.body_proxy = PanelBody(self.body, self._body_keypress_impl)
        self.layout = urwid.Frame(self.body_proxy, footer=self.footer)
        super().__init__(urwid.LineBox(urwid.Padding(self.layout, left=2, right=2), title=title))
        self.set_actions(actions)
        self.focus_first()

    def set_actions(self, actions, include_close=True):
        previous = None
        if hasattr(self, "actions") and self.actions.contents:
            previous = self.actions.focus.base_widget.get_label()
        actions = list(actions)
        if include_close:
            actions.append((self.close_label, lambda: self.close(cancel=True)))
        self.actions = ActionBar(actions, self.invoke)
        self.footer.contents = [(widget, self.footer.options("pack")) for widget in (
            urwid.Divider("─"), self.status, self.hint, self.actions)]
        self.footer.focus_position = 3
        if previous in self.actions.buttons and self.actions.buttons[previous].enabled:
            self.actions.focus_position = list(self.actions.buttons).index(previous)
        elif self.actions.indices():
            self.actions.focus_position = self.actions.indices()[0]

    def invoke(self, callback):
        try:
            return callback()
        except Exception as error:
            self.status.set_text(("error", str(error)))

    def _body_targets(self):
        targets = [i for i, widget in enumerate(self.walker) if widget.selectable()]
        # A read-only list still needs a focus stop so it can be scrolled.
        return targets or [None]

    def _body_focus(self):
        return self.walker.focus if self.walker and any(w.selectable() for w in self.walker) else None

    def _set_body_focus(self, target):
        if target is not None:
            self.walker.set_focus(target)

    def focus_first(self):
        self.layout.focus_position = "body"
        self._set_body_focus(self._body_targets()[0])

    def focus_actions(self, index=None):
        indices = self.actions.indices()
        if not indices:
            return
        self.layout.focus_position = "footer"
        self.footer.focus_position = 3
        self.actions.focus_position = indices[0] if index is None else index

    def _move_focus(self, reverse=False):
        targets = [("body", target) for target in self._body_targets()]
        targets += [("footer", index) for index in self.actions.indices()]
        current = (("footer", self.actions.focus_position) if self.layout.focus_position == "footer"
                   else ("body", self._body_focus()))
        index = targets.index(current) if current in targets else 0
        region, target = targets[(index + (-1 if reverse else 1)) % len(targets)]
        if region == "footer":
            self.focus_actions(target)
        else:
            self.layout.focus_position = "body"
            self._set_body_focus(target)

    def keypress(self, size, key):
        if key == "esc":
            self.invoke(lambda: self.close(cancel=True))
            return None
        if key in {"tab", "shift tab"}:
            self._move_focus(reverse=key == "shift tab")
            return None
        return super().keypress(size, key)

    def _body_keypress_impl(self, original, size, key):
        return original(size, key)


class FormPanel(Panel):
    def __init__(self, title, values, save, close, multiline=()):
        self.save = save
        self.fields = {}
        widgets = []
        for name, value in values.items():
            if isinstance(value, bool):
                field = urwid.CheckBox(name, state=value)
            else:
                widgets.append(urwid.Text(("secondary", name)))
                field = urwid.Edit(edit_text=str(value or ""), multiline=name in multiline)
            widgets.append(urwid.AttrMap(field, "edit", "edit_focused"))
            self.fields[name] = field
            widgets.append(urwid.Divider())
        super().__init__(title, widgets, close, actions=[("Save", self._save)], close_label="Cancel")

    def values(self):
        return {name: field.get_state() if isinstance(field, urwid.CheckBox) else field.edit_text
                for name, field in self.fields.items()}

    def keypress(self, size, key):
        if key == "ctrl s":
            self.invoke(self._save)
            return None
        return super().keypress(size, key)

    def _save(self):
        self.save(self.values())


class ChoicePanel(Panel):
    def __init__(self, title, choices, select, close, preview=None, current=None):
        self.choices = list(choices)
        self.select = select
        self.preview = preview
        self.query = urwid.Edit("Search: ")
        self.options = urwid.SimpleFocusListWalker([])
        self.options_box = urwid.ListBox(self.options)
        self.choice_body = urwid.Frame(self.options_box,
            header=urwid.Pile([self.query, urwid.Divider()]))
        self.filtered = []
        super().__init__(title, [], close, close_label="Cancel", body=self.choice_body)
        urwid.connect_signal(self.query, "change", lambda _, text: self.refresh(text))
        self.refresh("")
        if current in self.filtered:
            self.options.set_focus(self.filtered.index(current))
        self.choice_body.focus_position = "body"

    def _body_targets(self):
        return ["query", "options"]

    def _body_focus(self):
        return "query" if self.choice_body.focus_position == "header" else "options"

    def _set_body_focus(self, target):
        self.choice_body.focus_position = "header" if target == "query" else "body"

    def refresh(self, query):
        self.filtered = [value for value in self.choices if query.casefold() in value.casefold()]
        self.options[:] = [urwid.AttrMap(urwid.Button(value, on_press=lambda _, value=value:
            self.invoke(lambda: self.select(value))), "button", "button_focused") for value in self.filtered]
        if not self.options:
            self.options.append(urwid.Text("No matches."))
        self.set_actions([("Select", self.select_current, bool(self.filtered))])

    def select_current(self):
        if self.filtered:
            self.select(self.filtered[self.options.focus])

    def keypress(self, size, key):
        if key == "/" and self.layout.focus_position == "body" and self._body_focus() != "query":
            self.choice_body.focus_position = "header"
            return None
        if key == "enter" and self.layout.focus_position == "body" and self._body_focus() == "query":
            self.choice_body.focus_position = "body"
            return None
        result = super().keypress(size, key)
        if self.preview and self.filtered and self.layout.focus_position == "body" and self._body_focus() == "options" and key in ("up", "down"):
            self.invoke(lambda: self.preview(self.filtered[self.options.focus]))
        return result


class ControllerPanel(Panel):
    """Wrap a session/task controller in the same template without a nested loop."""
    def __init__(self, controller, close, title=None):
        self.controller = controller
        self.finished = close
        self.is_session = hasattr(controller, "session_mgr")
        self.source_key = None
        self.controller_walker = None
        self.last_mode = None
        super().__init__(title or ("Sessions · /session" if self.is_session else "Tasks · /task"),
                         [], self._cancel)
        self.sync()

    def _cancel(self, cancel=False):
        self.send("esc")

    def _body_targets(self):
        if self.controller_walker is not None and self.controller.mode in {"info", "edit"}:
            return [i for i, widget in enumerate(self.controller_walker) if widget.selectable()] or [None]
        return [None]

    def _body_focus(self):
        if self.controller_walker is not None and self.controller.mode in {"info", "edit"}:
            return self.controller_walker.focus
        return None

    def _set_body_focus(self, target):
        if target is not None and self.controller_walker is not None:
            self.controller_walker.set_focus(target)

    def sync(self):
        controller = self.controller
        widget = controller.loop.widget
        mode = controller.mode
        source = widget.body if isinstance(widget, urwid.Frame) else widget
        rows = controller.filtered_sessions if self.is_session else controller.filtered_tasks
        if mode == "main":
            walker = self._selection_walker()
            for widget in walker:
                if isinstance(widget, urwid.AttrMap) and not widget.selectable():
                    widget.original_widget = urwid.SelectableIcon(widget.base_widget.text, cursor_position=0)
        key = (id(source), mode, bool(rows))
        if key != self.source_key:
            if isinstance(widget, urwid.Overlay):
                # Input overlays use the same form body and the shared footer,
                # rather than nesting another border/header/action area.
                self.controller_walker = urwid.SimpleFocusListWalker([widget.top_w.base_widget])
                source = urwid.ListBox(self.controller_walker)
            else:
                self.controller_walker = getattr(source, "body", None)
                if mode == "main" and not rows:
                    source = urwid.Filler(urwid.Text("No items found. Use New or Search."), valign="top")
            self.body = source
            self.body_proxy._w = source
            self.source_key = key
        footer = controller.footer_text.text
        self.status.set_text(footer if not footer.startswith("[") else "")
        if mode in {"delete", "delete_confirm"}:
            self.status.set_text(("warning", "Delete the selected item?"))
        self.set_actions(self._controller_actions(), include_close=False)
        if mode != self.last_mode:
            self.focus_first()
        self.last_mode = mode

    def _selection_walker(self):
        return self.controller.body_widget if self.is_session else self.controller.body_walker

    def mouse_event(self, size, event, button, col, row, focus):
        handled = super().mouse_event(size, event, button, col, row, focus)
        if event == "mouse press" and button == 1 and self.layout.focus_position == "body" and self.controller.mode == "main":
            walker = self._selection_walker()
            if walker:
                self.controller.current_index = walker.focus
                build = self.controller.build_session_list if self.is_session else self.controller.build_task_list
                walker[:] = build()
                walker.set_focus(self.controller.current_index)
                self.sync()
        return handled

    def _controller_actions(self):
        mode = self.controller.mode
        if mode == "main":
            rows = self.controller.filtered_sessions if self.is_session else self.controller.filtered_tasks
            if self.is_session:
                values = [("Load", "enter", bool(rows)), ("New", "n", True), ("Rename", "r", bool(rows)),
                          ("Details", "right", bool(rows)), ("Preview", "v", bool(rows)),
                          ("Search", "/", True), ("Delete", "d", bool(rows))]
            else:
                selected = rows[self.controller.current_index] if rows else {}
                mark = "Reopen" if selected.get("status") == "done" else "Mark done"
                values = [("Edit", "enter", bool(rows)), ("New", "n", True), (mark, "m", bool(rows)),
                          ("Search", "/", True), ("Hide done" if self.controller.show_completed else "Show done", "c", True),
                          ("Newest" if self.controller.sort_ascending else "Oldest", "s", True), ("Delete", "d", bool(rows))]
            values.append(("Close", "esc", True))
        elif mode in {"delete", "delete_confirm"}:
            values = [("Delete", "y", True), ("Cancel", "n", True)]
        elif mode == "preview":
            values = [("Back", "esc", True)]
        else:
            label = "Search" if mode == "search" else "Create" if mode == "new" else "Save"
            values = [(label, "enter", True), ("Cancel", "esc", True)]
        return [(label, lambda key=key: self.send(key, finish_edit=True), enabled)
                for label, key, enabled in values]

    def send(self, key, finish_edit=False):
        try:
            if self.controller.mode == "main":
                walker = self._selection_walker()
                if walker:
                    self.controller.current_index = walker.focus
            self.controller.loop.unhandled_input(key)
            if finish_edit and key == "enter" and self.controller.mode in {"edit", "info"} and self.controller.footer_text.text.startswith("✓"):
                self.controller.return_to_main()
            self.sync()
        except urwid.ExitMainLoop:
            self.finished()
        except Exception as error:
            self.status.set_text(("error", str(error)))

    def _body_keypress_impl(self, original, size, key):
        if self.controller.mode == "main" and key in {"up", "down", "j", "k", "page up", "page down"}:
            direction = "up" if key in {"up", "k", "page up"} else "down"
            for _ in range(10 if key.startswith("page ") else 1):
                self.send(direction)
            return None
        unhandled = original(size, key)
        if unhandled is not None:
            self.send(unhandled)
        return None

    def keypress(self, size, key):
        if key == "ctrl s" and self.controller.mode in {"new", "rename", "info", "edit"}:
            self.send("enter", finish_edit=True)
            return None
        return super().keypress(size, key)
