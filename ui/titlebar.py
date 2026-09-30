import webbrowser

import customtkinter as ctk

from core import theme
from core.config import APP_NAME, DISCORD_INVITE


class TitleBar(ctk.CTkFrame):
    """Barra de ventana fina inspirada en la referencia."""

    def __init__(self, master, app, on_language=None):
        super().__init__(
            master,
            height=theme.TITLEBAR_HEIGHT,
            fg_color=theme.BG_TITLEBAR,
            corner_radius=0,
        )
        self.app = app
        self.on_language = on_language
        self._maximized = False
        self._prev_geometry = None
        self._drag_start = (0, 0)

        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=(8, 0))
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left")
        brand_name = ctk.CTkLabel(
            brand_text,
            text=APP_NAME,
            height=22,
            font=theme.FONT_BRAND,
            text_color=theme.RED_BRIGHT,
            anchor="w",
        )
        brand_name.pack(fill="x")
        self.brand_caption = ctk.CTkLabel(
            brand_text,
            text="Contact: Psicoseado",
            height=18,
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_MUTED,
            anchor="w",
        )
        self.brand_caption.pack(fill="x")

        drag_zone = ctk.CTkFrame(self, fg_color="transparent")
        drag_zone.grid(row=0, column=1, sticky="nsew")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e")
        self.language_selector = ctk.CTkSegmentedButton(
            right,
            values=["EN", "ES"],
            width=76,
            height=24,
            corner_radius=5,
            border_width=1,
            fg_color=theme.BG_TITLEBAR,
            selected_color=theme.RED_GHOST,
            selected_hover_color=theme.RED_GHOST,
            unselected_color=theme.BG_TITLEBAR,
            unselected_hover_color=theme.BG_ELEVATED,
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_SMALL,
            command=self._select_language,
        )
        self.language_selector.set("EN")
        self.language_selector.pack(side="left", padx=(0, 12))
        if DISCORD_INVITE:
            invite = ctk.CTkLabel(
                right,
                text=DISCORD_INVITE,
                font=theme.FONT_SMALL,
                text_color=theme.TEXT_MUTED,
                cursor="hand2",
            )
            invite.pack(side="left", padx=(0, 12))
            invite.bind("<Button-1>", self.open_discord)


        self._window_button(right, "−", self.minimize)
        self._window_button(right, "□", self.toggle_maximize)
        self._window_button(right, "×", self.close, close=True)

        ctk.CTkFrame(
            self,
            height=1,
            fg_color=theme.BORDER_SUBTLE,
            corner_radius=0,
        ).place(relx=0, rely=1, relwidth=1, anchor="sw")

        for widget in (self, brand, brand_name, self.brand_caption, brand_text, drag_zone):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._do_move)
            widget.bind("<Double-Button-1>", lambda _event: self.toggle_maximize())

    def _select_language(self, value):
        if self.on_language:
            self.on_language(value.lower())

    def set_language(self, language):
        self.language_selector.set(language.upper())
        self.brand_caption.configure(
            text="Contacto: Psicoseado" if language == "es" else "Contact: Psicoseado"
        )


    def open_discord(self, _event=None):
        url = DISCORD_INVITE if DISCORD_INVITE.startswith("https://") else "https://" + DISCORD_INVITE
        webbrowser.open_new_tab(url)

    def _window_button(self, parent, symbol, command, close=False):
        button = ctk.CTkButton(
            parent,
            text=symbol,
            width=38,
            height=theme.TITLEBAR_HEIGHT,
            corner_radius=0,
            fg_color="transparent",
            hover_color=theme.RED_DARK if close else theme.RED_GHOST,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_WINDOW_CONTROL,
            command=command,
        )
        button.pack(side="left")
        return button

    def _start_move(self, event):
        self._drag_start = (event.x_root, event.y_root)

    def _do_move(self, event):
        if self._maximized:
            return
        delta_x = event.x_root - self._drag_start[0]
        delta_y = event.y_root - self._drag_start[1]
        self.app.geometry(
            f"+{self.app.winfo_x() + delta_x}+{self.app.winfo_y() + delta_y}"
        )
        self._drag_start = (event.x_root, event.y_root)

    def minimize(self):
        self.app.minimize_to_taskbar()

    def toggle_maximize(self):
        if self._maximized:
            if self._prev_geometry:
                self.app.geometry(self._prev_geometry)
            self._maximized = False
            return

        self._prev_geometry = self.app.geometry()
        width = self.app.winfo_screenwidth()
        height = self.app.winfo_screenheight()
        self.app.geometry(f"{width}x{height}+0+0")
        self._maximized = True

    def close(self):
        self.app.close_app()
