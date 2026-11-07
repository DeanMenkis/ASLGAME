"""The app: owns the frame loop and the top-level screen state machine."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import math
import time

import pygame

from aslgame import config, theme
from aslgame.game import rhythm
from aslgame.game.app_flow import PLAY_STATES, Action, AppState, next_state
from aslgame.game.chart import load_charts, make_session
from aslgame.game.clock import GameClock
from aslgame.game.rhythm import RhythmSession
from aslgame.game.sign_queue import make_queue
from aslgame.media.player import MediaPlayer, load_tracks
from aslgame.media.sfx import Sfx
from aslgame.presentation.draw import draw_hand
from aslgame.presentation.screens.boot import BootScreen
from aslgame.presentation.screens.common import is_key
from aslgame.presentation.screens.learn import LearnScreen
from aslgame.presentation.screens.menu import MenuScreen
from aslgame.presentation.screens.paused import PausedScreen
from aslgame.presentation.screens.results import ResultsScreen
from aslgame.presentation.screens.rhythm import RhythmScreen
from aslgame.settings import load_settings, save_settings
from aslgame.signs import load_signs


class App:
    def __init__(self):
        # Everything from disk is loaded here, before the loop starts.
        self.signs = load_signs(config.SIGNS_DIR)
        self.settings = load_settings(config.SETTINGS_PATH)
        self.runtime = Runtime(config.WINDOW_TITLE)
        self.sfx = Sfx(self.settings)
        self.charts = load_charts(config.CHARTS_DIR)
        self.tracks = load_tracks(config.MEDIA_DIR, self.charts)
        self.size_px = self.runtime.screen.get_size()
        self.state = AppState.BOOT
        self.play_state = AppState.LEARN
        self.played_item = None
        self.player = None
        fonts = self.runtime.fonts
        self.screens = {
            AppState.BOOT: BootScreen(),
            AppState.MENU: MenuScreen(fonts, set(self.signs), self.charts, set(self.tracks), self.settings, self.size_px, self.sfx),
            AppState.PAUSED: PausedScreen(fonts, self.size_px),
        }

    def start_play(self, state, item_value, now_s):
        """Build a fresh screen for a mode, used by both the menu and retry."""
        fonts = self.runtime.fonts
        self.stop_music()
        if state in (AppState.LEARN, AppState.RECALL):
            self.screens[state] = LearnScreen(fonts, self.signs, item_value, self.size_px, self.settings, self.sfx,
                                              recall=state == AppState.RECALL)
        elif state == AppState.RHYTHM:
            repeats = max(1, math.ceil(config.RHYTHM_MIN_SIGNS / len(item_value.replace(" ", ""))))
            queue = make_queue(" ".join([item_value] * repeats))
            session = RhythmSession([queue.text[i] for i in queue.positions])
            self.screens[state] = RhythmScreen(fonts, self.signs, queue, session, GameClock(now_s), self.size_px, self.settings,
                                               self.sfx)
        elif state == AppState.MUSIC:
            session = make_session(item_value)
            self.player = MediaPlayer(self.tracks[item_value.name], now_s)
            self.screens[state] = RhythmScreen(fonts, self.signs, make_queue(item_value.text), session, self.player, self.size_px,
                                               self.settings, self.sfx)
        self.play_state = state
        self.played_item = item_value

    def stop_music(self):
        if self.player is not None:
            self.player.stop()
            self.player = None

    def apply(self, action, now_s):
        """The one place the app changes screen, and the side effects of each change."""
        new_state = next_state(self.state, action, self.play_state)
        if new_state == self.state:
            return
        self.sfx.play("complete" if new_state == AppState.RESULTS else "click")
        if self.state == AppState.MENU and new_state in PLAY_STATES:
            self.start_play(new_state, self.screens[AppState.MENU].selected_item().value, now_s)
        elif self.state == AppState.RESULTS and new_state in PLAY_STATES:
            self.start_play(new_state, self.played_item, now_s)
        elif new_state == AppState.PAUSED and self.state in (AppState.RHYTHM, AppState.MUSIC):
            self.screens[self.state].pause(now_s)
        elif self.state == AppState.PAUSED and new_state in (AppState.RHYTHM, AppState.MUSIC):
            self.screens[new_state].resume(now_s)
        elif new_state == AppState.RESULTS:
            self.stop_music()
            results = rhythm.summarize(self.screens[self.state].session)
            self.screens[AppState.RESULTS] = ResultsScreen(self.runtime.fonts, results, self.signs, self.size_px)
        if new_state in (AppState.MENU, AppState.QUIT):
            self.stop_music()
        self.state = new_state

    def run(self):
        runtime = self.runtime
        while self.state != AppState.QUIT:
            screen = self.screens[self.state]
            action = None
            for event in pygame.event.get():
                if runtime.handle_common(event):
                    action = Action.QUIT
                elif is_key(event, (pygame.K_c,)):
                    self.settings.finger_colors = not self.settings.finger_colors
                elif is_key(event, (pygame.K_s,)):
                    self.settings.sound = not self.settings.sound
                elif action is None:
                    action = screen.handle_event(event)
            runtime.begin_frame()
            now_s = time.perf_counter()
            hand = runtime.result.hand if runtime.result else None
            action = action or screen.update(now_s, runtime.result)
            screen.draw(runtime.screen, now_s, hand)
            if runtime.debug.visible and hand is not None:
                draw_hand(runtime.screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
            runtime.end_frame()
            if action is not None:
                self.apply(action, now_s)
        runtime.close()
        # Written after the loop so the frame loop never touches the disk.
        save_settings(config.SETTINGS_PATH, self.settings)


def main():
    App().run()
