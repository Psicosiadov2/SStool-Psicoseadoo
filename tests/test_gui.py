import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.resize import resized_bounds
from ui.app import App
from ui.content import ContentArea
from core.data import CATEGORIES
from ui.splash import StartupSplash
from core import theme
from ui.motion import frame_delay, TARGET_FPS
import queue
import io
import tempfile
from core.cooldown import Cooldown
from ui.card import ToolCard
from ui.titlebar import TitleBar
from ui.topnav import TopNav
from core.launcher import _download_to_temp, _tool_command
from core.i18n import DEFAULT_LANGUAGE, category_label, tool_description


class GuiTests(unittest.TestCase):
    def test_discord_opens_https_invite(self):
        with patch("ui.titlebar.webbrowser.open_new_tab") as open_url:
            TitleBar.open_discord(Mock())
        open_url.assert_called_once_with("https://discord.gg/Eux3UUKvXg")

    def test_github_button_opens_psicoseado_profile(self):
        with patch("ui.topnav.webbrowser.open_new_tab") as open_url:
            TopNav.open_github()
        open_url.assert_called_once_with("https://github.com/Psicoseado")

    def test_scroll_reset_waits_for_layout_and_cancels_old_request(self):
        content = Mock(_scroll_reset_job="old")
        ContentArea._reset_scroll_after_layout(content)
        content.after_cancel.assert_called_once_with("old")
        content.after_idle.assert_called_once_with(content._reset_scroll)

    def test_cooldown_expires_by_time_not_callback_count(self):
        now = [100.0]
        cooldown = Cooldown(clock=lambda: now[0])
        cooldown.start()
        self.assertEqual(cooldown.remaining, 5.0)
        now[0] = 102.5
        self.assertEqual(cooldown.remaining, 2.5)
        now[0] = 120
        self.assertEqual(cooldown.remaining, 0)

    def test_card_ignores_repeated_clicks_and_busy_launch(self):
        for remaining, busy in ((4.9, False), (0, True)):
            card = Mock(_launching=busy, cooldown=Mock(remaining=remaining))
            ToolCard._trigger(card, None)
            card.on_click.assert_not_called()

    def test_rejected_launch_does_not_start_cooldown(self):
        card = Mock(_launching=False, cooldown=Mock(remaining=0))
        card.on_click.return_value = False
        ToolCard._trigger(card, None)
        card.cooldown.start.assert_not_called()

    def test_successful_dispatch_starts_one_cooldown(self):
        card = Mock(_launching=False, cooldown=Mock(remaining=0), _pulse_job=None)
        card.on_click.return_value = True
        ToolCard._trigger(card, None)
        card.on_click.assert_called_once_with(card.tool)
        card.cooldown.start.assert_called_once()

    def test_animation_clock_skips_missed_frames(self):
        self.assertEqual(TARGET_FPS, 180)
        for elapsed in (0, .005, .016, .09, 5.5):
            self.assertIn(frame_delay(100, 100 + elapsed), range(1, 7))

    def test_transition_finishes_in_place(self):
        content = Mock(_transition_started=100.0, _visible_cards=[])
        with patch("ui.content.time.monotonic", return_value=100.2):
            ContentArea._transition_step(content)
        content.scroll.place.assert_called_once_with(x=0, y=0, relwidth=1, relheight=1)
        content.after.assert_not_called()

    def test_same_category_does_not_render_or_animate_again(self):
        content = Mock(category=CATEGORIES[0])
        ContentArea.show_category(content, CATEGORIES[0])
        content._render.assert_not_called()
        content._transition_step.assert_not_called()

    def test_completed_actions_stop_polling(self):
        messages = queue.Queue()
        messages.put(("done", "launch"))
        app = Mock(_ui_messages=messages, _busy_actions={"launch"}, _closing=False)
        App._drain_ui_messages(app)
        self.assertEqual(app._busy_actions, set())
        app.after.assert_not_called()
        app.content.set_busy.assert_called_once_with(False)

    def test_startup_finishes_at_six_seconds_without_blocking(self):
        self.assertEqual(StartupSplash.DURATION, 6.0)
        splash = Mock(_started=100.0, DURATION=StartupSplash.DURATION, _stars=[],
                      _meteors=[], _size=(100, 100))
        with patch("ui.splash.time.monotonic", return_value=105.9):
            StartupSplash._tick(splash)
        splash.destroy.assert_not_called()
        self.assertLessEqual(splash.after.call_args.args[0], 125)
        splash.after.reset_mock()
        with patch("ui.splash.time.monotonic", return_value=106.0):
            StartupSplash._tick(splash)
        splash.destroy.assert_called_once()
        splash.after.assert_not_called()
        splash.on_complete.assert_called_once()

    def test_download_reports_real_byte_progress_and_finishes_at_100(self):
        payload = b"MZ" + b"x" * 14

        class Response(io.BytesIO):
            headers = {"Content-Length": str(len(payload))}
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                self.close()

        progress = []
        with tempfile.TemporaryDirectory() as directory, patch(
            "core.launcher.urllib.request.urlopen", return_value=Response(payload)
        ):
            path = _download_to_temp(
                "https://example.invalid/tool.exe", directory,
                on_progress=lambda current, total: progress.append((current, total)),
            )
            self.assertTrue(path)
        self.assertEqual(progress[0], (0, len(payload)))
        self.assertEqual(progress[-1], (len(payload), len(payload)))

    def test_progress_message_updates_the_matching_card(self):
        messages = queue.Queue()
        messages.put(("progress", "tool:orbdiff:Example", "Example", 42.5))
        app = Mock(_ui_messages=messages, _busy_actions={"launch"}, _closing=False)
        App._drain_ui_messages(app)
        app.toast.show_progress.assert_called_once_with("Example", 42.5)

    def test_header_appears_directly_after_intro(self):
        app = Mock(_closing=False)
        App._on_splash_complete(app)
        app.titlebar.grid.assert_called_once_with(row=0, column=0, sticky="ew")
        app.titlebar.tkraise.assert_called_once()
        self.assertFalse(hasattr(TitleBar, "start_reveal"))

    def test_cards_are_reused_across_renders(self):
        category = CATEGORIES[0]
        content = Mock(category=category, columns=3,
                       _cards={}, _visible_cards=[], _empty_label=None)
        content._get_card = lambda cid, tool: ContentArea._get_card(content, cid, tool)
        with patch("ui.content.ToolCard") as factory:
            ContentArea._render(content)
            created = factory.call_count
            ContentArea._render(content)
            self.assertEqual(factory.call_count, created)
            self.assertEqual(created, len(category["tools"]))

    def test_switching_categories_preserves_card_and_cooldown(self):
        first, second = CATEGORIES[:2]
        content = Mock(category=first, columns=3,
                       _cards={}, _visible_cards=[], _empty_label=None)
        content._get_card = lambda cid, tool: ContentArea._get_card(content, cid, tool)
        with patch("ui.content.ToolCard", side_effect=lambda *a, **kw: Mock(_grid_slot=None)):
            ContentArea._render(content)
            original = content._visible_cards[0]
            original.cooldown_marker = 123
            content.category = second
            ContentArea._render(content)
            original.grid_remove.assert_called_once()
            content.category = first
            ContentArea._render(content)
            self.assertIs(content._visible_cards[0], original)
            self.assertEqual(original.cooldown_marker, 123)
            self.assertEqual(original.grid.call_count, 2)

    def test_text_contrast_on_black(self):
        rgb = [int(theme.TEXT_PRIMARY[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        luminance = sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
        self.assertGreaterEqual((luminance + .05) / .05, 4.5)

    def test_all_edges(self):
        for edge in ("n", "s", "e", "w", "ne", "nw", "se", "sw"):
            with self.subTest(edge=edge):
                x, y, w, h = resized_bounds((100, 100, 1440, 820), edge,
                                            100, 50, (1040, 640))
                self.assertGreaterEqual(w, 1040)
                self.assertGreaterEqual(h, 640)
                if "w" in edge:
                    self.assertEqual(x + w, 1540)
                if "n" in edge:
                    self.assertEqual(y + h, 920)

    def test_minimum_and_negative_monitor_coordinates(self):
        self.assertEqual(resized_bounds((-1440, 100, 1440, 820), "nw",
                                        9999, 9999, (1040, 640)),
                         (-1040, 280, 1040, 640))

    def test_activity_is_not_restarted_by_concurrent_launches(self):
        content = Mock(_busy=False)
        ContentArea.set_busy(content, True)
        ContentArea.set_busy(content, True)
        content.activity.start.assert_called_once()
        ContentArea.set_busy(content, False)
        content.activity.stop.assert_called_once()
        content.activity.place_forget.assert_called_once()

    def test_fade_finishes_opaque_without_rescheduling(self):
        app = Mock(_closing=False, _fade_started=time.monotonic() - 1)
        App._fade_in(app)
        app.attributes.assert_called_once_with("-alpha", 1.0)
        app.after.assert_not_called()

    def test_child_map_events_do_not_reconfigure_native_window(self):
        app = Mock(_closing=False)
        App._on_native_restore(app, SimpleNamespace(widget=object()))
        app.after.assert_not_called()

    def test_minimize_still_uses_native_path(self):
        app = Mock()
        with patch("ui.app.minimize_taskbar_window", return_value=True):
            App.minimize_to_taskbar(app)
        app.iconify.assert_not_called()
        app.overrideredirect.assert_not_called()

    def test_inventory(self):
        self.assertEqual(sum(len(c["tools"]) for c in CATEGORIES), 42)

    def test_requested_category_and_tool_order(self):
        self.assertEqual(CATEGORIES[0]["label"], "Orbdiff/Others")
        main_names = [tool["name"] for tool in CATEGORIES[0]["tools"]]
        self.assertEqual(main_names[4], "ConsoleHostHistory")
        self.assertEqual(main_names[5], "Eventvwr")
        self.assertEqual(main_names[main_names.index("P1AE Scanner") + 1], "Siege")
        script_names = [tool["name"] for tool in CATEGORIES[3]["tools"]]
        self.assertEqual(script_names[1], "Lilith Script")
        self.assertEqual(script_names[4], "Lilith DoomsDay Finder")
        self.assertIn("Habibi Mod Analyzer", script_names)
        self.assertIn("Real Doomsday Detector", script_names)
        self.assertNotIn("Zeedoonvm1 Doomsday Detector", script_names)

    def test_updated_dependencies_are_desktop_runtimes(self):
        dependencies = {tool["name"]: tool for tool in CATEGORIES[-1]["tools"]}
        self.assertIn("WindowsDesktop/10.0.5", dependencies[".NET 10.0"]["url"])
        self.assertIn("WindowsDesktop/9.0.14", dependencies[".NET 9.0"]["url"])

    def test_event_viewer_uses_native_windows_launcher(self):
        event_viewer = next(t for t in CATEGORIES[0]["tools"] if t["name"] == "Eventvwr")
        self.assertEqual(_tool_command(None, event_viewer), ["eventvwr.exe"])

    def test_new_tools_use_stable_sources_and_admin(self):
        tools = {tool["name"]: tool for tool in CATEGORIES[0]["tools"]}
        self.assertEqual(tools["VMAware"]["url"], "https://github.com/NotRequiem/VMAware/releases/download/v2.8.2/vmaware32.exe")
        self.assertEqual(tools["Siege"]["url"], "https://github.com/praiselily/Siege/releases/download/Scanner/Siege.exe")
        self.assertTrue(tools["VMAware"]["run_as_admin"])
        self.assertTrue(tools["Siege"]["run_as_admin"])

    def test_language_defaults_to_english_and_translates(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertEqual(category_label(CATEGORIES[0], "es"), "Orbdiff/Otros")
        siege = next(t for t in CATEGORIES[0]["tools"] if t["name"] == "Siege")
        self.assertIn("Minecraft", tool_description(siege, "en"))
        self.assertIn("Minecraft", tool_description(siege, "es"))


if __name__ == "__main__":
    unittest.main()
