"""Six-second, timer-driven intro. No downloads or blocking waits."""
import math
import random
import time
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from core import theme
from core.windows_shell import asset_path
from ui.motion import ease_out_quint, frame_delay


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
        self._last_star_update = -1.0
        self._size = (1, 1)
        for index in range(64):
            x, y = rng.random(), rng.random()
            radius = 2.5 if index % 6 == 0 else 1.2
            item = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0,
                                               fill="#397db0", outline="")
            self._stars.append((item, x, y, radius, rng.random() * math.tau))
        self._meteors = [
            self.canvas.create_line(0, 0, 0, 0, fill=color, width=1)
            for color in ("#245d88", "#398fc8", "#70c7ff")
        ]
        self._rings = [
            self.canvas.create_arc(0, 0, 0, 0, start=0, extent=62,
                                   style="arc", outline=color, width=1)
            for color in ("#173b59", "#286c9c", "#4aa9e9")
        ]
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
        self._loading_label = ctk.CTkLabel(
            center,
            text="Loading SStool Kits",
            text_color=theme.TEXT_PRIMARY,
            font=theme.FONT_CARD_DESC,
        )
        self._loading_label.pack()
        ctk.CTkLabel(
            center,
            text="INITIALIZING FORENSIC MODULES",
            text_color=theme.TEXT_FAINT,
            font=theme.FONT_EYEBROW,
        ).pack(pady=(5, 0))
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
        center_x, center_y = event.width / 2, event.height / 2
        for index, ring in enumerate(self._rings):
            radius = (150 + index * 24) * self._get_widget_scaling()
            self.canvas.coords(
                ring,
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            )
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
        self.progress.set(ease_out_quint(phase))
        self._loading_label.configure(
            text="Loading SStool Kits" + "." * (1 + int(elapsed / .35) % 3)
        )
        last_star_update = getattr(self, "_last_star_update", -1.0)
        if not isinstance(last_star_update, (int, float)):
            last_star_update = -1.0
        stars = getattr(self, "_stars", ())
        if not isinstance(stars, (list, tuple)):
            stars = ()
        if elapsed - last_star_update >= 1 / 30:
            self._last_star_update = elapsed
            for item, _, _, _, offset in stars:
                brightness = int(130 + 80 * math.sin(elapsed * 1.8 + offset))
                color = f"#{max(25, brightness // 3):02x}{max(70, brightness * 2 // 3):02x}{brightness:02x}"
                if self._star_colors.get(item) != color:
                    self.canvas.itemconfigure(item, fill=color)
                    self._star_colors[item] = color
        width, height = self._size
        meteors = getattr(self, "_meteors", ())
        if not isinstance(meteors, (list, tuple)):
            meteors = ()
        for i, item in enumerate(meteors):
            flight = (elapsed / 3.2 + i * .48) % 1
            x = flight * (width + 160) - 80
            y = height * (.12 + i * .36) + flight * height * .12
            self.canvas.coords(item, x - 50, y - 12, x, y)
        rings = getattr(self, "_rings", ())
        if not isinstance(rings, (list, tuple)):
            rings = ()
        for index, ring in enumerate(rings):
            direction = -1 if index % 2 else 1
            self.canvas.itemconfigure(
                ring,
                start=(elapsed * (28 + index * 9) * direction + index * 95) % 360,
            )
        self._job = self.after(frame_delay(self._started), self._tick)

    def destroy(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        super().destroy()
