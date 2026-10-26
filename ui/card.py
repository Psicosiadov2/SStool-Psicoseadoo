import time
import customtkinter as ctk

from core import theme
from core.cooldown import Cooldown
from core.i18n import tool_description, tr
from ui.motion import ease_out_quint, frame_delay, mix_color


class ToolCard(ctk.CTkFrame):
    """Tarjeta plana y minimalista; toda la superficie es clicable."""

    def __init__(self, master, tool, on_click, language="en"):
        super().__init__(
            master,
            height=theme.CARD_HEIGHT,
            fg_color=theme.CARD_BG,
            corner_radius=theme.CORNER_RADIUS,
            border_width=1,
            border_color=theme.CARD_BORDER,
            cursor="hand2",
        )
        self.grid_propagate(False)
        self._wrap_width = None
        self._pulse_job = None
        self._fit_job = None
        self._hover_job = None
        self._hover_level = 0.0
        self._hovered = False
        self.cooldown = Cooldown()
        self._cooldown_job = None
        self._launching = False
        self.tool = tool
        self.language = language
        self.on_click = on_click

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Reflejo superior fino: simula el borde de una lamina de vidrio.
        self.reflection = ctk.CTkFrame(
            self,
            height=1,
            fg_color=theme.GLASS_REFLECTION,
            corner_radius=1,
            cursor="hand2",
        )
        self.reflection.place(relx=.06, rely=0, relwidth=.88)

        self.title = ctk.CTkLabel(
            self,
            text=tool["name"],
            font=theme.FONT_CARD_TITLE,
            text_color=theme.TEXT_HEADING,
            anchor="w",
            justify="left",
            cursor="hand2",
        )
        self.title.grid(row=0, column=0, sticky="ew", padx=13, pady=(11, 0))

        self.desc = ctk.CTkLabel(
            self,
            text=tool_description(tool, language),
            font=theme.FONT_CARD_DESC,
            text_color=theme.TEXT_SECONDARY,
            anchor="nw",
            justify="left",
            wraplength=280,
            cursor="hand2",
        )
        self.desc.grid(row=1, column=0, sticky="nsew", padx=13, pady=(5, 8))
        self.status = ctk.CTkLabel(self, text="", height=18, anchor="w",
                                  font=theme.FONT_SMALL, text_color=theme.TEXT_PRIMARY)
        self.status.grid(row=2, column=0, sticky="ew", padx=13, pady=(0, 7))
        self.status.grid_remove()
        self.cooldown_progress = ctk.CTkProgressBar(
            self, height=2, corner_radius=0, fg_color=theme.CARD_BG,
            progress_color=theme.RED_PRIMARY)
        self.cooldown_progress.set(0)
        self.cooldown_progress.grid(row=3, column=0, sticky="ew", padx=1, pady=(0, 1))

        self.accent = ctk.CTkFrame(
            self,
            width=3,
            fg_color="transparent",
            corner_radius=0,
            cursor="hand2",
        )
        self.accent.place(x=0, y=0, relheight=1)

        self.bind("<Configure>", self._on_resize)
        for widget in (self, self.title, self.desc, self.accent, self.reflection, self.status,
                       self.cooldown_progress):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._trigger)

    def _on_resize(self, event):
        width = max(150, event.width - 30)
        if width == self._wrap_width:
            return
        self._wrap_width = width
        self.desc.configure(wraplength=width)
        self.title.configure(wraplength=width)
        if self._fit_job is not None:
            self.after_cancel(self._fit_job)
        self._fit_job = self.after_idle(self._fit_height)

    def _fit_height(self):
        self._fit_job = None
        # Native requested label height accounts for wrapped text and DPI.
        scale = self._get_widget_scaling()
        needed = (self.title.winfo_reqheight() + self.desc.winfo_reqheight()) / scale + 45
        self.configure(height=max(theme.CARD_HEIGHT, needed))

    def _trigger(self, _event):
        if self._launching or self.cooldown.remaining > 0:
            return
        accepted = self.on_click(self.tool)
        if accepted is False:
            return
        self.cooldown.start()
        self._update_cooldown()
        if self._pulse_job is not None:
            self.after_cancel(self._pulse_job)
        self._pulse_started = time.monotonic()
        self._animate_launch()

    def _animate_launch(self):
        self._pulse_job = None
        t = min(1.0, (time.monotonic() - self._pulse_started) / .24)
        amount = (1 - t) ** 2
        colors = (theme.RED_BRIGHT, theme.CARD_BORDER)
        rgb = [round(int(colors[1][i:i+2], 16) * (1-amount) +
                     int(colors[0][i:i+2], 16) * amount) for i in (1, 3, 5)]
        self.configure(border_color="#%02x%02x%02x" % tuple(rgb))
        if t < 1:
            self._pulse_job = self.after(frame_delay(self._pulse_started), self._animate_launch)
        else:
            self.configure(border_color=(
                theme.CARD_BORDER_HOVER if self._hovered else theme.CARD_BORDER
            ))

    def set_launching(self, busy):
        self._launching = busy
        self._update_cooldown()

    def _update_cooldown(self):
        if self._cooldown_job is not None:
            self.after_cancel(self._cooldown_job)
            self._cooldown_job = None
        remaining = self.cooldown.remaining
        if remaining > 0:
            self.status.grid()
            self.status.configure(text=tr("available", self.language, seconds=remaining))
            self.cooldown_progress.set(1 - remaining / self.cooldown.duration)
            self._cooldown_job = self.after(100, self._update_cooldown)
        elif self._launching:
            self.status.grid()
            self.status.configure(text=tr("opening", self.language))
            self.cooldown_progress.set(1)
        else:
            self.status.configure(text="")
            self.status.grid_remove()
            self.cooldown_progress.set(0)
        self.title.configure(text_color=theme.TEXT_SECONDARY)
        if not self._hovered:
            self.configure(fg_color=(
                theme.RED_GHOST if remaining > 0 or self._launching else theme.CARD_BG
            ))

    def set_language(self, language):
        self.language = language
        self.desc.configure(text=tool_description(self.tool, language))
        self._update_cooldown()

    def destroy(self):
        if self._pulse_job is not None:
            self.after_cancel(self._pulse_job)
        if self._fit_job is not None:
            self.after_cancel(self._fit_job)
        if self._cooldown_job is not None:
            self.after_cancel(self._cooldown_job)
        if self._hover_job is not None:
            self.after_cancel(self._hover_job)
        super().destroy()

    def _on_enter(self, _event):
        if self._hovered:
            return
        self._hovered = True
        self._start_hover_animation(1.0)

    def _on_leave(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget is self:
                return
            widget = getattr(widget, "master", None)
        if not self._hovered:
            return
        self._hovered = False
        self._start_hover_animation(0.0)

    def _start_hover_animation(self, target):
        if self._hover_job is not None:
            self.after_cancel(self._hover_job)
        self._hover_from = self._hover_level
        self._hover_target = target
        self._hover_started = time.monotonic()
        self._animate_hover()

    def _animate_hover(self):
        self._hover_job = None
        progress = min(1.0, (time.monotonic() - self._hover_started) / .12)
        eased = ease_out_quint(progress)
        self._hover_level = self._hover_from + (
            self._hover_target - self._hover_from
        ) * eased
        resting = theme.RED_GHOST if self._launching or self.cooldown.remaining > 0 else theme.CARD_BG
        self.configure(
            fg_color=mix_color(resting, theme.CARD_BG_HOVER, self._hover_level),
            border_color=mix_color(theme.CARD_BORDER, theme.CARD_BORDER_HOVER, self._hover_level),
        )
        self.accent.configure(
            fg_color=mix_color(theme.CARD_BG, theme.RED_PRIMARY, self._hover_level)
        )
        self.reflection.configure(
            fg_color=mix_color(
                theme.GLASS_REFLECTION, theme.GLASS_HIGHLIGHT,
                self._hover_level,
            )
        )
        self.title.configure(
            text_color=mix_color(theme.TEXT_HEADING, theme.RED_BRIGHT, self._hover_level)
        )
        if progress < 1:
            self._hover_job = self.after(
                frame_delay(self._hover_started), self._animate_hover
            )
