import os
import queue
import sys
import threading
import time
import tkinter as tk

import customtkinter as ctk

from core import theme
from core.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    APP_ICON_ICO,
    APP_ICON_PNG,
)
from core.data import CATEGORIES, get_category
from core.i18n import DEFAULT_LANGUAGE, tr
from core.launcher import launch_tool
from core.windows_shell import (
    asset_path,
    force_taskbar_window,
    minimize_taskbar_window,
)
from ui.titlebar import TitleBar
from ui.topnav import TopNav
from ui.content import ContentArea
from ui.toast import ToastBanner
from ui.resize import ResizeHandles
from ui.splash import StartupSplash
from ui.motion import frame_delay


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        theme.configure_fonts(self)

        self.title("PsicoseadoSSTool")
        self.overrideredirect(True)
        scaling = self._get_window_scaling()
        available_width = max(640, int(self.winfo_screenwidth() / scaling) - 32)
        available_height = max(360, int(self.winfo_screenheight() / scaling) - 80)
        width = min(WINDOW_WIDTH, available_width)
        height = min(WINDOW_HEIGHT, available_height)
        self.geometry(f"{width}x{height}+16+24")
        self.minsize(min(WINDOW_MIN_WIDTH, width), min(WINDOW_MIN_HEIGHT, height))
        self.configure(fg_color=theme.BG_APP)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0, minsize=theme.TITLEBAR_HEIGHT)
        self.grid_rowconfigure(1, weight=0, minsize=theme.TOPNAV_HEIGHT)
        self.grid_rowconfigure(2, weight=1)

        self._icon_image = None
        self._configure_window_icon()
        self._ui_messages = queue.Queue()
        self._busy_actions = set()
        self._closing = False
        self._fallback_minimize = False
        self._fade_job = None
        self._poll_job = None
        self._worker_slots = threading.Semaphore(2)
        self.language = DEFAULT_LANGUAGE

        self.titlebar = TitleBar(self, self, on_language=self._set_language)

        self.topnav = TopNav(
            self,
            CATEGORIES,
            on_select_category=self._on_select_category,
        )
        self.topnav.grid(row=1, column=0, sticky="ew")

        self.content = ContentArea(self, on_launch=self._on_launch)
        self.content.grid(row=2, column=0, sticky="nsew")

        self.toast = ToastBanner(self)
        self.resize_handles = ResizeHandles(self)

        self.content.show_category(CATEGORIES[0])
        self.splash = StartupSplash(self, on_complete=self._on_splash_complete)
        self.splash.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.splash.tkraise()
        self.content.prepare_cards(CATEGORIES)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Map>", self._on_native_restore, add="+")
        self.after(20, self._show_window)

    def _on_splash_complete(self):
        if self._closing:
            return
        self.titlebar.grid(row=0, column=0, sticky="ew")
        self.titlebar.tkraise()

    def _configure_window_icon(self):
        png_path = asset_path(APP_ICON_PNG)
        ico_path = asset_path(APP_ICON_ICO)
        try:
            if os.path.isfile(png_path):
                self._icon_image = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self._icon_image)
            if sys.platform.startswith("win") and os.path.isfile(ico_path):
                self.iconbitmap(ico_path)
        except tk.TclError:
            # El ejecutable sigue abriendo aunque Windows no acepte un formato.
            pass

    def _show_window(self):
        self.update_idletasks()
        force_taskbar_window(self)
        try:
            self.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self.deiconify()
        self.splash.start()
        self._fade_started = time.monotonic()
        self._fade_in()
        self.after(30, self.ensure_taskbar_presence)

    def _fade_in(self):
        self._fade_job = None
        if self._closing:
            return
        progress = min(1.0, (time.monotonic() - self._fade_started) / 0.20)
        try:
            self.attributes("-alpha", 1 - (1 - progress) ** 3)
        except tk.TclError:
            return
        if progress < 1:
            self._fade_job = self.after(frame_delay(self._fade_started), self._fade_in)

    def ensure_taskbar_presence(self):
        force_taskbar_window(self)

    def _queue_status(self, message):
        self._ui_messages.put(("status", message))

    def _queue_progress(self, key, name, downloaded, total):
        percent = 0 if not total else downloaded * 100 / total
        self._ui_messages.put(("progress", key, name, min(100, percent)))

    def _drain_ui_messages(self):
        self._poll_job = None
        try:
            for _ in range(50):
                message = self._ui_messages.get_nowait()
                kind, value = message[0], message[1]
                if kind == "status":
                    self._show_status(value)
                elif kind == "progress":
                    self.toast.show_progress(message[2], message[3])
                elif kind == "done":
                    self._busy_actions.discard(value)
                    self.content.set_tool_busy(value, False)
                    self.content.set_busy(bool(self._busy_actions))
        except queue.Empty:
            pass
        try:
            if not self._closing and (self._busy_actions or not self._ui_messages.empty()):
                self._poll_job = self.after(50, self._drain_ui_messages)
        except tk.TclError:
            pass

    def _start_background_action(self, key, initial_message, operation):
        if key in self._busy_actions:
            self._show_status(tr("already_running", self.language))
            return False

        self._busy_actions.add(key)
        if self._poll_job is None:
            self._poll_job = self.after(50, self._drain_ui_messages)
        self.content.set_busy(True)
        self.content.set_tool_busy(key, True)
        self._show_status(initial_message)

        def worker():
            try:
                with self._worker_slots:
                    if not self._closing:
                        operation()
            except Exception as exc:  # Protege la GUI ante fallos imprevistos.
                self._queue_status(tr("unexpected", self.language, error=exc))
            finally:
                self._ui_messages.put(("done", key))

        threading.Thread(target=worker, daemon=True, name=key).start()
        return True

    # ---- Callbacks ----
    def _on_select_category(self, category_id):
        cat = get_category(category_id)
        if cat:
            self.content.show_category(cat)

    def _on_launch(self, category_id, tool):
        key = f"tool:{category_id}:{tool['name']}"
        return self._start_background_action(
            key,
            tr("preparing", self.language, name=tool["name"]),
            lambda: launch_tool(
                category_id,
                tool,
                on_missing=self._queue_status,
                on_error=self._queue_status,
                on_status=self._queue_status,
                on_progress=lambda downloaded, total: self._queue_progress(
                    key, tool["name"], downloaded, total
                ),
            ),
        )

    def _set_language(self, language):
        if language not in ("en", "es"):
            return
        self.language = language
        self.titlebar.set_language(language)
        self.topnav.set_language(language)
        self.content.set_language(language)
        self.toast.set_language(language)

    def _show_status(self, message):
        self.toast.show(message)

    # ---- Minimizado estandar en la barra de tareas ----
    def minimize_to_taskbar(self):
        """Minimiza como una app normal y conserva su icono en la taskbar."""
        if minimize_taskbar_window(self):
            return

        # Fallback para entornos que no sean Windows.
        self._fallback_minimize = True
        self.overrideredirect(False)
        self.iconify()

    def _on_native_restore(self, event):
        # Child widgets also send Map events through the toplevel bindtag.
        if self._closing or event.widget is not self:
            return
        if self._fallback_minimize:
            self._fallback_minimize = False
            self.overrideredirect(True)
        self.after(20, self.ensure_taskbar_presence)

    def close_app(self):
        if self._closing:
            return
        self._closing = True
        if self._fade_job is not None:
            self.after_cancel(self._fade_job)
        self.content.set_busy(False)
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
        self.destroy()
