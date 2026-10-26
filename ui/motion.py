"""Animation cadence target, not a guarantee of display refresh rate."""
import ctypes
import math
import sys
import time

TARGET_FPS = 180


def enable_high_resolution_timer():
    if not sys.platform.startswith("win"):
        return False
    return ctypes.windll.winmm.timeBeginPeriod(1) == 0


def disable_high_resolution_timer():
    if sys.platform.startswith("win"):
        ctypes.windll.winmm.timeEndPeriod(1)


def frame_delay(started, now=None):
    now = time.monotonic() if now is None else now
    elapsed = max(0.0, now - started)
    next_frame = math.floor(elapsed * TARGET_FPS) + 1
    return max(1, math.ceil((next_frame / TARGET_FPS - elapsed) * 1000))


def ease_out_quint(value):
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 5


def mix_color(start, end, amount):
    amount = max(0.0, min(1.0, amount))
    channels = []
    for offset in (1, 3, 5):
        first = int(start[offset:offset + 2], 16)
        second = int(end[offset:offset + 2], 16)
        channels.append(round(first + (second - first) * amount))
    return "#%02x%02x%02x" % tuple(channels)
