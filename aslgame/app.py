"""The app: owns the frame loop and the top-level screen state machine."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import time

import pygame

from aslgame import config
from aslgame.game import rhythm
from aslgame.game.app_flow import Action, AppState, next_state
from aslgame.presentation.screens.boot import BootScreen
from aslgame.presentation.screens.learn import LearnScreen
from aslgame.presentation.screens.menu import MenuScreen
from aslgame.presentation.screens.paused import PausedScreen
from aslgame.presentation.screens.results import ResultsScreen
from aslgame.presentation.screens.rhythm import RhythmScreen
from aslgame.signs import load_signs


class App:
    def __init__(self):
        self.signs = load_signs(config.SIGNS_DIR)
        self.runtime = Runtime(config.WINDOW_TITLE)
        self.size_px = self.runtime.screen.get_size()
        self.state = AppState.BOOT
        self.paused_from = AppState.LEARN
        self.screens = {
            AppState.BOOT: BootScreen(),
            AppState.MENU: MenuScreen(self.runtime.fonts, set(self.signs), self.size_px),
            AppState.PAUSED: PausedScreen(self.runtime.fonts, self.size_px),
        }

    def apply(self, action, now_s):
        """The one place the app changes screen, and the side effects of each change."""
        new_state = next_state(self.state, action, self.paused_from)
        fonts = self.runtime.fonts
        if action == Action.START_LEARN and new_state == AppState.LEARN:
            word = self.screens[AppState.MENU].selected_word()
            self.screens[AppState.LEARN] = LearnScreen(fonts, self.signs, word, self.size_px)
        elif action == Action.START_RHYTHM and new_state == AppState.RHYTHM:
            word = self.screens[AppState.MENU].selected_word()
            self.screens[AppState.RHYTHM] = RhythmScreen(fonts, self.signs, word, self.size_px, now_s)
        elif action == Action.PAUSE and new_state == AppState.PAUSED:
            self.paused_from = self.state
            if self.state == AppState.RHYTHM:
                self.screens[AppState.RHYTHM].pause(now_s)
        elif action == Action.RESUME and new_state == AppState.RHYTHM:
            self.screens[AppState.RHYTHM].resume(now_s)
        elif action == Action.FINISH and new_state == AppState.RESULTS:
            results = rhythm.summarize(self.screens[AppState.RHYTHM].session)
            self.screens[AppState.RESULTS] = ResultsScreen(fonts, results, self.signs, self.size_px)
        self.state = new_state

    def run(self):
        runtime = self.runtime
        while self.state != AppState.QUIT:
            screen = self.screens[self.state]
            action = None
            for event in pygame.event.get():
                if runtime.handle_common(event):
                    action = Action.QUIT
                elif action is None:
                    action = screen.handle_event(event)
            runtime.begin_frame()
            now_s = time.perf_counter()
            hand = runtime.result.hand if runtime.result else None
            action = action or screen.update(now_s, runtime.result)
            screen.draw(runtime.screen, now_s, hand)
            runtime.end_frame()
            if action is not None:
                self.apply(action, now_s)
        runtime.close()


def main():
    App().run()
