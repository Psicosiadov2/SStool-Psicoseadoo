"""Monotonic cooldown: changing tabs cannot reset it."""
import time


class Cooldown:
    def __init__(self, duration=5.0, clock=time.monotonic):
        self.duration = duration
        self.clock = clock
        self.deadline = 0.0

    @property
    def remaining(self):
        return max(0.0, self.deadline - self.clock())

    def start(self):
        self.deadline = self.clock() + self.duration
