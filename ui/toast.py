import customtkinter as ctk
import time

from core import theme
from core.i18n import tr
from ui.motion import frame_delay


class ToastBanner(ctk.CTkFrame):
    """Notificacion discreta alineada a la esquina inferior derecha."""

    def __init__(self, master, language="en"):
        super().__init__(
            master,
            width=1,
            height=1,
            fg_color=theme.BG_ELEVATED,
            border_width=1,
            border_color=theme.RED_DARK,
            corner_radius=6,
        )
        self.language = language
        ctk.CTkFrame(
            self,
            width=2,
            height=1,
            fg_color=theme.RED_PRIMARY,
            corner_radius=0,
        ).pack(side="left", fill="y", padx=(6, 0), pady=8)

        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(side="left", padx=(9, 12), pady=9)
        self.label = ctk.CTkLabel(
            body,
            text="",
            width=390,
            height=1,
            font=theme.FONT_CARD_DESC,
            text_color=theme.TEXT_PRIMARY,
            justify="left",
            anchor="w",
            wraplength=390,
        )
        self.label.pack(fill="x")

        self.progress_row = ctk.CTkFrame(
            body, fg_color="transparent", corner_radius=0)
        self.download_bar = ctk.CTkProgressBar(
            self.progress_row, width=330, height=5, orientation="horizontal",
            mode="determinate", corner_radius=2,
            fg_color=theme.BORDER_SUBTLE,
            progress_color=theme.RED_BRIGHT)
        self.download_bar.set(0)
        self.download_bar.pack(side="left", pady=(7, 0))
        self.percent_label = ctk.CTkLabel(
            self.progress_row, text="0%", width=46, height=18,
            font=theme.FONT_EYEBROW, text_color=theme.TEXT_PRIMARY,
            anchor="e")
        self.percent_label.pack(side="left", padx=(10, 0), pady=(4, 0))
        self._hide_job = None
        self._slide_job = None
        self._visible = False

    def show(self, message, ms=3200):
        self.label.configure(text=message)
        self.progress_row.pack_forget()
        self._present()
        if self._hide_job:
            self.after_cancel(self._hide_job)
        self._hide_job = self.after(ms, self.hide)

    def show_progress(self, name, percent):
        value = max(0.0, min(100.0, float(percent)))
        self.label.configure(text=tr("downloading", self.language, name=name))
        self.download_bar.set(value / 100)
        self.percent_label.configure(text=f"{round(value):d}%")
        if not self.progress_row.winfo_manager():
            self.progress_row.pack(fill="x")
        if self._hide_job:
            self.after_cancel(self._hide_job)
            self._hide_job = None
        self._present()

    def set_language(self, language):
        self.language = language

    def _present(self):
        if not self._visible:
            if self._slide_job:
                self.after_cancel(self._slide_job)
            self._slide_started = time.monotonic()
            self._slide_in()
            self._visible = True
        self.lift()

    def hide(self):
        if self._slide_job:
            self.after_cancel(self._slide_job)
            self._slide_job = None
        self.place_forget()
        self._hide_job = None
        self._visible = False

    def _slide_in(self):
        self._slide_job = None
        progress = min(1.0, (time.monotonic() - self._slide_started) / 0.16)
        offset = round(30 * (1 - progress) ** 3)
        self.place(relx=0.985, rely=0.975, x=offset, anchor="se")
        if progress < 1:
            self._slide_job = self.after(frame_delay(self._slide_started), self._slide_in)

    def destroy(self):
        for job in (self._hide_job, self._slide_job):
            if job:
                self.after_cancel(job)
        super().destroy()
