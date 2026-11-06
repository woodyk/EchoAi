"""Small embeddable Urwid panels; no panel starts a nested terminal loop."""

import urwid


class Panel(urwid.WidgetWrap):
    def __init__(self, title, widgets, close, actions=()):
        self.close = close
        self.status = urwid.Text("")
        self.walker = urwid.SimpleFocusListWalker(list(widgets))
        self.listbox = urwid.ListBox(self.walker)
        buttons = [urwid.AttrMap(urwid.Button(label, on_press=lambda _, fn=fn: self.invoke(fn)),
                                "button", "button_focused") for label, fn in actions]
        buttons.append(urwid.AttrMap(urwid.Button("Close", on_press=lambda _: close(cancel=True)),
                                    "button", "button_focused"))
        body = urwid.Pile([
            ("weight", 1, self.listbox),
            ("pack", self.status),
            ("pack", urwid.Divider()),
            ("pack", urwid.Columns(buttons, dividechars=1)),
        ])
        super().__init__(urwid.LineBox(urwid.Padding(body, left=1, right=1), title=title))

    def invoke(self, callback):
        try:
            callback()
        except Exception as error:
            self.status.set_text(("error", str(error)))

    def keypress(self, size, key):
        if key == "esc":
            self.close(cancel=True)
            return None
        if key in {"tab", "shift tab"}:
            pile = self._w.base_widget
            selectable = [i for i, widget in enumerate(self.walker) if widget.selectable()]
            if pile.focus_position != 0:
                if selectable:
                    pile.focus_position = 0
                    self.walker.set_focus(selectable[-1] if key == "shift tab" else selectable[0])
            elif selectable:
                current = self.walker.focus
                candidates = [i for i in selectable if i < current] if key == "shift tab" else [
                    i for i in selectable if i > current]
                if candidates:
                    self.walker.set_focus(candidates[-1] if key == "shift tab" else candidates[0])
                else:
                    pile.focus_position = 3
            else:
                pile.focus_position = 3
            return None
        return super().keypress(size, key)


class FormPanel(Panel):
    def __init__(self, title, values, save, close, multiline=()):
        self.save = save
        self.fields = {}
        widgets = []
        for name, value in values.items():
            if isinstance(value, bool):
                field = urwid.CheckBox(name, state=value)
                widgets.append(urwid.AttrMap(field, "edit", "edit_focused"))
            else:
                widgets.append(urwid.Text(("secondary", name)))
                field = urwid.Edit(edit_text=str(value or ""), multiline=name in multiline)
                widgets.append(urwid.AttrMap(field, "edit", "edit_focused"))
            self.fields[name] = field
            widgets.append(urwid.Divider())
        super().__init__(title, widgets, close, actions=[("Save", lambda: save(self.values()))])

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
        super().__init__(title, [], close)
        self._w = urwid.LineBox(urwid.Padding(urwid.Pile([
            ("pack", self.query), ("pack", urwid.Divider()),
            ("weight", 1, self.options_box), ("pack", self.status),
            ("pack", urwid.Text("Enter selects · Esc cancels")),
        ]), left=1, right=1), title=title)
        self._w.base_widget.focus_position = 2
        urwid.connect_signal(self.query, "change", lambda _, text: self.refresh(text))
        self.refresh("")
        if current in self.choices:
            self.options.set_focus(self.choices.index(current))

    def refresh(self, query):
        self.filtered = [value for value in self.choices if query.casefold() in value.casefold()]
        self.options[:] = [urwid.AttrMap(urwid.Button(value, on_press=lambda _, value=value: self.invoke(
            lambda: self.select(value))), "button", "button_focused") for value in self.filtered]
        if not self.options:
            self.options.append(urwid.Text("No matches."))

    def keypress(self, size, key):
        if key in {"tab", "shift tab"}:
            pile = self._w.base_widget
            pile.focus_position = 2 if pile.focus_position == 0 else 0
            return None
        if key == "/" and self._w.base_widget.focus_position != 0:
            self._w.base_widget.focus_position = 0
            return None
        if key == "enter" and self._w.base_widget.focus_position == 0:
            self._w.base_widget.focus_position = 2
            return None
        result = super().keypress(size, key)
        if self.preview and self.filtered and key in ("up", "down"):
            self.invoke(lambda: self.preview(self.filtered[self.options.focus]))
        return result


class ControllerPanel(urwid.WidgetWrap):
    """Embed an existing standalone browser using its own key routing, without run()."""

    def __init__(self, controller, close):
        self.controller = controller
        self.close = close
        super().__init__(controller.loop.widget)

    def keypress(self, size, key):
        try:
            unhandled = self.controller.loop.widget.keypress(size, key)
            if unhandled is not None:
                self.controller.loop.unhandled_input(unhandled)
            self._w = self.controller.loop.widget
        except urwid.ExitMainLoop:
            self.close()
        except Exception as error:
            footer = getattr(self.controller, "footer_text", None)
            if footer is not None:
                footer.set_text(("error", str(error)))
            else:
                raise
        return None
