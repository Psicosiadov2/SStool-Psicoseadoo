import time
import customtkinter as ctk

from core import theme
from core.i18n import category_label, tr
from ui.card import ToolCard
from ui.motion import ease_out_quint, frame_delay


MAX_COLUMNS = 3


class ContentArea(ctk.CTkFrame):
    """Cabecera compacta y cuadricula de herramientas clicables."""

    def __init__(self, master, on_launch):
        super().__init__(master, fg_color=theme.BG_CONTENT, corner_radius=0)
        self.on_launch = on_launch
        self.language = "en"
        self.category = None
        self.columns = MAX_COLUMNS
        self._cards = {}
        self._visible_cards = []
        self._empty_label = None
        self._transition_job = None
        self._scroll_reset_job = None
        self._warmup_job = None

        header = ctk.CTkFrame(
            self,
            height=theme.CONTENT_HEADER_HEIGHT,
            fg_color=theme.BG_CONTENT,
            corner_radius=0,
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        self._busy = False
        self.activity = ctk.CTkProgressBar(
            header, height=2, mode="indeterminate", corner_radius=0,
            fg_color=theme.BG_CONTENT, progress_color=theme.RED_PRIMARY,
            indeterminate_speed=1.2,
        )

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(16, 0), pady=(13, 9))
        self.title_label = ctk.CTkLabel(
            left,
            text="",
            font=theme.FONT_TITLE,
            text_color=theme.RED_BRIGHT,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        decoration = ctk.CTkFrame(header, fg_color="transparent")
        decoration.pack(side="right", padx=(0, 18), pady=14)
        for width, color in (
            (56, theme.RED_DIM),
            (34, theme.RED_PRIMARY),
            (16, theme.GLASS_HIGHLIGHT),
        ):
            ctk.CTkFrame(
                decoration, width=width, height=2,
                fg_color=color, corner_radius=1,
            ).pack(side="left", padx=3)

        ctk.CTkFrame(
            self,
            height=1,
            fg_color=theme.BORDER_SUBTLE,
            corner_radius=0,
        ).pack(fill="x")

        self.viewport = ctk.CTkFrame(self, fg_color=theme.BG_CONTENT, corner_radius=0)
        self.viewport.pack(fill="both", expand=True, padx=(8, 8), pady=(2, 8))
        self.scroll = ctk.CTkScrollableFrame(
            self.viewport,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_fg_color=theme.SCROLLBAR_TRACK,
            scrollbar_button_color=theme.SCROLLBAR,
            scrollbar_button_hover_color=theme.SCROLLBAR_HOVER,
        )
        self.scroll.place(x=0, y=0, relwidth=1, relheight=1)
        self.transition_glow = ctk.CTkFrame(
            self.viewport,
            height=1,
            fg_color=theme.RED_BRIGHT,
            corner_radius=0,
        )
        self._configure_columns()

    def set_busy(self, busy):
        if busy == self._busy:
            return
        self._busy = busy
        if busy:
            self.activity.place(relx=0, rely=1, relwidth=1, anchor="sw")
            self.activity.start()
        else:
            self.activity.stop()
            self.activity.place_forget()

    def set_tool_busy(self, key, busy):
        for (category_id, name), card in self._cards.items():
            if key == f"tool:{category_id}:{name}":
                card.set_launching(busy)
                break

    def show_category(self, category):
        if self.category is not None and self.category["id"] == category["id"]:
            return
        animate = self.category is not None
        self._stop_transition()
        self.category = category
        self.title_label.configure(text=category_label(category, self.language))
        self._render()
        self._reset_scroll_after_layout()
        if animate:
            self._transition_started = time.monotonic()
            self._transition_step()

    def _transition_step(self):
        self._transition_job = None
        progress = min(1.0, (time.monotonic() - self._transition_started) / .18)
        eased = ease_out_quint(progress)
        self.scroll.place(
            x=0,
            y=round(12 * (1 - eased)),
            relwidth=1,
            relheight=1,
        )
        self.transition_glow.place(x=0, y=0, relwidth=eased)
        if progress < 1:
            self._transition_job = self.after(frame_delay(self._transition_started), self._transition_step)
        else:
            self.transition_glow.place_forget()

    def _reset_scroll_after_layout(self):
        if self._scroll_reset_job is not None:
            self.after_cancel(self._scroll_reset_job)
        self._scroll_reset_job = self.after_idle(self._reset_scroll)

    def _reset_scroll(self):
        self._scroll_reset_job = None
        self.scroll._parent_canvas.yview_moveto(0)

    def _get_card(self, category_id, tool):
        key = (category_id, tool["name"])
        if key not in self._cards:
            self._cards[key] = ToolCard(
                self.scroll, tool, language=self.language,
                on_click=lambda selected_tool, cid=category_id: self.on_launch(cid, selected_tool))
        return self._cards[key]

    def prepare_cards(self, categories):
        self._warmup_entries = iter((cat["id"], tool) for cat in categories for tool in cat["tools"])
        self._warmup_job = self.after_idle(self._prepare_next_cards)

    def _prepare_next_cards(self):
        self._warmup_job = None
        prepared = 0
        while prepared < 8:
            entry = next(self._warmup_entries, None)
            if entry is None:
                return
            self._get_card(*entry)
            prepared += 1
        self._warmup_job = self.after_idle(self._prepare_next_cards)

    def _stop_transition(self):
        if self._transition_job is not None:
            self.after_cancel(self._transition_job)
            self._transition_job = None
        self.scroll.place(x=0, y=0, relwidth=1, relheight=1)
        self.transition_glow.place_forget()

    def destroy(self):
        self._stop_transition()
        for job in (self._scroll_reset_job, self._warmup_job):
            if job is not None:
                self.after_cancel(job)
        super().destroy()

    def _configure_columns(self):
        for column in range(MAX_COLUMNS):
            self.scroll.grid_columnconfigure(
                column,
                weight=1 if column < self.columns else 0,
                uniform="tool_cards" if column < self.columns else "",
            )

    def _render(self):
        previous_cards = self._visible_cards
        if self._empty_label is not None:
            self._empty_label.grid_remove()

        if self.category:
            entries = [(self.category["id"], tool) for tool in self.category["tools"]]
            empty_message = tr("empty", self.language)
        else:
            return
        self._visible_cards = [self._get_card(cid, tool) for cid, tool in entries]
        visible = set(self._visible_cards)
        for card in previous_cards:
            if card not in visible:
                card.grid_remove()
                card._grid_slot = None

        if not entries:
            if self._empty_label is None:
                self._empty_label = ctk.CTkLabel(
                    self.scroll, text="", font=theme.FONT_CARD_DESC,
                    text_color=theme.TEXT_MUTED)
            self._empty_label.configure(text=empty_message)
            self._empty_label.grid(
                row=0,
                column=0,
                columnspan=self.columns,
                sticky="w",
                padx=14,
                pady=24,
            )
            return

        for index, (category_id, tool) in enumerate(entries):
            row, column = divmod(index, self.columns)
            card = self._visible_cards[index]
            if getattr(card, "_grid_slot", None) == (row, column):
                continue
            card._grid_slot = (row, column)
            card.grid(
                row=row,
                column=column,
                padx=theme.CARD_PAD_X,
                pady=theme.CARD_PAD_Y,
                sticky="nsew",
            )

    def set_language(self, language):
        self.language = language
        if self.category:
            self.title_label.configure(text=category_label(self.category, language))
        for card in self._cards.values():
            card.set_language(language)
        if self._empty_label is not None:
            self._empty_label.configure(text=tr("empty", language))
