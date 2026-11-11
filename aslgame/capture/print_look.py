"""Prints the camera picture in the game's three spot inks, the way a press would: shadows in blue, skin and warm things in red, and a yellow plate that joins as play heats up. Runs on the camera thread."""

import math
from dataclasses import dataclass

import cv2
import numpy as np

from aslgame import config, theme


@dataclass(frozen=True)
class Look:
    heat: float = 0.0  # 0 prints blue and red only; 1 adds the full yellow plate
    slip: float = 0.0  # 0 to 1: how far the plates have slipped out of register after a miss


def halftone_screen(size_px, pitch_px, angle_deg):
    """A dot screen at an angle, from -0.5 to 0.5. Added to a plate's tone, it gathers the ink into dots."""
    width, height = size_px
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    angle = math.radians(angle_deg)
    u = xx * math.cos(angle) + yy * math.sin(angle)
    v = -xx * math.sin(angle) + yy * math.cos(angle)
    return (0.25 * (np.cos(2 * np.pi * u / pitch_px) + np.cos(2 * np.pi * v / pitch_px))).astype(np.float32)


class Printer:
    """Made once for the camera's size. The picture is printed small and scaled up, which softens the dots for free."""

    def __init__(self, size_px):
        self._size_px = size_px
        self._small_px = (size_px[0] // config.PRINT_SCALE, size_px[1] // config.PRINT_SCALE)
        self._screens = [halftone_screen(self._small_px, config.PRINT_PITCH_PX, angle) for angle in config.PRINT_ANGLES_DEG]
        self._paper = np.array(theme.PAPER, np.float32)
        # How much of each channel an ink takes away at full strength.
        self._takes = [1.0 - np.array(ink, np.float32) / 255.0 for ink in (theme.BLUE, theme.RED, theme.YELLOW)]

    def _plate(self, tone, screen):
        """Tone from 0 to 1 as ink: part smooth, part gathered into soft dots, so the picture stays easy to read."""
        # No tone leaves bare paper: a dot only starts where the tone passes the screen.
        dots = np.clip((tone + screen - 0.5) * config.PRINT_DOT_CONTRAST + 0.5 * np.minimum(1.0, tone * 4.0), 0.0, 1.0)
        return tone * (1.0 - config.PRINT_DOTS) + dots * config.PRINT_DOTS

    def print(self, rgb, look):
        small = cv2.resize(rgb, self._small_px, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        red, green, blue = small[..., 0], small[..., 1], small[..., 2]
        light = 0.3 * red + 0.59 * green + 0.11 * blue
        warm = red - blue
        tones = [
            np.clip(config.PRINT_BLUE_GAIN * (1.0 - light) ** config.PRINT_BLUE_CURVE, 0.0, config.PRINT_MAX_INK),
            np.clip(warm * (config.PRINT_RED_GAIN + config.PRINT_RED_HEAT_GAIN * look.heat), 0.0, config.PRINT_MAX_INK),
        ]
        if look.heat > 0.01:
            tones.append(np.clip((np.minimum(red, green) - blue) * config.PRINT_YELLOW_GAIN + config.PRINT_YELLOW_BASE * light,
                                 0.0, config.PRINT_MAX_INK) * look.heat)
        plates = [self._plate(tone, screen) for tone, screen in zip(tones, self._screens)]
        slip_px = int(round(look.slip * config.PRINT_SLIP_PX / config.PRINT_SCALE))
        if slip_px:
            # Out of register: the red plate slides one way and the yellow the other.
            plates[1] = np.roll(plates[1], slip_px, axis=1)
            if len(plates) > 2:
                plates[2] = np.roll(plates[2], -slip_px, axis=0)
        out = np.empty((*light.shape, 3), np.float32)
        for channel in range(3):
            value = np.full(light.shape, self._paper[channel], np.float32)
            for plate, takes in zip(plates, self._takes):
                value *= 1.0 - plate * takes[channel]
            out[..., channel] = value
        return cv2.resize(out.astype(np.uint8), self._size_px, interpolation=cv2.INTER_LINEAR)
