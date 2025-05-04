#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: task_manager.py
# Description: Urwid-based Task Manager TUI for EchoAI
# Author: Ms. White
# Created: 2025-05-03
# Modified: 2025-05-03 23:37:42

import urwid
from echoai.tools.task_manager import (
    task_list, task_add, task_update, task_delete, task_complete
)
from echoai.tui.tui_layout import get_theme_palette, DynamicHeader

class TaskManager:
    def __init__(self, theme_name="default"):
        # Load theme
        self.palette, self.theme = get_theme_palette(theme_name)

        # Task data and filters
        self.tasks = self.load_tasks()
        self.active_query = ""
        self.show_completed = True
        self.sort_ascending = False  # False = newest→oldest
        self.filtered_tasks = []
        self.current_index = 0

        # UI state
        self.mode = 'main'
        self.input_text = ''
        self.edit_widgets = {}
        self.edit_focus = None

        # Header & Footer
        self.header_obj = DynamicHeader("Task Manager")
        self.header = self.header_obj.get_widget()
        self.footer_text = urwid.Text('', align='center')
        self.footer = urwid.AttrMap(self.footer_text, 'footer')

        # Main list body
        self.body_walker = urwid.SimpleFocusListWalker([])
        self.body = urwid.ListBox(self.body_walker)

        # Frame & Loop
        self.main_frame = urwid.Frame(
            header=self.header,
            body=self.body,
            footer=self.footer
        )
        self.screen = urwid.raw_display.Screen()
        self.screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            self.main_frame,
            self.palette,
            screen=self.screen,
            unhandled_input=self.handle_input
        )

        # Initial load
        self.refresh_tasks()
        self.update_footer()

    def load_tasks(self):
        result = task_list()
        return result.get('result', [])

    def apply_filters(self):
        # Start from full list
        tasks = list(self.tasks)
        # Completed toggle: hide tasks marked 'done'
        if not self.show_completed:
            tasks = [t for t in tasks if t.get('status','').lower() != 'done']
        # Search filter
        if self.active_query:
            q = self.active_query.lower()
            def match(t):
                for field in ('content','tag','notes'):
                    if q in (t.get(field,'') or '').lower():
                        return True
                return False
            tasks = [t for t in tasks if match(t)]
        # Sort
        tasks.sort(key=lambda t: t.get('created',''), reverse=not self.sort_ascending)
        return tasks

    def refresh_tasks(self):
        self.tasks = self.load_tasks()
        self.filtered_tasks = self.apply_filters()
        # Clamp selection
        if self.filtered_tasks:
            self.current_index = min(self.current_index, len(self.filtered_tasks)-1)
        else:
            self.current_index = 0
        self.body_walker[:] = self.build_task_list()

    def build_task_list(self):
        items = []
        for idx, t in enumerate(self.filtered_tasks):
            content = (t.get('content','') or '').splitlines()[0][:50]
            status = t.get('status','')
            tag = t.get('tag','') or ''
            sid = t.get('id','')
            label = f"{content} [{status}]{(' '+tag) if tag else ''} ({sid})"
            prefix = '→ ' if idx == self.current_index else '  '
            txt = urwid.Text(prefix + label)
            style = 'highlight' if idx == self.current_index else 'default'
            items.append(urwid.AttrMap(txt, style))
        return items

    def build_editable_task_view(self, task):
        # Editable fields
        content = task.get('content','') or ''
        tag = task.get('tag','') or ''
        notes = task.get('notes','') or ''
        current_status = task.get('status','').lower()
        self.edit_widgets = {
            'content': urwid.Edit(('prompt','Content: '), content),
            'tag':     urwid.Edit(('prompt','Tag:     '), tag),
            'status':  urwid.CheckBox('Complete', state=(current_status=='done')),
            'notes':   urwid.Edit(('prompt','Notes:\n'), notes, multiline=True)
        }
        meta = [
            urwid.Text(f"ID:      {task.get('id','') }"),
            urwid.Divider(),
            urwid.AttrMap(self.edit_widgets['content'], 'input'),
            urwid.AttrMap(self.edit_widgets['tag'], 'input'),
            urwid.AttrMap(self.edit_widgets['status'], 'input'),
            urwid.AttrMap(self.edit_widgets['notes'], 'input'),
            urwid.Divider(),
            urwid.Text(f"Created: {task.get('created','')}"),
            urwid.Text(f"Updated: {task.get('updated','')}"),
        ]
        self.edit_focus = urwid.SimpleFocusListWalker(meta)
        return urwid.ListBox(self.edit_focus)

    def build_input_overlay(self, prompt, default, callback):
        edit = urwid.Edit(('input', f"{prompt}: "), edit_text=default)
        wrapped = urwid.LineBox(
            urwid.Padding(urwid.AttrMap(edit,'input'), left=1, right=1)
        )
        overlay = urwid.Overlay(
            urwid.Filler(wrapped), self.main_frame,
            align='center', width=('relative',75),
            valign='middle', height=3
        )
        def handler(key):
            if key=='enter':
                self.input_text = edit.edit_text.strip()
                callback(self.input_text)
                self.return_to_main()
            elif key=='esc':
                self.return_to_main()
        return overlay, handler

    def update_footer(self):
        msgs = {
            'main':    '[↑↓] [n]ew [d]elete [m]ark [/] search [c]ompleted [s]ort [enter] edit [esc]exit',
            'new':     '[enter] add [esc] cancel',
            'delete':  '[y] confirm [n/esc] cancel',
            'edit':    '[↑↓/tab] nav [enter] save [esc] cancel',
            'search':  '[enter] filter [esc] cancel',
        }
        self.footer_text.set_text(('footer', msgs.get(self.mode, '')))

    def return_to_main(self):
        self.refresh_tasks()
        self.mode = 'main'
        self.main_frame.body = self.body
        self.loop.widget = self.main_frame
        self.loop.unhandled_input = self.handle_input
        self.update_footer()

    def search_tasks(self, query):
        self.active_query = query
        self.return_to_main()

    def handle_input(self, key):
        if key == 'window resize':
            cols, _ = self.screen.get_cols_rows()
            self.header_obj.resize(cols)
            return

        if self.mode == 'main':
            if key in ('up','k'):
                self.current_index = max(0, self.current_index-1)
            elif key in ('down','j'):
                self.current_index = min(len(self.filtered_tasks)-1, self.current_index+1)
            elif key == 'n':
                self.mode='new'; self.input_text=''
                overlay,handler=self.build_input_overlay("New task",'',self.add_task)
                self.loop.widget=overlay; self.loop.unhandled_input=handler; return
            elif key == 'd':
                self.mode='delete'; self.update_footer(); return
            elif key == 'm':
                if self.filtered_tasks:
                    task = self.filtered_tasks[self.current_index]
                    tid = task['id']
                    # toggle status between done and pending
                    current = task.get('status','').lower()
                    new_status = 'pending' if current == 'done' else 'done'
                    task_update(tid, {'status': new_status})
                    self.footer_text.set_text(('footer', f"✓ Task marked {new_status}"))
                    self.refresh_tasks()
                return
            elif key == '/':
                self.mode='search'
                overlay,handler=self.build_input_overlay("Search tasks",self.active_query,self.search_tasks)
                self.loop.widget=overlay; self.loop.unhandled_input=handler; return
            elif key == 'c':
                self.show_completed = not self.show_completed
                self.refresh_tasks(); return
            elif key == 's':
                self.sort_ascending = not self.sort_ascending
                self.refresh_tasks(); return
            elif key == 'enter':
                if not self.filtered_tasks: return
                self.mode='edit'
                self.main_frame.body = self.build_editable_task_view(self.filtered_tasks[self.current_index])
                self.loop.widget=self.main_frame; self.loop.unhandled_input=self.handle_input
                self.update_footer(); return
            elif key == 'esc':
                raise urwid.ExitMainLoop()
            self.body_walker[:] = self.build_task_list()

        elif self.mode == 'new':
            return
        elif self.mode == 'delete':
            if key.lower()=='y':
                if self.filtered_tasks:
                    task_delete(self.filtered_tasks[self.current_index]['id'])
                self.return_to_main()
            elif key.lower() in ('n','esc'):
                self.return_to_main()
        elif self.mode == 'edit':
            if key in ('tab','down'):
                pos=self.edit_focus.get_focus()[1]
                self.edit_focus.set_focus(min(len(self.edit_focus)-1,pos+1)); return
            elif key=='up':
                pos=self.edit_focus.get_focus()[1]
                self.edit_focus.set_focus(max(0,pos-1)); return
            elif key=='enter':
                task = self.filtered_tasks[self.current_index]
                tid=task['id']
                content=self.edit_widgets['content'].edit_text.strip()
                tag=self.edit_widgets['tag'].edit_text.strip()
                notes=self.edit_widgets['notes'].edit_text.strip()
                done = self.edit_widgets['status'].get_state()
                status = 'done' if done else 'pending'
                task_update(tid,{'content':content,'tag':tag,'notes':notes,'status':status})
                self.footer_text.set_text(('footer',"✓ Changes saved. Press ESC to return.")); return
            elif key=='esc':
                self.return_to_main()

    def add_task(self, content):
        if content:
            task_add(content)

    def run(self):
        self.loop.run()


def run_task_manager(theme="default"):
    tm = TaskManager(theme)
    tm.run()

if __name__=='__main__':
    run_task_manager('default')

