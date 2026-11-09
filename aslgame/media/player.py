"""Plays one loaded track and keeps the game clock in step with it."""

import pygame

from aslgame import config
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

    def __init__(self, sound, start_s, length_s):
        """Playback starts at start_s (after the countdown) and fades out once length_s has played."""
        self._sound = sound
        self._channel = None
        self._fading = False
        self._length_s = length_s
        self.clock = GameClock(start_s)

    def time(self, real_s):
        game_s = self.clock.time(real_s)
        if self._channel is None and game_s >= 0 and self.clock.paused_at_s is None:
            self._channel = self._sound.play()
        if self._channel is not None and not self._fading and game_s >= self._length_s:
            self._fading = True
            self._channel.fadeout(config.MUSIC_FADE_MS)
        return game_s

    def pause(self, real_s):
        if self._channel is not None:
            self._channel.pause()
        self.clock.pause(real_s)

    def resume(self, real_s):
        if self._channel is not None:
            self._channel.unpause()
        self.clock.resume(real_s)

    def stop(self):
        if self._channel is not None:
            self._channel.stop()
