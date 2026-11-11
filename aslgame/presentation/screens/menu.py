"""Menu: a poster. Pick a mode, a deck or song, a level, and a length. The proof at the right is the camera, printed live;
sign at it and the letter it reads is set beside it."""

import math
from dataclasses import dataclass

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.game.app_flow import Action
from aslgame.game.motion import MOTION_SIGNS
from aslgame.game import mastery
from aslgame.game.mastery import Mastery
from aslgame.game.words import ALPHABET, DECKS, DECKS_BY_NAME, pool
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation import press
from aslgame.presentation.screens.about import AboutPanel
from aslgame.presentation.screens.common import is_key
from aslgame.presentation.screens.help import HelpPanel
from aslgame.presentation.screens.settings import SettingsPanel
from aslgame.presentation.ui import Button, clicked
from aslgame.records import record_key

LEFT_PX = theme.MARGIN_PX * 2
TITLE_Y_PX = theme.GRID_PX * 9
MODES_Y_PX = theme.GRID_PX * 20
LIST_TOP_PX = theme.GRID_PX * 27
ROW_PX = theme.GRID_PX * 7
MAX_ROWS = 8
LIST_WIDTH_PX = theme.GRID_PX * 62
RIGHT_CENTER_X_PX = theme.GRID_PX * 116
# The proof: the camera at 16:9 inside a paper frame with trim marks.
PROOF_PICTURE_PX = (theme.GRID_PX * 54, theme.GRID_PX * 54 * 9 // 16)
PROOF_FRAME_PX = theme.GRID_PX
PROOF_TOP_PX = theme.GRID_PX * 14
READ_RADIUS_PX = theme.GRID_PX * 8
CHIP_HEIGHT_PX = theme.GRID_PX * 5
READ_MIN_SCORE = 0.7
ALPHABET_CELL_PX = (20, 28)
ALPHABET_STEP_PX = 22
ALPHABET_FONT_PX = 22
PRACTISE_NOTE_LETTERS = 6
# Three discs of ink behind everything: (ink, radius, center, drift radius, drift speed). They slide over each other slowly.
DISCS = (
    (theme.YELLOW, 300, (1190, 70), 26, 0.23),
    (theme.tint(theme.BLUE, 0.45), 150, (-20, 790), 18, 0.31),
    (theme.tint(theme.RED, 0.7), 150, (1300, 300), 24, 0.17),
)


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


def deck_note(deck, letters):
    if deck.ordered:
        return "26 letters"
    if not deck.by_need:
        return f"{len(deck.words)} words"
    # The Practise deck names the letters it will deal, weakest first.
    weak = mastery.weak_letters(letters)[:PRACTISE_NOTE_LETTERS]
    return "  ".join(weak) if weak else f"{mastery.known_count(letters)} of {len(ALPHABET)} known"


def deck_items(letters):
    return [Item(deck.title, deck, deck_note(deck, letters)) for deck in DECKS]


def make_alphabet(font, letters):
    """The alphabet as a case of type: a blue block is a known letter, an outlined one with a red dot is weak,
    and a faint one has not been tested yet."""
    width_px, height_px = ALPHABET_CELL_PX
    row = pygame.Surface((ALPHABET_STEP_PX * len(ALPHABET), height_px + 10), pygame.SRCALPHA)
    for index, letter in enumerate(ALPHABET):
        state = mastery.state(letters, letter)
        cell = pygame.Rect(index * ALPHABET_STEP_PX + (ALPHABET_STEP_PX - width_px) // 2, 0, width_px, height_px)
        if state == Mastery.KNOWN:
            pygame.draw.rect(row, theme.BLUE, cell, border_radius=2)
            label = font.render(letter, True, theme.PAPER)
        else:
            pygame.draw.rect(row, theme.PAPER, cell, border_radius=2)
            pygame.draw.rect(row, theme.BLUE if state == Mastery.WEAK else theme.BLUE_FAINT, cell, 2, border_radius=2)
            label = font.render(letter, True, theme.BLUE if state == Mastery.WEAK else theme.BLUE_FAINT)
        row.blit(label, label.get_rect(center=(cell.centerx, cell.centery + 2)))
        if state == Mastery.WEAK:
            pygame.draw.circle(row, theme.RED, (cell.centerx, height_px + 6), 3)
    return row


def song_items(charts, track_lengths):
    return [Item(chart.title, chart, f"{chart.bpm:.0f} bpm   {DECKS_BY_NAME[chart.deck].title}")
            for chart in charts if chart.name in track_lengths]


def make_paper(size_px):
    """Uncoated paper with faint fibres, made once."""
    rng = np.random.default_rng(7)
    sheet = pygame.Surface(size_px)
    sheet.fill(theme.PAPER)
    width, height = size_px
    for _ in range(900):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        angle, length = rng.uniform(0, math.pi), rng.uniform(4, 22)
        darker = int(rng.uniform(4, 12))
        fibre = tuple(channel - darker for channel in theme.PAPER)
        pygame.draw.line(sheet, fibre, (x, y), (x + math.cos(angle) * length, y + math.sin(angle) * length))
    return sheet


class Chip:
    """A small paper button: blue outline, filled with blue when chosen."""

    def __init__(self, font, label, rect):
        self.rect = pygame.Rect(rect)
        self._on = font.render(label, True, theme.PAPER)
        self._off = font.render(label, True, theme.BLUE)
        self._dim = font.render(label, True, theme.BLUE_FAINT)

    def draw(self, screen, chosen, enabled=True):
        hovered = enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if chosen and enabled:
            pygame.draw.rect(screen, theme.BLUE, self.rect, border_radius=3)
            label = self._on
        else:
            pygame.draw.rect(screen, theme.PAPER_SHADE if hovered else theme.PAPER, self.rect, border_radius=3)
            pygame.draw.rect(screen, theme.BLUE if enabled else theme.BLUE_FAINT, self.rect, 2, border_radius=3)
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
    def __init__(self, fonts, signs, charts, track_lengths, settings, records, letters, size_px, sfx):
        self._signs = signs
        self._still = {name: sign for name, sign in signs.items() if name not in MOTION_SIGNS}
        self._records = records
        self._track_lengths = track_lengths
        self._letters = letters
        self._songs = song_items(charts, track_lengths)
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
        self._discs = [press.disc(radius, ink) for ink, radius, _, _, _ in DISCS]
        self._title = press.overprint_text(fonts.slab_title, "ASLGAME", theme.BLUE, theme.RED, (6, 6))
        self._title_rect = self._title.get_rect(midleft=(LEFT_PX, TITLE_Y_PX))
        mode_font = pygame.font.SysFont(theme.LABEL_FAMILIES, 40, bold=True)
        self._mode_rects, self._mode_labels = [], []
        x_px = LEFT_PX
        for index, mode in enumerate(MODES):
            on = mode_font.render(mode.name.upper(), True, theme.BLUE)
            off = mode_font.render(mode.name.upper(), True, theme.BLUE_FAINT)
            self._mode_labels.append((on, off))
            self._mode_rects.append(on.get_rect(midleft=(x_px, MODES_Y_PX)))
            x_px += on.get_width() + theme.GRID_PX * 4
        picture_w, picture_h = PROOF_PICTURE_PX
        self._picture = pygame.Surface(PROOF_PICTURE_PX)
        self._picture_rect = pygame.Rect(0, PROOF_TOP_PX + PROOF_FRAME_PX, picture_w, picture_h)
        self._picture_rect.centerx = RIGHT_CENTER_X_PX
        self._proof = press.sticker((picture_w + PROOF_FRAME_PX * 2, picture_h + PROOF_FRAME_PX * 2))
        self._read_disc = press.starburst(READ_RADIUS_PX, 16, theme.YELLOW, 0.86, theme.BLUE)
        self._read_center = (self._picture_rect.right - theme.GRID_PX * 2, self._picture_rect.bottom - theme.GRID_PX * 2)
        self._levels = chip_row(fonts.small, config.LEVEL_NAMES, RIGHT_CENTER_X_PX, self._picture_rect.bottom + theme.GRID_PX * 5,
                                theme.GRID_PX * 13)
        self._lengths = chip_row(fonts.small, [length_label(s) for s in config.LENGTHS_S], RIGHT_CENTER_X_PX,
                                 self._levels[0].rect.bottom + theme.GRID_PX, theme.GRID_PX * 9)
        self._start = Button(fonts.slab_mode, "BEGIN", (0, 0, theme.GRID_PX * 30, theme.GRID_PX * 8), primary=True)
        self._start.rect.midtop = (RIGHT_CENTER_X_PX, self._lengths[0].rect.bottom + theme.GRID_PX * 2)
        self._start_rect = self._start.rect
        self._help = HelpPanel(fonts, size_px)
        self._about = AboutPanel(fonts, size_px)
        self._settings_panel = SettingsPanel(fonts, settings, size_px)
        self._help_chip = Chip(fonts.body, "?", (size_px[0] - LEFT_PX - theme.GRID_PX * 6, TITLE_Y_PX - CHIP_HEIGHT_PX // 2, theme.GRID_PX * 6, CHIP_HEIGHT_PX))
        self._settings_chip = Chip(fonts.small, "Settings", (self._help_chip.rect.left - theme.GRID_PX * 15, self._help_chip.rect.top,
                                                            theme.GRID_PX * 14, CHIP_HEIGHT_PX))
        self._reader_result = None
        self._read_letter = None
        self._read_score = 0.0
        self._read_surfaces = {}
        self._reader_font = pygame.font.SysFont(theme.SLAB_FAMILIES, 96, bold=True)
        self._best_cache = {}
        self._alphabet_font = pygame.font.SysFont(theme.LABEL_FAMILIES, ALPHABET_FONT_PX, bold=True)
        self._row_font = pygame.font.SysFont(theme.SLAB_FAMILIES, 32, bold=True)
        self.refresh()

    def refresh(self):
        """Called after every run: letter mastery has changed, so the Practise note and the alphabet are redrawn."""
        decks = deck_items(self._letters)
        self.lists = [self._songs if mode.songs else decks for mode in MODES]
        self._rows = {}
        self._alphabet = make_alphabet(self._alphabet_font, self._letters)

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
        """Reads the player's hand once per tracking result and sets the closest letter on the proof."""
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
        """The chosen row is a solid blue block with its name reversed out in paper; the others are plain type."""
        key = (id(item), selected)
        if key not in self._rows:
            row = pygame.Surface((LIST_WIDTH_PX, ROW_PX), pygame.SRCALPHA)
            if selected:
                block = pygame.Rect(0, 3, LIST_WIDTH_PX - theme.SHADOW_PX, ROW_PX - 6 - theme.SHADOW_PX)
                pygame.draw.rect(row, theme.RED, block.move(theme.SHADOW_PX, theme.SHADOW_PX), border_radius=3)
                pygame.draw.rect(row, theme.BLUE, block, border_radius=3)
            font = self._row_font if selected else self._fonts.slab_body
            label = font.render(item.label, True, theme.PAPER if selected else theme.BLUE)
            note = self._fonts.small.render(item.note, True, theme.PAPER if selected else theme.BLUE_SOFT)
            # A long selected name shrinks to fit beside its note instead of running into it.
            room_px = LIST_WIDTH_PX - note.get_width() - theme.GRID_PX * 7
            if label.get_width() > room_px:
                scale = room_px / label.get_width()
                label = pygame.transform.smoothscale(label, (room_px, int(label.get_height() * scale)))
            center_y = ROW_PX // 2 - (theme.SHADOW_PX // 2 if selected else 0)
            row.blit(label, label.get_rect(midleft=(theme.GRID_PX * 2, center_y)))
            row.blit(note, note.get_rect(midright=(LIST_WIDTH_PX - theme.GRID_PX * 3, center_y)))
            self._rows[key] = row
        return self._rows[key]

    def _best_surface(self):
        key = self.record_key()
        best = self._records.get(key)
        cache_key = (key, None if best is None else best["score"])
        if cache_key not in self._best_cache:
            text = "NO BEST YET" if best is None else f"BEST  {best['score']:,}   {best['grade']}"
            self._best_cache[cache_key] = self._fonts.label.render(text, True, theme.BLUE)
        return self._best_cache[cache_key]

    def draw(self, screen, now_s, hand):
        # The camera is already on the screen; take the proof's picture from it before the paper covers it.
        pygame.transform.smoothscale(screen, PROOF_PICTURE_PX, self._picture)
        screen.blit(self._paper, (0, 0))
        self._draw_discs(screen, now_s)
        screen.blit(self._title, self._title_rect)
        press.draw_registration(screen, (self._title_rect.right + theme.GRID_PX * 5, TITLE_Y_PX), theme.GRID_PX * 2, theme.RED)
        for index, rect in enumerate(self._mode_rects):
            on, off = self._mode_labels[index]
            screen.blit(on if index == self.mode else off, rect)
            if index == self.mode:
                press.underline(screen, rect.left, rect.bottom - 4, rect.width)
        self._settings_chip.draw(screen, False)
        self._help_chip.draw(screen, False)
        mouse = pygame.mouse.get_pos()
        for index in self._visible_indexes():
            rect = self._row_rect(index)
            is_selected = index == self.selected[self.mode]
            if not is_selected and rect.collidepoint(mouse):
                pygame.draw.rect(screen, theme.PAPER_SHADE, rect.inflate(0, -6), border_radius=3)
            screen.blit(self._row_surface(self.items()[index], is_selected), rect)
        self._draw_scroll_marks(screen)
        self._draw_proof(screen)
        for index, chip in enumerate(self._levels):
            chip.draw(screen, index == self.level)
        for index, chip in enumerate(self._lengths):
            chip.draw(screen, index == self.length_index, self.current().timed)
        self._start.enabled = self.playable()
        self._start.draw(screen)
        best = self._best_surface()
        draw_text_centered(screen, best, (RIGHT_CENTER_X_PX, self._start_rect.bottom + theme.GRID_PX * 3 + 2))
        screen.blit(self._alphabet, self._alphabet.get_rect(midtop=(RIGHT_CENTER_X_PX, self._start_rect.bottom + theme.GRID_PX * 6)))
        self._help.draw(screen)
        self._about.draw(screen)
        self._settings_panel.draw(screen)

    def _draw_discs(self, screen, now_s):
        """Flat discs of ink that drift a little, so the inks slide across each other where they overlap."""
        moving = self._settings.motion
        for surface, (_, radius, (x, y), reach, speed) in zip(self._discs, DISCS):
            angle = now_s * speed * 2 * math.pi if moving else 0.0
            at = (x + math.cos(angle) * reach - radius, y + math.sin(angle * 0.7) * reach - radius)
            screen.blit(surface, at, special_flags=pygame.BLEND_RGB_MULT)

    def _draw_proof(self, screen):
        """The camera, printed, in a paper frame with trim marks; the letter it reads is set on a star at its corner."""
        frame = self._picture_rect.inflate(PROOF_FRAME_PX * 2, PROOF_FRAME_PX * 2)
        screen.blit(self._proof, frame)
        screen.blit(self._picture, self._picture_rect)
        press.draw_crop_marks(screen, frame.inflate(theme.SHADOW_PX, theme.SHADOW_PX).move(theme.SHADOW_PX // 2, theme.SHADOW_PX // 2),
                              theme.BLUE)
        if self._read_letter is None:
            return
        if self._read_letter not in self._read_surfaces:
            self._read_surfaces[self._read_letter] = self._reader_font.render(self._read_letter, True, theme.BLUE)
        screen.blit(self._read_disc, self._read_disc.get_rect(center=self._read_center))
        draw_text_centered(screen, self._read_surfaces[self._read_letter], self._read_center)

    def _draw_scroll_marks(self, screen):
        first = self.first_row[self.mode]
        x_px = LEFT_PX + LIST_WIDTH_PX - theme.GRID_PX * 3
        size_px = theme.GRID_PX
        if first > 0:
            y_px = LIST_TOP_PX - theme.GRID_PX
            pygame.draw.polygon(screen, theme.BLUE, [(x_px - size_px, y_px), (x_px + size_px, y_px), (x_px, y_px - size_px)])
        if first + MAX_ROWS < len(self.items()):
            y_px = LIST_TOP_PX + MAX_ROWS * ROW_PX + theme.GRID_PX
            pygame.draw.polygon(screen, theme.BLUE, [(x_px - size_px, y_px), (x_px + size_px, y_px), (x_px, y_px + size_px)])
