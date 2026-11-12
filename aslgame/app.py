"""The app: owns the frame loop and the top-level screen state machine."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import random
import time

import pygame

from aslgame import config, theme
from aslgame.capture.print_look import Look
from aslgame.game import mastery, music, scoring
from aslgame.game.app_flow import PLAY_STATES, Action, AppState, next_state
from aslgame.game.chart import load_charts
from aslgame.game.motion import with_motion_letters
from aslgame.game.sign_queue import make_queue
from aslgame.game.words import DECKS_BY_NAME, draw_words
from aslgame.media.player import MediaPlayer, load_tracks
from aslgame.media.sfx import Sfx
from aslgame.presentation.draw import draw_hand
from aslgame.presentation.light_warning import LightWarning
from aslgame.presentation.screens.boot import BootScreen
from aslgame.presentation.screens.common import is_key
from aslgame.presentation.screens.learn import LearnScreen
from aslgame.presentation.screens.menu import MenuScreen
from aslgame.presentation.screens.music import MusicScreen
from aslgame.presentation.screens.paused import PausedScreen
from aslgame.presentation.screens.results import ResultsScreen
from aslgame.records import load_records, save_records, update_record
from aslgame.settings import load_settings, save_settings
from aslgame.signs import load_signs

COUNTDOWN_S = config.COUNTDOWN_STEPS * config.COUNTDOWN_STEP_S


class App:
    def __init__(self):
        # Everything from disk is loaded here, before the loop starts.
        self.signs = with_motion_letters(load_signs(config.SIGNS_DIR))
        self.settings = load_settings(config.SETTINGS_PATH)
        self.records = load_records(config.RECORDS_PATH)
        self.letters = mastery.clean(load_records(config.LETTERS_PATH))
        self.runtime = Runtime(config.WINDOW_TITLE)
        self.sfx = Sfx(self.settings)
        self.charts = load_charts(config.CHARTS_DIR)
        self.tracks = load_tracks(config.MEDIA_DIR, self.charts)
        self.size_px = self.runtime.screen.get_size()
        self.rng = random.Random()
        self.state = AppState.BOOT
        self.play_state = AppState.LEARN
        self.played = None  # (item, level, run length, record key) of the run, used by retry
        self.player = None
        fonts = self.runtime.fonts
        self.light_warning = LightWarning(fonts, self.size_px)
        track_lengths = {name: sound.get_length() for name, sound in self.tracks.items()}
        self.menu = MenuScreen(fonts, self.signs, self.charts, track_lengths, self.settings, self.records, self.letters,
                               self.size_px, self.sfx)
        self.screens = {
            AppState.BOOT: BootScreen(),
            AppState.MENU: self.menu,
            AppState.PAUSED: PausedScreen(fonts, self.size_px),
        }

    def start_play(self, state, played, now_s):
        """Build a fresh screen for a mode, used by both the menu and retry. Words are drawn fresh every time."""
        item, level, length_s, _ = played
        fonts = self.runtime.fonts
        self.stop_music()
        start_s = now_s + COUNTDOWN_S

        def draw(deck, min_signs):
            return draw_words(deck, level, min_signs, self.rng, self.signs, lambda letter: mastery.need(self.letters, letter))

        if state in (AppState.LEARN, AppState.RECALL):
            words = draw(item, config.LEARN_RUN_SIGNS)
            self.screens[state] = LearnScreen(fonts, self.signs, " ".join(words), self.size_px, self.settings, self.sfx,
                                              recall=state == AppState.RECALL)
        else:
            words = draw(DECKS_BY_NAME[item.deck], music.signs_for(length_s))
            self.player = MediaPlayer(self.tracks[item.name], start_s, length_s)
            self.screens[state] = MusicScreen(fonts, self.signs, make_queue(" ".join(words)),
                                              music.make_session(words, item, level, length_s), self.player, self.size_px,
                                              self.settings, self.sfx)
        self.play_state = state
        self.played = played

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
        in_run = self.state in PLAY_STATES or self.state == AppState.PAUSED
        if in_run and new_state not in PLAY_STATES and new_state != AppState.PAUSED:
            # However a run ends, finished or abandoned, the letters signed in it count.
            mastery.record(self.letters, self.screens[self.play_state].results)
            self.menu.refresh()
        if self.state == AppState.MENU and new_state in PLAY_STATES:
            menu = self.menu
            played = (menu.selected_item().value, menu.level, menu.run_length_s(), menu.record_key())
            self.start_play(new_state, played, now_s)
        elif self.state == AppState.RESULTS and new_state in PLAY_STATES:
            self.start_play(new_state, mastery.practise_run(self.played) if action == Action.PRACTISE else self.played, now_s)
        elif new_state == AppState.PAUSED and self.state == AppState.MUSIC:
            self.screens[self.state].pause(now_s)
        elif self.state == AppState.PAUSED and new_state == AppState.MUSIC:
            self.screens[new_state].resume(now_s)
        elif new_state == AppState.RESULTS:
            self.stop_music()
            results = scoring.summarize(self.screens[self.state].tally)
            new_best = update_record(self.records, self.played[3], results.score, results.grade) and results.score > 0
            self.screens[AppState.RESULTS] = ResultsScreen(self.runtime.fonts, results, self.signs, self.size_px, new_best)
        if new_state in (AppState.MENU, AppState.QUIT):
            self.stop_music()
        self.state = new_state

    def run(self):
        runtime = self.runtime
        last_click = None
        while self.state != AppState.QUIT:
            screen = self.screens[self.state]
            action = None
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    last_click = event.pos
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
            # The camera thread prints frames in the look the screen asks for; overlays keep the look under them.
            look = getattr(screen, "camera_look", None)
            if not self.settings.print_camera:
                runtime.camera.look = None
            elif look is not None:
                runtime.camera.look = look()
            elif self.state not in (AppState.PAUSED, AppState.RESULTS):
                runtime.camera.look = Look()
            screen.draw(runtime.screen, now_s, hand)
            self.light_warning.update(now_s, runtime.frame)
            if self.state in PLAY_STATES:
                self.light_warning.draw(runtime.screen, now_s)
            if runtime.debug.visible:
                # Where the game thinks the mouse is, and where it saw the last click.
                pygame.draw.circle(runtime.screen, theme.YELLOW, pygame.mouse.get_pos(), 12, 2)
                if last_click is not None:
                    pygame.draw.circle(runtime.screen, theme.RED, last_click, 6)
            if runtime.debug.visible and hand is not None:
                draw_hand(runtime.screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
            runtime.end_frame()
            if action is not None:
                self.apply(action, now_s)
        runtime.close()
        # Written after the loop so the frame loop never touches the disk.
        save_settings(config.SETTINGS_PATH, self.settings)
        save_records(config.RECORDS_PATH, self.records)
        save_records(config.LETTERS_PATH, self.letters)


def main():
    App().run()
