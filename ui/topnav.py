import tkinter as tk
import webbrowser

import customtkinter as ctk

from core import theme
from core.i18n import category_label


GITHUB_URL = "https://github.com/Psicoseado"


class TopNav(ctk.CTkFrame):
    """Navegacion dividida, compacta y basada en la referencia visual."""

    def __init__(self, master, categories, on_select_category):
        super().__init__(master, height=theme.TOPNAV_HEIGHT,
                         fg_color=theme.BG_TOPNAV, corner_radius=0)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.on_select_category = on_select_category
        self.active_id = categories[0]["id"]
        self.categories = {category["id"]: category for category in categories}
        self.language = "en"
        self._tabs = {}

        github = ctk.CTkButton(
            self, text="", width=46, height=theme.TOPNAV_HEIGHT,
            corner_radius=0, fg_color="transparent",
            hover_color=theme.RED_GHOST, command=self.open_github)
        github.grid(row=0, column=0, sticky="nsew")
        lens = tk.Canvas(github, width=22, height=22, bg=theme.BG_TOPNAV,
                         highlightthickness=0, borderwidth=0, cursor="hand2")
        lens.create_oval(3, 3, 13, 13, outline=theme.TEXT_PRIMARY, width=2)
        lens.create_line(12, 12, 19, 19, fill=theme.TEXT_PRIMARY, width=2)
        lens.place(relx=.5, rely=.5, anchor="center")
        lens.bind("<Button-1>", lambda _event: self.open_github())
        self._separator(1)

        for index, category in enumerate(categories):
            button_column = 2 + index * 2
            self.grid_columnconfigure(button_column, weight=1)
            label = self._label(category)
            button = ctk.CTkButton(
                self, text=label, width=1, height=theme.TOPNAV_HEIGHT,
                corner_radius=0, fg_color="transparent",
                hover_color=theme.RED_GHOST, text_color=theme.TEXT_SECONDARY,
                font=theme.FONT_TAB,
                command=lambda cid=category["id"]: self.select(cid))
            button.grid(row=0, column=button_column, sticky="nsew")
            self._tabs[category["id"]] = button
            if index < len(categories) - 1:
                self._separator(button_column + 1)

        ctk.CTkFrame(self, height=1, fg_color=theme.BORDER_SUBTLE,
                     corner_radius=0).place(relx=0, rely=1, relwidth=1, anchor="sw")
        self._style_tab(self.active_id, True)

    def _label(self, category):
        return f"{category.get('icon', '')}  {category_label(category, self.language)}".strip()

    def set_language(self, language):
        self.language = language
        for category_id, button in self._tabs.items():
            button.configure(text=self._label(self.categories[category_id]))

    def _separator(self, column):
        separator = ctk.CTkFrame(self, width=1, fg_color=theme.BORDER_SUBTLE,
                                 corner_radius=0)
        separator.grid(row=0, column=column, sticky="ns", pady=8)

    @staticmethod
    def open_github():
        webbrowser.open_new_tab(GITHUB_URL)

    def select(self, category_id):
        if category_id == self.active_id:
            return
        self._style_tab(self.active_id, False)
        self.active_id = category_id
        self._style_tab(category_id, True)
        self.on_select_category(category_id)

    def _style_tab(self, category_id, active):
        self._tabs[category_id].configure(
            fg_color=theme.RED_GHOST if active else "transparent",
            text_color=theme.RED_BRIGHT if active else theme.TEXT_SECONDARY,
            font=theme.FONT_TAB_ACTIVE if active else theme.FONT_TAB,
            border_width=2 if active else 0,
            border_color=theme.RED_BRIGHT,
        )
