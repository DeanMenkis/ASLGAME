"""Short sound effects, synthesized at startup so there are no files to load or license."""

import numpy as np
import pygame

from aslgame import config

# Note frequencies in Hz.
E5, A5, B5, E6, GS6, B6 = 659.25, 880.0, 987.77, 1318.5, 1661.2, 1975.5
MAJOR_SCALE = (1.0, 1.122, 1.26, 1.335, 1.498, 1.682, 1.888, 2.0)


def _envelope(count, attack_s, decay_per_s):
    t = np.arange(count) / config.AUDIO_RATE_HZ
    return np.minimum(1.0, t / attack_s) * np.exp(-decay_per_s * t)


def _tone(frequency_hz, duration_s, decay_per_s=12.0, harmonics=(1.0, 0.3)):
    count = int(duration_s * config.AUDIO_RATE_HZ)
    t = np.arange(count) / config.AUDIO_RATE_HZ
    wave = sum(level * np.sin(2 * np.pi * frequency_hz * (index + 1) * t) for index, level in enumerate(harmonics))
    return wave * _envelope(count, 0.003, decay_per_s)


def _sequence(frequencies_hz, step_s, note_s, decay_per_s=10.0):
    total = np.zeros(int((step_s * (len(frequencies_hz) - 1) + note_s) * config.AUDIO_RATE_HZ))
    for index, frequency_hz in enumerate(frequencies_hz):
        start = int(index * step_s * config.AUDIO_RATE_HZ)
        note = _tone(frequency_hz, note_s, decay_per_s)
        total[start:start + len(note)] += note
    return total


def _buzz(duration_s):
    """A falling, slightly detuned square: clearly a miss, but short and not harsh."""
    count = int(duration_s * config.AUDIO_RATE_HZ)
    t = np.arange(count) / config.AUDIO_RATE_HZ
    frequency_hz = 180 * np.exp(-2.5 * t)
    phase = 2 * np.pi * np.cumsum(frequency_hz) / config.AUDIO_RATE_HZ
    wave = np.sign(np.sin(phase)) * 0.5 + np.sign(np.sin(phase * 1.01)) * 0.5
    return wave * _envelope(count, 0.005, 8.0) * 0.6


def _click():
    count = int(0.03 * config.AUDIO_RATE_HZ)
    rng = np.random.default_rng(0)
    return (rng.uniform(-1, 1, count) * 0.3 + _tone(2400, 0.03, 120)[:count]) * _envelope(count, 0.001, 150)


def _hiss(duration_s):
    """Steam: bright noise that fades, for a fire put out."""
    count = int(duration_s * config.AUDIO_RATE_HZ)
    noise = np.random.default_rng(3).uniform(-1, 1, count)
    return np.diff(noise, prepend=0.0) * _envelope(count, 0.01, 2.8) * 0.3


def _whoosh(duration_s):
    """A rush of air as the fire catches: low noise that swells, then dies."""
    count = int(duration_s * config.AUDIO_RATE_HZ)
    t = np.arange(count) / config.AUDIO_RATE_HZ
    low = np.convolve(np.random.default_rng(4).uniform(-1, 1, count), np.ones(60) / 60, mode="same")
    swell = np.minimum(1.0, t / 0.2) * np.exp(-np.maximum(0.0, t - 0.2) * 5)
    return low * swell * 5.0


def _crackle(duration_s):
    """A few dry pops, for embers catching."""
    count = int(duration_s * config.AUDIO_RATE_HZ)
    rng = np.random.default_rng(5)
    wave = np.zeros(count)
    for start in rng.integers(0, count - 400, 9):
        pop = rng.uniform(-1, 1, 400) * np.exp(-np.arange(400) / 40)
        wave[start:start + 400] += pop * rng.uniform(0.3, 0.8)
    return wave


def _waves():
    waves = {
        "good": _tone(B5, 0.2, 14),
        "ok": _tone(E5, 0.16, 18),
        "miss": _buzz(0.28),
        "confirm": _sequence([A5, E6], 0.07, 0.3, 10),
        "complete": _sequence([E5, A5, E6, GS6, B6], 0.08, 0.45, 7),
        "combo": _sequence([E6, GS6, B6, E6 * 2], 0.04, 0.2, 16),
        "click": _click(),
        "tick": _tone(A5, 0.12, 25),
        "go": _sequence([E6, B6], 0.03, 0.4, 8),
        "lock": _tone(B6, 0.06, 60, (1.0,)),
        "tier": _sequence([E5, B5, E6, GS6, B6, E6 * 2], 0.035, 0.3, 10),
        "word": _sequence([B5, E6, GS6], 0.05, 0.3, 12),
        "break": _buzz(0.45),
        "hiss": _hiss(0.9),
        "ignite": _whoosh(0.7),
        "ember": _crackle(0.5),
    }
    # Perfect climbs a major scale as the combo grows, so a long streak sounds like it is rising.
    for step, ratio in enumerate(MAJOR_SCALE):
        waves[f"perfect{step}"] = _sequence([E6 * ratio, B6 * ratio], 0.05, 0.25, 14)
    return waves


class Sfx:
    """Plays effects when sound is on. Every effect also has a visible cue, so sound is never required."""

    def __init__(self, settings):
        self._settings = settings
        self._sounds = {}
        if pygame.mixer.get_init() is None:
            return
        pygame.mixer.set_num_channels(config.AUDIO_CHANNEL_COUNT)
        for name, wave in _waves().items():
            samples = (np.clip(wave, -1, 1) * config.SFX_VOLUME * 32767).astype(np.int16)
            self._sounds[name] = pygame.sndarray.make_sound(np.repeat(samples[:, None], config.AUDIO_CHANNELS, axis=1).copy())

    def play(self, name):
        if self._settings.sound and name in self._sounds:
            self._sounds[name].play()
