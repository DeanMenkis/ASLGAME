"""Records the game screen to a video file for a backup demo. Encoding runs on its own thread."""

import queue
import threading
import time

import cv2
import numpy as np
import pygame

from aslgame import config


class Recorder:
    def __init__(self):
        self._frames = queue.Queue(maxsize=config.RECORD_QUEUE_FRAMES)
        self._thread = None
        self._next_frame_s = 0.0
        self.path = None
        self.dropped = 0

    @property
    def active(self):
        return self._thread is not None

    def toggle(self, size_px):
        if self.active:
            self.stop()
        else:
            self.start(size_px)

    def start(self, size_px):
        config.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.path = config.RECORDINGS_DIR / time.strftime("aslgame-%Y%m%d-%H%M%S.mp4")
        self.dropped = 0
        self._thread = threading.Thread(target=self._run, args=(self.path, size_px), name="recorder", daemon=True)
        self._thread.start()

    def stop(self):
        self._frames.put(None)
        self._thread.join(config.THREAD_JOIN_TIMEOUT_S * 5)
        self._thread = None

    def capture(self, screen, now_s):
        """Called each frame. Copies the screen at the recording rate and never waits on the encoder."""
        if not self.active or now_s < self._next_frame_s:
            return
        self._next_frame_s = now_s + 1.0 / config.RECORD_FPS
        try:
            self._frames.put_nowait(pygame.image.tobytes(screen, "RGB"))
        except queue.Full:
            self.dropped += 1

    def _run(self, path, size_px):
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"avc1"), config.RECORD_FPS, size_px)
        while (data := self._frames.get()) is not None:
            rgb = np.frombuffer(data, dtype=np.uint8).reshape(size_px[1], size_px[0], 3)
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        writer.release()
