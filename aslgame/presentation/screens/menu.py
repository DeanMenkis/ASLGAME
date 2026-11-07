"""Menu: pick a mode and a word or song, by keyboard or mouse."""

from dataclasses import dataclass

import pygame

from aslgame import config, theme
from aslgame.game.app_flow import Action
from aslgame.game.sign_queue import missing_signs
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import is_key, make_shade
from aslgame.presentation.screens.help import HelpPanel
from aslgame.presentation.ui import Button, Toggle, button_width, clicked, make_panel, toggle_width

TAB_TOP_PX = theme.TOP_BAR_HEIGHT_PX + theme.GRID_PX * 2
CARD_TOP_PX = TAB_TOP_PX + theme.BUTTON_HEIGHT_PX + theme.GRID_PX * 3
MAX_ROWS = 7


@dataclass(frozen=True)
class Item:
    label: str
    value: object
    note: str  # why it cannot be played, or empty
    playable: bool


@dataclass(frozen=True)
class Mode:
    name: str
    action: Action
    items: list


def word_items(sign_names):
    # Every recorded letter in order, as untimed practice.
    alphabet = "".join(sorted(sign_names))
    items = [Item(config.ALPHABET_LABEL, alphabet, "", bool(alphabet))]
    for word in config.LEARN_WORDS:
        missing = missing_signs(word, sign_names)
        items.append(Item(word, word, "Needs " + " ".join(missing) if missing else "", not missing))
    return items


def chart_items(charts, sign_names, track_names):
    items = []
    for chart in charts:
        missing = missing_signs(chart.text, sign_names)
        note = "Needs " + " ".join(missing) if missing else ("" if chart.name in track_names else "Audio missing")
        items.append(Item(chart.title, chart, note, not note))
    return items


