"""Hand tracking thread that publishes the newest HandLandmarker result."""

import threading
import time
from dataclasses import dataclass

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

from aslgame import config
from aslgame.fps import smooth_fps
from aslgame.latest import Latest


@dataclass(frozen=True)
class Hand:
    # (21, 3) in frame pixels. z uses the x scale, as MediaPipe defines it.
    points_px: np.ndarray
    is_left: bool


@dataclass(frozen=True)
class TrackingResult:
    hand: Hand | None
    captured_s: float
    finished_s: float
    inference_ms: float


class Tracker:
    def __init__(self, frames):
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(config.MODEL_PATH)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.MAX_HANDS,
            min_hand_detection_confidence=config.MIN_HAND_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_HAND_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._frames = frames
        self.results = Latest()
        self.fps = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="tracker", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(config.THREAD_JOIN_TIMEOUT_S)
        self._landmarker.close()

    def _run(self):
        version = 0
        last_timestamp_ms = -1
        last_s = time.perf_counter()
        while not self._stop.is_set():
            version, frame = self._frames.wait_newer(version, config.TRACKER_WAIT_TIMEOUT_S)
            if frame is None:
                continue
            # VIDEO mode requires strictly increasing timestamps.
            timestamp_ms = max(int(frame.captured_s * 1000), last_timestamp_ms + 1)
            last_timestamp_ms = timestamp_ms
            started_s = time.perf_counter()
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame.rgb)
            raw = self._landmarker.detect_for_video(image, timestamp_ms)
            finished_s = time.perf_counter()
            self.results.publish(TrackingResult(
                hand=first_hand(raw, frame.rgb.shape),
                captured_s=frame.captured_s,
                finished_s=finished_s,
                inference_ms=(finished_s - started_s) * 1000,
            ))
            self.fps = smooth_fps(self.fps, finished_s - last_s)
            last_s = finished_s


def first_hand(raw, frame_shape):
    if not raw.hand_landmarks:
        return None
    height_px, width_px = frame_shape[:2]
    normalized = np.array([(p.x, p.y, p.z) for p in raw.hand_landmarks[0]], dtype=np.float32)
    points_px = normalized * np.array([width_px, height_px, width_px], dtype=np.float32)
    # In play testing the Tasks API label came out swapped for our mirrored frames,
    # so the player's right hand is reported as "Left".
    label = raw.handedness[0][0].category_name
    is_left = (label == "Right") if config.CAMERA_MIRROR else (label == "Left")
    return Hand(points_px, is_left)
