"""Resize handles for the existing borderless window (physical pixels)."""
import tkinter as tk

from core import theme


def resized_bounds(bounds, edge, dx, dy, minimum):
    x, y, width, height = bounds
    min_width, min_height = minimum
    if "e" in edge:
        width = max(min_width, width + dx)
    if "s" in edge:
        height = max(min_height, height + dy)
    if "w" in edge:
        new_width = max(min_width, width - dx)
        x += width - new_width
        width = new_width
    if "n" in edge:
        new_height = max(min_height, height - dy)
        y += height - new_height
        height = new_height
    return x, y, width, height


class ResizeHandles:
    def __init__(self, app):
        self.app = app
        self.start = None
        self.handles = []
        layouts = {
            "n": dict(relx=0, rely=0, relwidth=1, height=5),
            "s": dict(relx=0, rely=1, relwidth=1, height=5, anchor="sw"),
            "w": dict(relx=0, rely=0, relheight=1, width=5),
            "e": dict(relx=1, rely=0, relheight=1, width=5, anchor="ne"),
            "nw": dict(relx=0, rely=0, width=10, height=10),
            "ne": dict(relx=1, rely=0, width=10, height=10, anchor="ne"),
            "sw": dict(relx=0, rely=1, width=10, height=10, anchor="sw"),
            "se": dict(relx=1, rely=1, width=10, height=10, anchor="se"),
        }
        for edge, layout in layouts.items():
            cursor = {"n": "sb_v_double_arrow", "s": "sb_v_double_arrow",
                      "w": "sb_h_double_arrow", "e": "sb_h_double_arrow",
                      "nw": "top_left_corner", "ne": "top_right_corner",
                      "sw": "bottom_left_corner", "se": "bottom_right_corner"}[edge]
            # Keep the resize hit areas, without painting a colored outer frame.
            handle = tk.Frame(app, bg=theme.BG_APP, cursor=cursor,
                              borderwidth=0, highlightthickness=0)
            handle.place(**layout)
            handle.bind("<ButtonPress-1>", lambda event, e=edge: self.begin(event, e))
            handle.bind("<B1-Motion>", self.drag)
            handle.bind("<ButtonRelease-1>", self.end)
            self.handles.append(handle)

    def begin(self, event, edge):
        if self.app.titlebar._maximized:
            return "break"
        self.start = (edge, event.x_root, event.y_root,
                      (self.app.winfo_x(), self.app.winfo_y(),
                       self.app.winfo_width(), self.app.winfo_height()))
        event.widget.grab_set()
        return "break"

    def drag(self, event):
        if self.start is None:
            return "break"
        edge, px, py, bounds = self.start
        # Tk's native minimum and event coordinates are physical pixels;
        # CTk.geometry() would scale them a second time on high-DPI screens.
        minimum = tuple(map(int, self.app.tk.call("wm", "minsize", self.app._w)))
        x, y, width, height = resized_bounds(
            bounds, edge, event.x_root - px, event.y_root - py, minimum)
        self.app.tk.call("wm", "geometry", self.app._w,
                         f"{width}x{height}{x:+d}{y:+d}")
        return "break"

    def end(self, event):
        self.start = None
        if event.widget.grab_current() == event.widget:
            event.widget.grab_release()
        return "break"
