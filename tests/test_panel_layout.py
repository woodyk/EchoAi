"""Verify shared panel chrome and real keyboard/mouse activation of footer actions."""

from pathlib import Path
import re
import unittest
from unittest.mock import patch

import urwid
import test_app as app_tests
from test_session_cli import main
from echoai.tui.panels import Panel, FormPanel, ChoicePanel, ActionBar
from echoai.tools import task_manager


class PanelLayoutTests(unittest.TestCase):
    def setUp(self):
        self.fixture = app_tests.AppTests('test_unknown_command_does_not_reach_provider')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.app = self.fixture.app

    def open(self, method):
        getattr(self.app, method)()
        if self.app.busy:
            self.fixture.drain()
        return self.app.overlay

    def activate(self, label, key='enter', size=(90, 26)):
        panel = self.app.overlay
        panel.render(size, True)
        panel.focus_actions(list(panel.actions.buttons).index(label))
        panel.keypress(size, key)

    def click(self, label, size=(90, 26)):
        panel = self.app.overlay
        rows = [line.decode() for line in panel.render(size, True).text]
        for y in range(len(rows) - 1, -1, -1):
            x = rows[y].find('< ' + label)
            if x >= 0:
                panel.mouse_event(size, 'mouse press', 1, x + 3, y, True)
                return
        self.fail('Footer button was not rendered: ' + label)

    def input_text(self, text):
        panel = self.app.overlay
        panel.controller_walker[0].base_widget.set_edit_text(text)

    def test_every_menu_uses_same_template_and_centered_equal_width_actions(self):
        for label, method in self.app.MENU:
            panel = self.open(method)
            self.assertIsInstance(panel, Panel)
            self.assertEqual(panel.hint.text, Panel.HINT)
            for width, height in [(100, 30), (70, 24), (40, 24)]:
                with self.subTest(menu=label, width=width):
                    rows = [line.decode() for line in panel.render((width, height), True).text]
                    self.assertEqual(len(rows), height)
                    self.assertTrue(rows[0].startswith('┌'))
                    self.assertTrue(rows[-1].endswith('┘'))
                    self.assertIn('< ', rows[-2], 'Actions must stay directly above the bottom border')
                    footer_start = next(i for i, line in enumerate(rows[1:], 1) if '──────' in line)
                    rendered_footer = '\n'.join(rows[footer_start:-1])
                    for name in panel.actions.buttons:
                        self.assertIn('< ' + name, rendered_footer)
                    for row in rows[footer_start:-1]:
                        cells = list(re.finditer(r'<[^>]*>', row))
                        if cells:
                            self.assertEqual({len(cell.group()) for cell in cells}, {ActionBar.CELL_WIDTH})
                            self.assertLessEqual(abs(cells[0].start() - (width - cells[-1].end())), 1)
                            for left, right in zip(cells, cells[1:]):
                                self.assertEqual(right.start() - left.end(), 2)
                    self.assertNotIn('…', rendered_footer)
            self.app.close_overlay(cancel=True)

    def test_tab_and_shift_tab_reach_every_enabled_footer_button(self):
        for label, method in self.app.MENU:
            panel = self.open(method)
            names = [name for name, button in panel.actions.buttons.items() if button.enabled]
            panel.focus_actions()
            seen = []
            for _ in names:
                seen.append(panel.actions.focus.base_widget.get_label())
                panel.keypress((90, 26), 'tab')
            self.assertEqual(seen, names, label)
            panel.focus_actions(list(panel.actions.buttons).index(names[-1]))
            reverse = []
            for _ in names:
                reverse.append(panel.actions.focus.base_widget.get_label())
                panel.keypress((90, 26), 'shift tab')
            self.assertEqual(reverse, list(reversed(names)), label)
            self.app.close_overlay(cancel=True)

    def test_form_footer_save_and_mouse_cancel(self):
        panel = self.open('show_prompt_manager')
        panel.fields['system_prompt'].set_edit_text('Saved with footer')
        self.activate('Save', key=' ')
        self.assertEqual(self.app.CONFIG['system_prompt'], 'Saved with footer')
        self.assertIsNone(self.app.overlay)
        panel = self.open('show_settings')
        panel.fields['username'].set_edit_text('Discarded')
        self.click('Cancel', size=(40, 24))
        self.assertEqual(self.app.CONFIG['username'], 'User')
        self.assertIsNone(self.app.overlay)

    def test_choice_select_and_mouse_cancel_restore_theme(self):
        panel = self.open('show_model_selector')
        panel.options.set_focus(panel.filtered.index('ollama:local'))
        self.activate('Select')
        self.assertEqual(self.app.CONFIG['model'], 'ollama:local')
        panel = self.open('show_theme_manager')
        old = self.app.CONFIG['theme']
        panel.preview('night')
        self.click('Cancel')
        self.assertEqual(self.app.theme_manager.get_current_theme_name(), old)
        panel = self.open('show_theme_manager')
        panel.options.set_focus(panel.filtered.index('dark'))
        self.activate('Select')
        self.assertEqual(self.app.CONFIG['theme'], 'dark')

    def test_no_matches_disables_select_and_skips_it_in_focus_order(self):
        panel = self.open('show_model_selector')
        panel.query.set_edit_text('nothing matches')
        self.assertFalse(panel.actions.buttons['Select'].enabled)
        self.activate('Select')
        self.assertIs(self.app.overlay, panel)
        self.assertEqual(self.app.CONFIG['model'], 'openai:gpt-4o')
        panel.focus_first()
        for _ in range(8):
            panel.keypress((40, 24), 'tab')
            if panel.layout.focus_position == 'footer':
                self.assertEqual(panel.actions.focus.base_widget.get_label(), 'Cancel')
        self.click('Cancel', size=(40, 24))
        self.assertIsNone(self.app.overlay)

    def test_files_footer_open_up_and_close(self):
        root = Path(self.fixture.fixture.temp.name)
        folder = root / 'folder'
        folder.mkdir()
        path = folder / 'file with spaces.txt'
        path.write_text('Attached from bottom button')
        path = path.resolve()
        self.app.show_file_explorer(start_path=folder)
        panel = self.app.overlay
        panel.walker.set_focus(panel.entries.index(path) + 2)
        with patch.object(main, 'extract_text', side_effect=lambda path: Path(path).read_text()):
            self.activate('Open')
            self.fixture.drain()
        self.assertIn('Attached from bottom button', self.app.edit.edit_text)
        self.app.show_file_explorer(start_path=folder)
        self.activate('Up')
        self.assertEqual(self.app.overlay.path, root.resolve())
        self.activate('Close')
        self.assertIsNone(self.app.overlay)

    def test_session_footer_new_rename_details_preview_and_close(self):
        panel = self.open('show_session_manager')
        self.activate('New')
        self.input_text('Created by footer')
        self.activate('Create')
        controller = panel.controller
        self.assertEqual(controller.mode, 'main')
        sid = controller.filtered_sessions[controller.current_index]['id']
        self.assertEqual(self.app.SESSION.load_full(sid)['name'], 'Created by footer')
        self.activate('Rename')
        self.input_text('Renamed by footer')
        self.activate('Save')
        self.assertEqual(self.app.SESSION.load_full(sid)['name'], 'Renamed by footer')
        self.activate('Details')
        controller.edit_widgets['tags'].set_edit_text('one,two')
        self.activate('Save')
        self.assertEqual(controller.mode, 'main')
        self.assertEqual(self.app.SESSION.load_full(sid)['tags'], ['one', 'two'])
        self.activate('Preview')
        self.assertEqual(controller.mode, 'preview')
        self.activate('Back')
        self.activate('Close')
        self.assertIsNone(self.app.overlay)

    def test_session_search_delete_confirmation_and_load_footer(self):
        panel = self.open('show_session_manager')
        self.activate('Search')
        self.input_text('Project')
        self.activate('Search')
        self.assertEqual(len(panel.controller.filtered_sessions), 1)
        self.activate('Delete')
        self.assertEqual(panel.controller.mode, 'delete_confirm')
        self.activate('Cancel')
        self.assertEqual(len(self.app.SESSION.list()), 1)
        self.activate('Load')
        self.assertIsNone(self.app.overlay)
        self.assertEqual(self.app.AI.session_id, self.fixture.fixture.existing_id)
        panel = self.open('show_session_manager')
        self.activate('Delete')
        self.activate('Delete')
        self.assertEqual(self.app.SESSION.list(), [])
        self.assertFalse(panel.actions.buttons['Load'].enabled)
        self.activate('Close')
        self.assertIsNone(self.app.AI.session_id)

    def test_task_footer_crud_filter_sort_and_search(self):
        panel = self.open('show_task_manager')
        self.assertFalse(panel.actions.buttons['Edit'].enabled)
        self.activate('New')
        self.input_text('Task from footer')
        self.activate('Create')
        task = task_manager.task_list()['result'][0]
        self.activate('Edit')
        panel.controller.edit_widgets['notes'].set_edit_text('First line\nSecond line')
        self.activate('Save')
        self.assertEqual(panel.controller.mode, 'main')
        self.assertEqual(task_manager.task_list()['result'][0]['notes'], 'First line\nSecond line')
        self.activate('Mark done')
        self.assertEqual(task_manager.task_list()['result'][0]['status'], 'done')
        self.assertIn('Reopen', panel.actions.buttons)
        self.activate('Hide done')
        self.assertFalse(panel.actions.buttons['Edit'].enabled)
        self.activate('Show done')
        self.activate('Reopen')
        self.assertEqual(task_manager.task_list()['result'][0]['status'], 'pending')
        self.activate('Oldest')
        self.assertTrue(panel.controller.sort_ascending)
        self.activate('Search')
        self.input_text('Task from footer')
        self.activate('Search')
        self.assertEqual(panel.controller.filtered_tasks[0]['id'], task['id'])
        self.activate('Delete')
        self.activate('Cancel')
        self.assertEqual(len(task_manager.task_list()['result']), 1)
        self.activate('Delete')
        self.activate('Delete')
        self.assertEqual(task_manager.task_list()['result'], [])
        self.activate('Close')
        self.assertIsNone(self.app.overlay)

    def test_validation_errors_keep_form_and_action_bar_usable(self):
        for method in ('show_session_manager', 'show_task_manager'):
            panel = self.open(method)
            self.activate('New')
            self.input_text(' ')
            self.activate('Create')
            self.assertIn(panel.controller.mode, {'new'})
            self.assertTrue(panel.status.text)
            panel.render((40, 24), True)
            self.activate('Cancel')
            self.assertEqual(panel.controller.mode, 'main')
            self.activate('Close')

    def test_memory_and_tools_footer_buttons_use_shared_actions(self):
        panel = self.open('show_memory_manager')
        self.activate('Enable')
        self.fixture.drain()
        panel = self.open('show_memory_manager')
        panel.editor.set_edit_text('Footer memory')
        self.activate('Remember')
        self.fixture.drain()
        self.assertIn('Footer memory', self.app.MEMORY.records)
        self.activate('Recall')
        self.fixture.drain()
        self.assertIn('Memory Search Results', self.fixture.text())
        self.activate('Close')
        panel = self.open('show_tool_manager')
        panel.fields['example'].set_state(False)
        self.activate('Apply')
        self.assertTrue(self.app.AI.functions[0]['function']['disabled'])

    def test_keyboard_navigation_and_mouse_selection_match_controller_actions(self):
        for i in range(20):
            self.app.SESSION.create(f'Extra session {i}')
        panel = self.open('show_session_manager')
        panel.focus_first()
        panel.keypress((90, 26), 'down')
        self.assertEqual(panel.controller.current_index, 1)
        panel.keypress((90, 26), 'page down')
        self.assertEqual(panel.controller.current_index, 11)
        sid = panel.controller.filtered_sessions[11]['id']
        self.activate('Load')
        self.assertEqual(self.app.AI.session_id, sid)
        panel = self.open('show_session_manager')
        rows = [line.decode() for line in panel.render((90, 26), True).text]
        selected = panel.controller.filtered_sessions[2]
        row = next(i for i, line in enumerate(rows) if selected['name'] in line)
        panel.mouse_event((90, 26), 'mouse press', 1, 10, row, True)
        self.activate('Load')
        self.assertEqual(self.app.AI.session_id, selected['id'])


if __name__ == '__main__':
    unittest.main()
