"""Menu: paper and ink. Pick a mode, a deck or song, a level, and a length. Sign at the camera and the ensō reads it."""

import math
from dataclasses import dataclass

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.game.app_flow import Action
from aslgame.game.motion import MOTION_SIGNS
from aslgame.game.words import DECKS, DECKS_BY_NAME, pool
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.about import AboutPanel
from aslgame.presentation.screens.common import is_key
from aslgame.presentation.screens.help import HelpPanel
from aslgame.presentation.screens.settings import SettingsPanel
from aslgame.presentation.ui import clicked
from aslgame.records import record_key

LEFT_PX = theme.MARGIN_PX * 2
TITLE_Y_PX = theme.GRID_PX * 9
MODES_Y_PX = theme.GRID_PX * 20
LIST_TOP_PX = theme.GRID_PX * 28
ROW_PX = theme.GRID_PX * 7
MAX_ROWS = 8
LIST_WIDTH_PX = theme.GRID_PX * 62
RIGHT_CENTER_X_PX = theme.GRID_PX * 116
ENSO_CENTER_Y_PX = theme.GRID_PX * 36
CHIP_HEIGHT_PX = theme.GRID_PX * 5
READ_MIN_SCORE = 0.7


@dataclass(frozen=True)
class Item:
    label: str
    value: object
    note: str


@dataclass(frozen=True)
class Mode:
    name: str
    action: Action
    timed: bool
    songs: bool = False


MODES = (
    Mode("Learn", Action.START_LEARN, False),
    Mode("Recall", Action.START_RECALL, False),
    Mode("Rhythm", Action.START_RHYTHM, True),
    Mode("Music", Action.START_MUSIC, True, songs=True),
    Mode("Rush", Action.START_RUSH, True),
)


def deck_items():
    return [Item(deck.title, deck, f"{len(deck.words)} words" if not deck.ordered else "26 letters") for deck in DECKS]


def song_items(charts, track_lengths):
    return [Item(chart.title, chart, f"{chart.bpm:.0f} bpm   {DECKS_BY_NAME[chart.deck].title}")
            for chart in charts if chart.name in track_lengths]


def make_paper(size_px):
    """Warm paper with faint fibres and a soft vignette, made once."""
    rng = np.random.default_rng(7)
    paper = pygame.Surface(size_px, pygame.SRCALPHA)
    paper.fill(theme.PAPER_WASH)
    width, height = size_px
    for _ in range(900):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        angle, length = rng.uniform(0, math.pi), rng.uniform(4, 22)
        darker = int(rng.uniform(6, 16))
        fibre = (theme.PAPER[0] - darker, theme.PAPER[1] - darker, theme.PAPER[2] - darker, theme.PAPER_WASH[3])
        pygame.draw.line(paper, fibre, (x, y), (x + math.cos(angle) * length, y + math.sin(angle) * length))
    for step in range(24):
        pygame.draw.rect(paper, (120, 100, 80, 6), (-step * 4, -step * 4, width + step * 8, height + step * 8), 6)
    return paper


def draw_enso(surface, center, radius_px, width_px, seed=3):
    """A brushed circle: thick where the brush lands, thinning out, with the gap a real ensō leaves."""
    rng = np.random.default_rng(seed)
    start = -math.pi * 0.35
    sweep = math.pi * 1.86
    steps = 220
    wobble = rng.uniform(-1, 1, 6)
    for index in range(steps):
        t = index / steps
        angle = start + sweep * t
        r = radius_px * (1 + 0.025 * math.sin(angle * 3 + wobble[0]) + 0.015 * math.sin(angle * 5 + wobble[1]))
        thickness = width_px * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (1 - 0.5 * t)
        x, y = center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r
        alpha = int(230 * (1 - 0.45 * t))
        pygame.draw.circle(surface, (*theme.INK_BLACK, alpha), (x, y), max(1.0, thickness / 2))
        if rng.random() < 0.35 and t > 0.5:
            # Dry brush: bristles break up near the end of the stroke.
            pygame.draw.circle(surface, (*theme.PAPER, 160), (x + rng.uniform(-thickness, thickness) / 3,
                                                            y + rng.uniform(-thickness, thickness) / 3), thickness / 6)


