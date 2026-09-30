"""Animation cadence target, not a guarantee of display refresh rate."""
import math
import time

TARGET_FPS = 180


def frame_delay(started, now=None):
    now = time.monotonic() if now is None else now
    elapsed = max(0.0, now - started)
    next_frame = math.floor(elapsed * TARGET_FPS) + 1
    return max(1, math.ceil((next_frame / TARGET_FPS - elapsed) * 1000))