class MenuScreen:
    def __init__(self, fonts, sign_names, charts, track_names, settings, size_px, sfx):
        words = word_items(sign_names)
        self.modes = [
            Mode("Learn", Action.START_LEARN, words),
            Mode("Rhythm", Action.START_RHYTHM, words),
            Mode("Music", Action.START_MUSIC, chart_items(charts, sign_names, track_names)),
        ]
        self.mode = 0
        self.selected = [next((i for i, item in enumerate(m.items) if item.playable), None) for m in self.modes]
        self._settings = settings
        self._sfx = sfx
        self._fonts = fonts
        self._size_px = size_px
        self._shade = make_shade(size_px)
        self._top_bar = make_panel((size_px[0], theme.TOP_BAR_HEIGHT_PX), theme.SURFACE, 0)
        self._wordmark = fonts.large.render("ASLGAME", True, theme.INK)
        self._help = HelpPanel(fonts, size_px)
        help_rect = pygame.Rect(0, 0, theme.ICON_BUTTON_PX, theme.ICON_BUTTON_PX)
        help_rect.midright = (size_px[0] - theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2)
        self._help_button = Button(fonts.medium, "?", help_rect)
        self._toggles = self._make_toggles(fonts, help_rect)
        self._tabs = self._make_tabs(fonts, size_px)
        self._rows = {}  # (mode, index, selected) -> rendered row, built on first draw
        self._card_rect = pygame.Rect(0, CARD_TOP_PX, theme.CARD_WIDTH_PX, theme.ROW_HEIGHT_PX * MAX_ROWS + theme.GRID_PX * 2)
        self._card_rect.centerx = size_px[0] // 2
        self._card = make_panel(self._card_rect.size)
        start_rect = pygame.Rect(0, 0, theme.GRID_PX * 28, theme.BUTTON_HEIGHT_PX)
        start_rect.midtop = (size_px[0] // 2, self._card_rect.bottom + theme.GRID_PX * 3)
        self._start = Button(fonts.body, "Start", start_rect, primary=True)

    def _make_toggles(self, fonts, help_rect):
        """Settings toggles in the header, right-aligned before the ? button."""
        toggles = []
        right_px = help_rect.left - theme.GRID_PX * 2
        for name, label in (("sound", "Sound"), ("finger_colors", "Finger colors")):
            width_px = toggle_width(fonts.small, label)
            rect = pygame.Rect(right_px - width_px, 0, width_px, theme.ICON_BUTTON_PX)
            rect.centery = help_rect.centery
            toggles.append((name, Toggle(fonts.small, label, rect)))
            right_px = rect.left - theme.GRID_PX * 2
        return toggles

    def _make_tabs(self, fonts, size_px):
        widths = [button_width(fonts.body, mode.name) + theme.GRID_PX * 4 for mode in self.modes]
        x_px = (size_px[0] - sum(widths) - theme.GRID_PX * 2 * (len(widths) - 1)) // 2
        tabs = []
        for mode, width_px in zip(self.modes, widths):
            tabs.append(Button(fonts.body, mode.name, (x_px, TAB_TOP_PX, width_px, theme.BUTTON_HEIGHT_PX)))
            x_px += width_px + theme.GRID_PX * 2
        self._active_tabs = [Button(fonts.body, mode.name, tab.rect, primary=True) for mode, tab in zip(self.modes, tabs)]
        return tabs

    def current(self):
        return self.modes[self.mode]

    def selected_item(self):
        index = self.selected[self.mode]
        return None if index is None else self.current().items[index]

    def handle_event(self, event):
        before = (self.mode, list(self.selected), self._help.visible)
        action = self._handle(event)
        if (self.mode, self.selected, self._help.visible) != before:
            self._sfx.play("click")
        return action

    def _handle(self, event):
        if self._help.handle_event(event):
            return None
        if is_key(event, (pygame.K_ESCAPE,)):
            return Action.QUIT
        for name, toggle in self._toggles:
            if toggle.is_clicked(event):
                setattr(self._settings, name, not getattr(self._settings, name))
                return None
        if is_key(event, (pygame.K_h,)) or self._help_button.is_clicked(event):
            self._help.visible = True
        elif is_key(event, (pygame.K_LEFT,)):
            self.mode = (self.mode - 1) % len(self.modes)
        elif is_key(event, (pygame.K_RIGHT,)):
            self.mode = (self.mode + 1) % len(self.modes)
        elif is_key(event, (pygame.K_UP,)):
            self._step(-1)
        elif is_key(event, (pygame.K_DOWN,)):
            self._step(1)
        elif is_key(event, (pygame.K_RETURN, pygame.K_SPACE)) or self._start.is_clicked(event):
            return self._start_action()
        else:
            return self._handle_click(event)
        return None

    def _handle_click(self, event):
        for index, tab in enumerate(self._tabs):
            if tab.is_clicked(event):
                self.mode = index
                return None
        for index in range(len(self.current().items)):
            if clicked(event, self._row_rect(index)) and self.current().items[index].playable:
                # A second click on the selected row starts it.
                if self.selected[self.mode] == index:
                    return self._start_action()
                self.selected[self.mode] = index
        return None

    def _start_action(self):
        item = self.selected_item()
        return self.current().action if item is not None and item.playable else None

    def _step(self, direction):
        items = self.current().items
        index = self.selected[self.mode]
        if index is None:
            return
        for _ in items:
            index = (index + direction) % len(items)
            if items[index].playable:
                self.selected[self.mode] = index
                return

    def _row_rect(self, index):
        top_px = self._card_rect.top + theme.GRID_PX + index * theme.ROW_HEIGHT_PX
        return pygame.Rect(self._card_rect.left + theme.GRID_PX, top_px, self._card_rect.width - theme.GRID_PX * 2, theme.ROW_HEIGHT_PX)

    def _row_surface(self, item, selected):
        key = (id(item), selected)
        if key not in self._rows:
            # Rendered once per row and state, then reused.
            rect = self._row_rect(0)
            row = pygame.Surface(rect.size, pygame.SRCALPHA)
            if selected:
                pygame.draw.rect(row, theme.SURFACE_RAISED, row.get_rect(), border_radius=theme.CORNER_PX)
                pygame.draw.rect(row, theme.ACCENT, (0, theme.GRID_PX * 2, theme.MENU_MARKER_PX, rect.height - theme.GRID_PX * 4),
                                 border_radius=theme.GRID_PX // 2)
            font = self._fonts.medium if selected else self._fonts.body
            color = theme.INK if item.playable else theme.DISABLED
            label = font.render(item.label, True, color)
            row.blit(label, label.get_rect(midleft=(theme.GRID_PX * 4, rect.height // 2)))
            if item.note:
                note = self._fonts.small.render(item.note, True, theme.INK_DIM)
                row.blit(note, note.get_rect(midright=(rect.width - theme.GRID_PX * 3, rect.height // 2)))
            self._rows[key] = row
        return self._rows[key]

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        screen.blit(self._top_bar, (0, 0))
        screen.blit(self._wordmark, self._wordmark.get_rect(midleft=(theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2)))
        self._help_button.draw(screen)
        for name, toggle in self._toggles:
            toggle.draw(screen, getattr(self._settings, name))
        for index, tab in enumerate(self._tabs):
            (self._active_tabs[index] if index == self.mode else tab).draw(screen)
        screen.blit(self._card, self._card_rect)
        mouse = pygame.mouse.get_pos()
        for index, item in enumerate(self.current().items[:MAX_ROWS]):
            rect = self._row_rect(index)
            if index != self.selected[self.mode] and item.playable and rect.collidepoint(mouse):
                pygame.draw.rect(screen, theme.SURFACE_HOVER, rect, border_radius=theme.CORNER_PX)
            screen.blit(self._row_surface(item, index == self.selected[self.mode]), rect)
        self._start.enabled = self.selected_item() is not None and self.selected_item().playable
        self._start.draw(screen)
        self._help.draw(screen)