def draw_brush_line(surface, left, y_px, width_px, color, seed):
    """A short ink stroke used to underline the chosen mode."""
    rng = np.random.default_rng(seed)
    for index in range(width_px):
        t = index / width_px
        thickness = 7 * (1 - 0.6 * t) + rng.uniform(-0.8, 0.8)
        pygame.draw.circle(surface, color, (left + index, y_px + math.sin(t * 2.4) * 2), max(1.0, thickness / 2))


def draw_seal(surface, center, size_px, font):
    """The red artist's seal, a little off-square."""
    rect = pygame.Rect(0, 0, size_px, size_px)
    rect.center = center
    pygame.draw.rect(surface, theme.SEAL, rect, border_radius=4)
    pygame.draw.rect(surface, theme.PAPER, rect.inflate(-8, -8), 2, border_radius=3)
    draw_text_centered(surface, font.render("ASL", True, theme.PAPER), rect.center)


class Chip:
    """A small paper button: ink outline, filled with ink when chosen."""

    def __init__(self, font, label, rect):
        self.rect = pygame.Rect(rect)
        self._on = font.render(label, True, theme.PAPER)
        self._off = font.render(label, True, theme.INK_BLACK)
        self._dim = font.render(label, True, theme.INK_FAINT)

    def draw(self, screen, chosen, enabled=True):
        hovered = enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if chosen and enabled:
            pygame.draw.rect(screen, theme.INK_BLACK, self.rect, border_radius=3)
            label = self._on
        else:
            if hovered:
                pygame.draw.rect(screen, theme.PAPER_SHADE, self.rect, border_radius=3)
            pygame.draw.rect(screen, theme.INK_SOFT if enabled else theme.INK_FAINT, self.rect, 1, border_radius=3)
            label = self._off if enabled else self._dim
        draw_text_centered(screen, label, self.rect.center)


def chip_row(font, labels, center_x, top_px, width_px):
    gap = theme.GRID_PX
    total = width_px * len(labels) + gap * (len(labels) - 1)
    left = center_x - total // 2
    return [Chip(font, label, (left + index * (width_px + gap), top_px, width_px, CHIP_HEIGHT_PX)) for index, label in enumerate(labels)]


def length_label(length_s):
    return f"{length_s // 60}:{length_s % 60:02d}"


class MenuScreen:
    def __init__(self, fonts, signs, charts, track_lengths, settings, records, size_px, sfx):
        self._signs = signs
        self._still = {name: sign for name, sign in signs.items() if name not in MOTION_SIGNS}
        self._records = records
        self._track_lengths = track_lengths
        self.lists = [song_items(charts, track_lengths) if mode.songs else deck_items() for mode in MODES]
        self.mode = 0
        self.selected = [0 for _ in MODES]
        self.first_row = [0 for _ in MODES]
        self.level = 0
        self.length_index = config.LENGTHS_S.index(config.DEFAULT_LENGTH_S)
        self._settings = settings
        self._sfx = sfx
        self._fonts = fonts
        self._size_px = size_px
        self._paper = make_paper(size_px)
        draw_enso(self._paper, (RIGHT_CENTER_X_PX, ENSO_CENTER_Y_PX), theme.ENSO_RADIUS_PX, theme.ENSO_WIDTH_PX)
        title = fonts.serif_title.render("ASLGAME", True, theme.INK_BLACK)
        self._paper.blit(title, title.get_rect(midleft=(LEFT_PX, TITLE_Y_PX)))
        draw_seal(self._paper, (LEFT_PX + title.get_width() + theme.GRID_PX * 5, TITLE_Y_PX), theme.GRID_PX * 7, fonts.small)
        self._mode_rects, self._mode_labels = [], []
        x_px = LEFT_PX
        for index, mode in enumerate(MODES):
            on = fonts.serif_mode.render(mode.name, True, theme.INK_BLACK)
            off = fonts.serif_mode.render(mode.name, True, theme.INK_FAINT)
            self._mode_labels.append((on, off))
            self._mode_rects.append(on.get_rect(midleft=(x_px, MODES_Y_PX)))
            x_px += on.get_width() + theme.GRID_PX * 5
        self._levels = chip_row(fonts.small, config.LEVEL_NAMES, RIGHT_CENTER_X_PX, ENSO_CENTER_Y_PX + theme.ENSO_RADIUS_PX + theme.GRID_PX * 3,
                                theme.GRID_PX * 13)
        self._lengths = chip_row(fonts.small, [length_label(s) for s in config.LENGTHS_S], RIGHT_CENTER_X_PX,
                                 self._levels[0].rect.bottom + theme.GRID_PX * 2, theme.GRID_PX * 9)
        self._start_rect = pygame.Rect(0, 0, theme.GRID_PX * 30, theme.GRID_PX * 7)
        self._start_rect.midtop = (RIGHT_CENTER_X_PX, self._lengths[0].rect.bottom + theme.GRID_PX * 2)
        self._start_label = fonts.serif_mode.render("Begin", True, theme.PAPER)
        self._help = HelpPanel(fonts, size_px)
        self._about = AboutPanel(fonts, size_px)
        self._settings_panel = SettingsPanel(fonts, settings, size_px)
        self._help_chip = Chip(fonts.body, "?", (size_px[0] - LEFT_PX - theme.GRID_PX * 6, TITLE_Y_PX - CHIP_HEIGHT_PX // 2, theme.GRID_PX * 6, CHIP_HEIGHT_PX))
        self._settings_chip = Chip(fonts.small, "Settings", (self._help_chip.rect.left - theme.GRID_PX * 15, self._help_chip.rect.top,
                                                            theme.GRID_PX * 14, CHIP_HEIGHT_PX))
        self._rows = {}
        self._reader_result = None
        self._read_letter = None
        self._read_score = 0.0
        self._read_surfaces = {}
        self._reader_font = pygame.font.SysFont(theme.SERIF_FAMILIES, theme.FONT_SIZE_DISPLAY_PX + 40)
        self._reader_hint = fonts.serif_body.render("sign any letter", True, theme.INK_FAINT)
        self._best_cache = {}

    # Selection

    def current(self):
        return MODES[self.mode]

    def items(self):
        return self.lists[self.mode]

    def selected_item(self):
        items = self.items()
        return items[self.selected[self.mode]] if items else None

    @property
    def length_s(self):
        return config.LENGTHS_S[self.length_index]

    def run_length_s(self):
        """The chosen length, or the whole song when the song is shorter."""
        item = self.selected_item()
        if self.current().songs and item is not None:
            return min(self.length_s, int(self._track_lengths[item.value.name] - config.MUSIC_END_MARGIN_S))
        return self.length_s

    def record_key(self):
        item = self.selected_item()
        name = item.value.name if item is not None else ""
        return record_key(self.current().name, name, config.LEVEL_NAMES[self.level], self.run_length_s() if self.current().timed else 0)

    def playable(self):
        item = self.selected_item()
        if item is None:
            return False
        if self.current().songs:
            return bool(pool(DECKS_BY_NAME[item.value.deck], self.level, self._signs))
        return bool(pool(item.value, self.level, self._signs))

    # Input

    def handle_event(self, event):
        before = self._ui_state()
        action = self._handle(event)
        if self._ui_state() != before:
            self._sfx.play("click")
        return action

    def _ui_state(self):
        return (self.mode, list(self.selected), self.level, self.length_index, self._help.visible, self._about.visible,
                self._settings_panel.visible, self._settings.finger_colors, self._settings.sound)

    def _handle(self, event):
        if self._settings_panel.handle_event(event):
            if self._settings_panel.wants_about:
                self._settings_panel.wants_about = False
                self._about.visible = True
            return None
        if self._help.handle_event(event) or self._about.handle_event(event):
            return None
        if clicked(event, self._settings_chip.rect):
            self._settings_panel.open()
        elif is_key(event, (pygame.K_ESCAPE,)):
            return Action.QUIT
        elif is_key(event, (pygame.K_h,)) or clicked(event, self._help_chip.rect):
            self._help.visible = True
        elif is_key(event, (pygame.K_LEFT,)):
            self.mode = (self.mode - 1) % len(MODES)
        elif is_key(event, (pygame.K_RIGHT,)):
            self.mode = (self.mode + 1) % len(MODES)
        elif is_key(event, (pygame.K_UP,)):
            self._step(-1)
        elif is_key(event, (pygame.K_DOWN,)):
            self._step(1)
        elif is_key(event, (pygame.K_1, pygame.K_2, pygame.K_3)):
            self.level = event.key - pygame.K_1
        elif is_key(event, (pygame.K_TAB,)):
            self.level = (self.level + 1) % len(config.LEVEL_NAMES)
        elif is_key(event, (pygame.K_l,)):
            self.length_index = (self.length_index + 1) % len(config.LENGTHS_S)
        elif is_key(event, (pygame.K_RETURN, pygame.K_SPACE)) or clicked(event, self._start_rect):
            return self._start_action()
        else:
            return self._handle_click(event)
        return None

    def _handle_click(self, event):
        for index, rect in enumerate(self._mode_rects):
            if clicked(event, rect.inflate(theme.GRID_PX * 2, theme.GRID_PX * 2)):
                self.mode = index
                return None
        for index, chip in enumerate(self._levels):
            if clicked(event, chip.rect):
                self.level = index
        if self.current().timed:
            for index, chip in enumerate(self._lengths):
                if clicked(event, chip.rect):
                    self.length_index = index
        if event.type == pygame.MOUSEWHEEL:
            last = max(0, len(self.items()) - MAX_ROWS)
            self.first_row[self.mode] = max(0, min(last, self.first_row[self.mode] - event.y))
            return None
        for index in self._visible_indexes():
            if clicked(event, self._row_rect(index)):
                if self.selected[self.mode] == index:
                    return self._start_action()
                self.selected[self.mode] = index
        return None

    def _start_action(self):
        return self.current().action if self.playable() else None

    def _step(self, direction):
        items = self.items()
        if not items:
            return
        index = (self.selected[self.mode] + direction) % len(items)
        self.selected[self.mode] = index
        first = self.first_row[self.mode]
        if index < first:
            self.first_row[self.mode] = index
        elif index >= first + MAX_ROWS:
            self.first_row[self.mode] = index - MAX_ROWS + 1

    def _visible_indexes(self):
        first = self.first_row[self.mode]
        return range(first, min(len(self.items()), first + MAX_ROWS))

    def _row_rect(self, index):
        top_px = LIST_TOP_PX + (index - self.first_row[self.mode]) * ROW_PX
        return pygame.Rect(LEFT_PX - theme.GRID_PX * 2, top_px, LIST_WIDTH_PX, ROW_PX)

    # Hand reader

    def update(self, now_s, result):
        """Reads the player's hand once per tracking result and shows the closest letter in the ensō."""
        if result is self._reader_result:
            return None
        self._reader_result = result
        hand = result.hand if result else None
        if hand is None:
            self._read_letter = None
            return None
        name, score = matcher.best_match(normalize(hand.points_px, hand.is_left), self._still)
        self._read_letter, self._read_score = (name, score) if score >= READ_MIN_SCORE else (None, score)
        return None

    # Drawing

    def _row_surface(self, item, selected):
        key = (id(item), selected)
        if key not in self._rows:
            row = pygame.Surface((LIST_WIDTH_PX, ROW_PX), pygame.SRCALPHA)
            if selected:
                draw_brush_line(row, theme.GRID_PX * 2, ROW_PX - theme.GRID_PX, theme.GRID_PX * 8, (*theme.SEAL, 255), id(item) % 97)
            font = self._fonts.serif_mode if selected else self._fonts.serif_body
            label = font.render(item.label, True, theme.INK_BLACK if selected else theme.INK_SOFT)
            row.blit(label, label.get_rect(midleft=(theme.GRID_PX * 2, ROW_PX // 2)))
            note = self._fonts.small.render(item.note, True, theme.INK_FAINT)
            row.blit(note, note.get_rect(midright=(LIST_WIDTH_PX - theme.GRID_PX * 2, ROW_PX // 2)))
            self._rows[key] = row
        return self._rows[key]

    def _best_surface(self):
        key = self.record_key()
        best = self._records.get(key)
        cache_key = (key, None if best is None else best["score"])
        if cache_key not in self._best_cache:
            text = "no best yet" if best is None else f"best  {best['score']:,}   {best['grade']}"
            self._best_cache[cache_key] = self._fonts.serif_body.render(text, True, theme.INK_SOFT)
        return self._best_cache[cache_key]

    def draw(self, screen, now_s, hand):
        screen.blit(self._paper, (0, 0))
        for index, rect in enumerate(self._mode_rects):
            on, off = self._mode_labels[index]
            screen.blit(on if index == self.mode else off, rect)
            if index == self.mode:
                draw_brush_line(screen, rect.left, rect.bottom + 2, rect.width, theme.SEAL, index)
        self._settings_chip.draw(screen, False)
        self._help_chip.draw(screen, False)
        mouse = pygame.mouse.get_pos()
        for index in self._visible_indexes():
            rect = self._row_rect(index)
            is_selected = index == self.selected[self.mode]
            if not is_selected and rect.collidepoint(mouse):
                pygame.draw.rect(screen, theme.PAPER_SHADE, rect, border_radius=3)
            screen.blit(self._row_surface(self.items()[index], is_selected), rect)
        self._draw_scroll_marks(screen)
        self._draw_reader(screen, now_s)
        for index, chip in enumerate(self._levels):
            chip.draw(screen, index == self.level)
        for index, chip in enumerate(self._lengths):
            chip.draw(screen, index == self.length_index, self.current().timed)
        playable = self.playable()
        hovered = self._start_rect.collidepoint(mouse)
        pygame.draw.rect(screen, theme.SEAL if playable else theme.INK_FAINT, self._start_rect, border_radius=4)
        if hovered and playable:
            pygame.draw.rect(screen, theme.INK_BLACK, self._start_rect, 2, border_radius=4)
        draw_text_centered(screen, self._start_label, self._start_rect.center)
        best = self._best_surface()
        draw_text_centered(screen, best, (RIGHT_CENTER_X_PX, self._start_rect.bottom + theme.GRID_PX * 2))
        self._help.draw(screen)
        self._about.draw(screen)
        self._settings_panel.draw(screen)

    def _draw_reader(self, screen, now_s):
        center = (RIGHT_CENTER_X_PX, ENSO_CENTER_Y_PX)
        if self._read_letter is None:
            draw_text_centered(screen, self._reader_hint, center)
            return
        if self._read_letter not in self._read_surfaces:
            self._read_surfaces[self._read_letter] = self._reader_font.render(self._read_letter, True, theme.INK_BLACK)
        draw_text_centered(screen, self._read_surfaces[self._read_letter], center)

    def _draw_scroll_marks(self, screen):
        first = self.first_row[self.mode]
        x_px = LEFT_PX + LIST_WIDTH_PX - theme.GRID_PX * 3
        size_px = theme.GRID_PX
        if first > 0:
            y_px = LIST_TOP_PX - theme.GRID_PX
            pygame.draw.polygon(screen, theme.INK_FAINT, [(x_px - size_px, y_px), (x_px + size_px, y_px), (x_px, y_px - size_px)])
        if first + MAX_ROWS < len(self.items()):
            y_px = LIST_TOP_PX + MAX_ROWS * ROW_PX + theme.GRID_PX
            pygame.draw.polygon(screen, theme.INK_FAINT, [(x_px - size_px, y_px), (x_px + size_px, y_px), (x_px, y_px + size_px)])
