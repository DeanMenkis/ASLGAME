"""The app: owns the frame loop and the top-level screen state machine."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import time

import pygame

from aslgame import config
from aslgame.game.app_flow import AppState, next_state
from aslgame.presentation.screens import BootScreen, LearnScreen, MenuScreen, PausedScreen
from aslgame.signs import load_signs


class App:
    def __init__(self):
        self.signs = load_signs(config.SIGNS_DIR)
        self.runtime = Runtime(config.WINDOW_TITLE)
        size_px = self.runtime.screen.get_size()
        self.state = AppState.BOOT
        self.boot = BootScreen()
        self.menu = MenuScreen(self.runtime.fonts, set(self.signs), size_px)
        self.paused = PausedScreen(self.runtime.fonts, size_px)
        self.learn = None

    def active_screen(self):
        return {
            AppState.BOOT: self.boot,
            AppState.MENU: self.menu,
            AppState.LEARN: self.learn,
            AppState.PAUSED: self.paused,
        }[self.state]

    def apply(self, action):
        """The one place the app changes screen."""
        new_state = next_state(self.state, action)
        if self.state == AppState.MENU and new_state == AppState.LEARN:
            self.learn = LearnScreen(self.runtime.fonts, self.signs, self.menu.selected_word(), self.runtime.screen.get_size())
        self.state = new_state

    def run(self):
        runtime = self.runtime
        while self.state != AppState.QUIT:
            screen = self.active_screen()
            action = None
            for event in pygame.event.get():
                if runtime.handle_common(event):
                    self.state = AppState.QUIT
                elif action is None:
                    action = screen.handle_event(event)
            runtime.begin_frame()
            now_s = time.perf_counter()
            hand = runtime.result.hand if runtime.result else None
            action = action or screen.update(now_s, runtime.result)
            screen.draw(runtime.screen, now_s, hand)
            runtime.end_frame()
            if action is not None and self.state != AppState.QUIT:
                self.apply(action)
        runtime.close()


def main():
    App().run()
