"""Plays one loaded track and keeps the game clock in step with it."""

import pygame

from aslgame.game.clock import GameClock


def load_tracks(media_dir, charts):
    """Load every chart's audio at startup. Charts whose file is missing or unreadable are left out."""
    if pygame.mixer.get_init() is None:
        return {}
    tracks = {}
    for chart in charts:
        path = media_dir / chart.media
        if path.exists():
            try:
                tracks[chart.name] = pygame.mixer.Sound(str(path))
            except pygame.error:
                continue
    return tracks


class MediaPlayer:
    """The clock starts the moment playback starts, and pauses with it, so notes stay on the music."""

    def __init__(self, sound, real_s):
        self._channel = sound.play()
        self.clock = GameClock(real_s)

    def time(self, real_s):
        return self.clock.time(real_s)

    def pause(self, real_s):
        self._channel.pause()
        self.clock.pause(real_s)

    def resume(self, real_s):
        self._channel.unpause()
        self.clock.resume(real_s)

    def stop(self):
        self._channel.stop()
