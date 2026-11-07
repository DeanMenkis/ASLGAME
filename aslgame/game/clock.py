"""The game clock: the single source of truth for when notes are due."""

from dataclasses import dataclass


@dataclass
class GameClock:
    """Game time in seconds since start, not counting paused time. Real time is passed in, so it is testable."""

    started_s: float
    paused_at_s: float | None = None

    def time(self, real_s):
        return (self.paused_at_s if self.paused_at_s is not None else real_s) - self.started_s

    def pause(self, real_s):
        if self.paused_at_s is None:
            self.paused_at_s = real_s

    def resume(self, real_s):
        if self.paused_at_s is not None:
            self.started_s += real_s - self.paused_at_s
            self.paused_at_s = None
