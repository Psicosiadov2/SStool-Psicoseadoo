"""Six-second, timer-driven intro. No downloads or blocking waits."""
import math
import random
import time
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from core import theme
from core.windows_shell import asset_path
from ui.motion import frame_delay


class StartupSplash(ctk.CTkFrame):
    DURATION = 6.0

    def __init__(self, master, on_complete=None):
        super().__init__(master, fg_color=theme.BG_APP, corner_radius=0)
        self.on_complete = on_complete
        self._job = None
        self._started = None
        self.canvas = tk.Canvas(self, bg=theme.BG_APP, highlightthickness=0, borderwidth=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        rng = random.Random(71)
        self._stars = []
        self._star_colors = {}
        self._size = (1, 1)
        for index in range(48):
            x, y = rng.random(), rng.random()
            radius = 2.5 if index % 6 == 0 else 1.2
            item = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0,
                                               fill="#505050", outline="")
            self._stars.append((item, x, y, radius, rng.random() * math.tau))
        self._meteors = [self.canvas.create_line(0, 0, 0, 0, fill="#606060", width=1),
                         self.canvas.create_line(0, 0, 0, 0, fill="#999999", width=1)]
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=.5, rely=.5, anchor="center")
        with Image.open(asset_path("Intro.png")) as original:
            artwork = original.convert("RGB")
        self._ratio = artwork.width / artwork.height
        self._art = ctk.CTkImage(light_image=artwork, dark_image=artwork,
                                size=(round(300 * self._ratio), 300))
        ctk.CTkLabel(center, text="", image=self._art, width=1, height=1).pack()
        ctk.CTkLabel(center, text="PSICOSEADOSSTOOL", text_color=theme.TEXT_HEADING,
                     font=(theme.FONT_DISPLAY, 20, "bold")).pack(pady=(12, 10))
        ctk.CTkLabel(center, text="Loading SStool Kits....",
                     text_color=theme.TEXT_PRIMARY, font=theme.FONT_CARD_DESC).pack()
        self.progress = ctk.CTkProgressBar(center, width=270, height=2,
                                          fg_color=theme.BORDER_SUBTLE, progress_color=theme.RED_BRIGHT,
                                          corner_radius=0, mode="determinate")
        self.progress.set(0)
        self.progress.pack(pady=(22, 8))
        self.canvas.bind("<Configure>", self._layout)

    def _layout(self, event):
        self._size = (event.width, event.height)
        for item, x, y, radius, _ in self._stars:
            x, y = x * event.width, y * event.height
            r = radius * self._get_widget_scaling()
            self.canvas.coords(item, x, y-r*2, x+r*.35, y-r*.35,
                               x+r*2, y, x+r*.35, y+r*.35,
                               x, y+r*2, x-r*.35, y+r*.35,
                               x-r*2, y, x-r*.35, y-r*.35)
        scale = self._get_widget_scaling()
        height = max(80, min(390, event.height / scale - 145,
                            event.width / scale * .55 / self._ratio))
        self._art.configure(size=(round(height * self._ratio), round(height)))

    def start(self):
        if self._started is not None:
            return
        self._started = time.monotonic()
        self._tick()

    def _tick(self):
        self._job = None
        elapsed = time.monotonic() - self._started
        if elapsed >= self.DURATION:
            self.destroy()
            if self.on_complete:
                self.on_complete()
            return
        phase = elapsed / self.DURATION
        # This is the intro timeline, not a fabricated download percentage.
        self.progress.set(phase * phase * (3 - 2 * phase))
        for item, _, _, _, offset in self._stars:
            brightness = int(105 + 65 * math.sin(elapsed * 1.8 + offset))
            color = "#" + f"{brightness:02x}" * 3
            if self._star_colors.get(item) != color:
                self.canvas.itemconfigure(item, fill=color)
                self._star_colors[item] = color
        width, height = self._size
        for i, item in enumerate(self._meteors):
            flight = (elapsed / 3.2 + i * .48) % 1
            x = flight * (width + 160) - 80
            y = height * (.12 + i * .6) + flight * height * .12
            self.canvas.coords(item, x - 50, y - 12, x, y)
        self._job = self.after(frame_delay(self._started), self._tick)

    def destroy(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        super().destroy()
