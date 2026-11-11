"""Camera thread that publishes the newest RGB frame."""

import sys
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from aslgame import config
from aslgame.capture.print_look import Printer
from aslgame.fps import smooth_fps
from aslgame.latest import Latest


@dataclass(frozen=True)
class Frame:
    rgb: np.ndarray
    captured_s: float
    brightness: float  # mean level from 0 to 255
    display: np.ndarray | None = None  # printed copy for the screen; tracking always uses rgb


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
        # A Look set by the game each frame, or None for the plain picture. Printed here, off the frame loop.
        self.look = None
        self._printer = Printer(self.size_px)
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
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            # A sparse sample is enough to judge the light, and costs almost nothing.
            brightness = float(rgb[::config.BRIGHTNESS_SAMPLE_STEP, ::config.BRIGHTNESS_SAMPLE_STEP].mean())
            look = self.look
            display = self._printer.print(rgb, look) if look is not None else None
            self.frames.publish(Frame(rgb, captured_s, brightness, display))
            self.fps = smooth_fps(self.fps, captured_s - last_s)
            last_s = captured_s



def open_capture():
    """Open the camera on the main thread, retrying while macOS shows its permission prompt."""
    give_up_s = time.perf_counter() + config.CAMERA_OPEN_TIMEOUT_S
    while True:
        capture = cv2.VideoCapture(config.CAMERA_INDEX, camera_backend())
        if capture.isOpened():
            return capture
        capture.release()
        if time.perf_counter() > give_up_s:
            raise RuntimeError(f"Cannot open camera {config.CAMERA_INDEX}. Check camera permission.")
        time.sleep(config.CAMERA_OPEN_RETRY_S)


def camera_backend():
    """The platform's native camera API. Windows support is untested."""
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform == "win32":
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY
