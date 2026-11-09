"""The app: owns the frame loop and the top-level screen state machine."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import random
import time

import pygame

from aslgame import config, theme
from aslgame.game import rush, scoring
from aslgame.game.app_flow import PLAY_STATES, TIMED_STATES, Action, AppState, next_state
from aslgame.game.chart import load_charts, make_session, signs_needed
from aslgame.game.clock import GameClock
from aslgame.game.motion import with_motion_letters
from aslgame.game.rhythm import RhythmSession, signs_for
from aslgame.game.sign_queue import make_queue, word_ends
from aslgame.game.words import DECKS_BY_NAME, draw_words
from aslgame.media.player import MediaPlayer, load_tracks
from aslgame.media.sfx import Sfx
from aslgame.presentation.draw import draw_hand
from aslgame.presentation.light_warning import LightWarning
from aslgame.presentation.screens.boot import BootScreen
from aslgame.presentation.screens.common import is_key
from aslgame.presentation.screens.learn import LearnScreen
from aslgame.presentation.screens.menu import MenuScreen
from aslgame.presentation.screens.paused import PausedScreen
from aslgame.presentation.screens.results import ResultsScreen
from aslgame.presentation.screens.rhythm import RhythmScreen
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
        self.menu = MenuScreen(fonts, self.signs, self.charts, track_lengths, self.settings, self.records, self.size_px, self.sfx)
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
        if state in (AppState.LEARN, AppState.RECALL):
            words = draw_words(item, level, config.LEARN_RUN_SIGNS, self.rng, self.signs)
            self.screens[state] = LearnScreen(fonts, self.signs, " ".join(words), self.size_px, self.settings, self.sfx,
                                              recall=state == AppState.RECALL)
        elif state == AppState.RHYTHM:
            beats = config.LEVEL_BEATS_PER_NOTE[level]
            words = draw_words(item, level, signs_for(length_s, config.RHYTHM_BPM * config.SPEED_MAX, beats), self.rng, self.signs)
            session = RhythmSession([c for w in words for c in w], word_ends(words), beats_per_note=beats,
                                    last_due_s=length_s - config.HIT_WINDOW_S - config.FEEDBACK_S)
            self.screens[state] = RhythmScreen(fonts, self.signs, make_queue(" ".join(words)), session, GameClock(start_s),
                                               self.size_px, self.settings, self.sfx, length_s)
        elif state == AppState.MUSIC:
            deck = DECKS_BY_NAME[item.deck]
            words = draw_words(deck, level, signs_needed(item, level, length_s), self.rng, self.signs)
            session = make_session(item, words, level, length_s)
            self.player = MediaPlayer(self.tracks[item.name], start_s, length_s)
            self.screens[state] = RhythmScreen(fonts, self.signs, make_queue(" ".join(words)), session, self.player, self.size_px,
                                               self.settings, self.sfx, length_s)
        elif state == AppState.RUSH:
            words = draw_words(item, level, rush.signs_for(length_s), self.rng, self.signs)
            session = rush.RushSession([c for w in words for c in w], word_ends(words), float(length_s), config.RUSH_FUSE_S[level])
            self.screens[state] = RhythmScreen(fonts, self.signs, make_queue(" ".join(words)), session, GameClock(start_s),
                                               self.size_px, self.settings, self.sfx, length_s)
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
        if self.state == AppState.MENU and new_state in PLAY_STATES:
            menu = self.menu
            played = (menu.selected_item().value, menu.level, menu.run_length_s(), menu.record_key())
            self.start_play(new_state, played, now_s)
        elif self.state == AppState.RESULTS and new_state in PLAY_STATES:
            self.start_play(new_state, self.played, now_s)
        elif new_state == AppState.PAUSED and self.state in TIMED_STATES:
            self.screens[self.state].pause(now_s)
        elif self.state == AppState.PAUSED and new_state in TIMED_STATES:
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
            self.light_warning.update(now_s, runtime.frame)
            if self.state in PLAY_STATES:
                self.light_warning.draw(runtime.screen, now_s)
            if runtime.debug.visible and hand is not None:
                draw_hand(runtime.screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
            runtime.end_frame()
            if action is not None:
                self.apply(action, now_s)
        runtime.close()
        # Written after the loop so the frame loop never touches the disk.
        save_settings(config.SETTINGS_PATH, self.settings)
        save_records(config.RECORDS_PATH, self.records)


def main():
    App().run()
