"""Camera thread that publishes the newest RGB frame."""

import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from aslgame import config
from aslgame.fps import smooth_fps
from aslgame.latest import Latest


@dataclass(frozen=True)
class Frame:
    rgb: np.ndarray
    captured_s: float


class Camera:
    def __init__(self):
        self._capture = open_capture()
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH_PX)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT_PX)
        self._capture.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        # The camera may not support the requested size.
        self.size_px = (
            int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        self.frames = Latest()
        self.fps = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="camera", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(config.THREAD_JOIN_TIMEOUT_S)
        self._capture.release()

    def _run(self):
        last_s = time.perf_counter()
        while not self._stop.is_set():
            ok, bgr = self._capture.read()
            if not ok:
                time.sleep(config.CAMERA_RETRY_S)
                continue
            captured_s = time.perf_counter()
            if config.CAMERA_MIRROR:
                bgr = cv2.flip(bgr, 1)
            self.frames.publish(Frame(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), captured_s))
            self.fps = smooth_fps(self.fps, captured_s - last_s)
            last_s = captured_s



def open_capture():
    """Open the camera on the main thread, retrying while macOS shows its permission prompt."""
    give_up_s = time.perf_counter() + config.CAMERA_OPEN_TIMEOUT_S
    while True:
        capture = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_AVFOUNDATION)
        if capture.isOpened():
            return capture
        capture.release()
        if time.perf_counter() > give_up_s:
            raise RuntimeError(f"Cannot open camera {config.CAMERA_INDEX}. Check camera permission.")
        time.sleep(config.CAMERA_OPEN_RETRY_S)
