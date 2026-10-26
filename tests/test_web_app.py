import unittest
from unittest.mock import Mock, patch
from ui.web_app import Bridge, catalogue, document
from core.data import CATEGORIES


class WebTests(unittest.TestCase):
    def test_video_intro_keeps_header_visible_and_has_exit_fallback(self):
        page = document()
        self.assertIn('autoplay muted playsinline', page)
        self.assertIn('data:video/mp4;base64,', page)
        self.assertIn("addEventListener('ended',finishIntro", page)
        self.assertIn('setTimeout(finishIntro,10000)', page)
        self.assertIn('.app.intro-waiting{opacity:1;pointer-events:auto}', page)
        self.assertNotIn('class="app intro-waiting" inert', page)
        other = next(c for c in CATEGORIES if c['id'] == 'nirsoft')
        self.assertNotIn('USB Deview', [t['name'] for t in other['tools']])

    def test_requested_moves_and_script_commands(self):
        other = next(c for c in CATEGORIES if c['id'] == 'nirsoft')
        names = [t['name'] for t in other['tools']]
        self.assertEqual(names[names.index('Siege') + 1:], ['Eventvwr', 'ConsoleHostHistory'])
        scripts = next(c for c in CATEGORIES if c['id'] == 'scripts')
        for t in scripts['tools'][-3:]:
            self.assertTrue(t['run_as_admin'])
            self.assertTrue(t['cmd_command'].startswith('powershell '))
            self.assertNotIn('https\\:', t['cmd_command'])

    def test_nirsoft_archives_have_unique_admin_actions(self):
        category = next(c for c in CATEGORIES if c['id'] == 'nirsoft_utilities')
        self.assertEqual(len(category['tools']), 14)
        self.assertEqual(len({t['path'] for t in category['tools']}), 14)
        for t in category['tools']:
            self.assertTrue(t['archive'])
            self.assertTrue(t['run_as_admin'])
            self.assertTrue(t['url'].startswith('https://www.nirsoft.net/utils/'))
            self.assertTrue(t['url'].endswith('.zip'))
            self.assertEqual(Bridge()._tools[t['id']][1]['name'], t['name'])

    def test_spokwn_additions_keep_existing_ids_and_admin_launch(self):
        category = next(c for c in CATEGORIES if c['label'] == 'Spokwn')
        tools = {t['name']: t for t in category['tools']}
        self.assertEqual(len(tools), 9)
        self.assertEqual(tools['JournalTrace']['id'], 'redlotus:0')
        self.assertEqual(tools['KernelDumpTool']['id'], 'redlotus:1')
        for name in ('BAMParser', 'PrefetchParser', 'BAMDeletedKeys', 'ActivitiesCache', 'PathsParser', 'ProcessParser', 'PcaSvcExecuted'):
            self.assertTrue(tools[name]['run_as_admin'])
            self.assertTrue(tools[name]['url'].startswith('https://github.com/spokwn/'))
        self.assertNotIn('Espouken Tool', tools)

    def test_desktop_starts_movable_with_explicit_title_drag_region(self):
        import tempfile
        from ui.web_app import run
        from unittest.mock import MagicMock
        fake = MagicMock()
        fake.settings = {}
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict('sys.modules', {'webview': fake}), patch.dict('os.environ', {'LOCALAPPDATA': folder}):
                run()
        self.assertFalse(fake.create_window.call_args.kwargs['fullscreen'])
        self.assertTrue(fake.create_window.call_args.kwargs['frameless'])
        self.assertEqual(fake.settings['DRAG_REGION_SELECTOR'], '.pywebview-drag-region')
        self.assertTrue(fake.settings['DRAG_REGION_DIRECT_TARGET_ONLY'])

    def test_relocated_cards_keep_their_original_actions(self):
        bridge = Bridge()
        cards = [t for c in catalogue() for t in c['tools']]
        self.assertEqual(len({t['id'] for t in cards}), 123)
        for card in cards:
            self.assertEqual(bridge._tools[card['id']][1]['name'], card['name'])
        other = next(c for c in catalogue() if c['id'] == 'nirsoft')
        self.assertIn('P1AE Scanner', [t['name'] for t in other['tools']])
        siege = bridge._tools['siege'][1]
        self.assertTrue(siege['run_as_admin'])
        self.assertEqual(siege['url'], 'https://github.com/praiselily/Siege/releases/download/Scanner/Siege.exe')

    def test_progress_is_bounded_and_does_not_wait_for_renderer(self):
        bridge = Bridge()
        bridge._window = Mock()
        for n in range(1000):
            bridge._emit(dict(id='orbdiff:0', kind='progress', percent=n))
        bridge._emit(dict(id='orbdiff:0', kind='done', ok=True))
        self.assertEqual(bridge.poll_events(), [dict(id='orbdiff:0', kind='progress', percent=999), dict(id='orbdiff:0', kind='done', ok=True)])
        self.assertEqual(bridge.poll_events(), [])
        bridge._window.evaluate_js.assert_not_called()

    def test_worker_limit_and_failed_thread_recovery(self):
        bridge = Bridge()
        with patch('ui.web_app.threading.Thread'):
            self.assertTrue(bridge.launch('orbdiff:0')['accepted'])
            self.assertTrue(bridge.launch('orbdiff:1')['accepted'])
            self.assertFalse(bridge.launch('orbdiff:2')['accepted'])
        bridge = Bridge()
        with patch('ui.web_app.threading.Thread') as worker:
            worker.return_value.start.side_effect = RuntimeError('no resources')
            self.assertFalse(bridge.launch('orbdiff:0')['accepted'])
            self.assertFalse(bridge._busy)
            self.assertFalse(bridge._until)

    def test_social_buttons_open_requested_profiles(self):
        page = document()
        self.assertNotIn('id="language"', page)
        self.assertIn('id="github"', page)
        bridge = Bridge()
        with patch('ui.web_app.webbrowser.open_new_tab', return_value=True) as open_tab:
            bridge.open_link('github')
            open_tab.assert_called_with('https://github.com/Psicosiadov2/')
            bridge.open_link('discord')
            open_tab.assert_called_with('https://discord.gg/bhD5sheFf4')

    def test_spokwn_journal_uses_permanent_download(self):
        category = next(c for c in CATEGORIES if c['label'] == 'Spokwn')
        tool = next(t for t in category['tools'] if t['name'] == 'JournalTrace')
        self.assertEqual(tool['url'], 'https://github.com/spokwn/JournalTrace/releases/download/1.2/JournalTrace.exe')
        self.assertTrue(tool['run_as_admin'])

    def test_toolbar_is_above_categories(self):
        html = document()
        self.assertLess(html.index('<header class="titlebar pywebview-drag-region"'), html.index('<nav class="nav"'))
        self.assertEqual(html.count('id="search"'), 0)

    def test_original_intro_is_embedded(self):
        html = document()
        self.assertIn('id="intro-frame"', html)
        self.assertIn('data:video/mp4;base64,', html)
        self.assertNotIn('__INTRO_IMAGE__', html)
        self.assertIn('class="app intro-waiting"', html)

    def test_monochrome_theme(self):
        html = document()
        self.assertNotIn('<footer', html)
        self.assertIn('accent-color:var(--yellow)', html)

    def test_complete_catalogue(self):
        items = catalogue()
        self.assertEqual(sum(len(c['tools']) for c in items), 123)
        self.assertEqual(len(items), 9)
        for old, new in zip(CATEGORIES, items):
            self.assertEqual([t['name'] for t in old['tools']], [t['name'] for t in new['tools']])
            self.assertEqual([t['desc'] for t in old['tools']], [t['descriptions']['en'] for t in new['tools']])

    def test_unknown_command_rejected(self):
        bridge = Bridge()
        self.assertFalse(bridge.launch('cmd.exe')['accepted'])
        self.assertFalse(bridge.launch({'command':'bad'})['accepted'])
        self.assertFalse(bridge.open_link('https://example.com'))

    def test_detect_downloads_are_unique_and_elevated(self):
        category = next(c for c in CATEGORIES if c['id'] == 'detect_ac')
        self.assertEqual(category['label'], 'Detect.ac')
        ids = [c['id'] for c in CATEGORIES]
        self.assertEqual(ids.index('redlotus') + 1, ids.index('nirsoft_utilities'))
        self.assertEqual(ids.index('nirsoft_utilities') + 1, ids.index('ericzimmerman'))
        self.assertEqual(ids.index('ericzimmerman') + 1, ids.index('detect_ac'))
        self.assertEqual(len(category['tools']), 17)
        self.assertEqual(len({t['path'] for t in category['tools']}), 17)
        self.assertEqual(CATEGORIES[-1]['id'], 'dependencies')
        for tool in category['tools']:
            self.assertTrue(tool['run_as_admin'])
            self.assertTrue(tool['url'].startswith('https://github.com/detect-ac/'))
            self.assertIn('/releases/download/', tool['url'])
            self.assertTrue(tool['path'].endswith('.exe'))

    def test_cooldown_enforced_in_host(self):
        bridge = Bridge()
        with patch('ui.web_app.threading.Thread') as thread:
            self.assertTrue(bridge.launch('orbdiff:0')['accepted'])
            self.assertFalse(bridge.launch('orbdiff:0')['accepted'])
            thread.assert_called_once()

    def test_window_actions(self):
        bridge = Bridge()
        bridge._window = Mock()
        bridge.window_control('maximize')
        bridge._window.maximize.assert_called_once()
        bridge.window_control('maximize')
        bridge._window.restore.assert_called_once()
        bridge.window_control('fullscreen')
        bridge._window.toggle_fullscreen.assert_called_once()

    def test_document_keeps_embedded_wallpaper_and_blur(self):
        html = document()
        self.assertIn('class="wallpaper"', html)
        self.assertIn('data:image/', html)
        self.assertIn('<title>SSTool+</title>', html)
        self.assertIn('backdrop-filter:none!important', html)
        self.assertIn('Meow Imports Checker', html)
        self.assertNotIn("'launch-tool'", html)

    def test_worker_passes_catalogue_object_not_user_command(self):
        bridge = Bridge()
        bridge._window = Mock()
        with patch('ui.web_app.launch_tool', return_value=True) as launch:
            bridge._run('orbdiff:0')
        self.assertIs(launch.call_args.args[1], CATEGORIES[0]['tools'][0])
