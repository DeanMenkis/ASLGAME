"""Smoothed rate measurement shared by the threads and the main loop."""

from aslgame import config


def smooth_fps(fps, interval_s):
    if interval_s <= 0:
        return fps
    return fps + (1.0 / interval_s - fps) * config.FPS_SMOOTHING
