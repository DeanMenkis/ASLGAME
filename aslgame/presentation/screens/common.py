"""Helpers shared by the screens: scoring the target, the ghost, the reference card, and the top bar."""

import pygame

from aslgame import config, theme
from aslgame.game.motion import MOTION_SIGNS, MotionState, MotionTracker
from aslgame.game.motion import update as motion_update
from aslgame.game.scoring import Judgement
from aslgame.hand import FINGERS, WRIST
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, palm_size
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.hand_shape import GhostRenderer, draw_finger_fixes
from aslgame.presentation.press import band, line_hand, sticker
from aslgame.presentation.motion_path import draw_guide, draw_trail, guide_points
from aslgame.presentation.ui import clicked, make_panel

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_SPACE)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
JUDGEMENT_TEXT = {Judgement.PERFECT: "Perfect", Judgement.GOOD: "Good", Judgement.OK: "OK", Judgement.MISS: "Miss"}
CARD_TOPLEFT_PX = (theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX + theme.GRID_PX * 2)
# A small hand drawing may grow this much to fill the card, never more, so strokes stay crisp.
CARD_MAX_ZOOM = 1.4


def is_key(event, keys):
    return event.type == pygame.KEYDOWN and event.key in keys


def make_shade(size_px):
    return make_panel(size_px, theme.SHADE, 0)


def idle_wrist(size_px):
    """Where the ghost's wrist sits when no hand is seen."""
    return (size_px[0] / 2 + theme.IDLE_GHOST_OFFSET_PX[0], size_px[1] / 2 + theme.IDLE_GHOST_OFFSET_PX[1])


class TargetScorer:
    """Scores the live hand against a target once per tracking result, and finds the fingers to fix.

    Motion signs (J, Z) pass only once their path has been drawn with the right fingers straight.
    """

    def __init__(self, signs):
        self._signs = signs
        # Motion letters are told apart by their path, so they never count as look-alikes of still letters.
        self._still_signs = {name: sign for name, sign in signs.items() if name not in MOTION_SIGNS}
        self._result = None
        self._target = None
        self.score = 0.0
        self.fingers_off = []
        self.shape_ok = False
        self.tracker = None
        self.trail_px = []

    def update(self, result, target_name):
        if result is self._result and target_name == self._target:
            return self.score
        if target_name != self._target:
            motion = MOTION_SIGNS.get(target_name)
            self.tracker = MotionTracker(motion) if motion else None
            self.trail_px = []
        self._result, self._target = result, target_name
        hand = result.hand if result else None
        if hand is None:
            self.score, self.fingers_off, self.shape_ok = 0.0, [], False
            if self.tracker is not None:
                motion_update(self.tracker, 0.0, False, None, 1.0, False)
                self.trail_px = []
            return self.score
        normalized = normalize(hand.points_px, hand.is_left)
        if self.tracker is not None:
            return self._update_motion(result, hand, normalized)
        target = self._signs[target_name]
        self.score = matcher.target_score(normalized, target, self._still_signs)
        self.shape_ok = self.score >= config.MATCH_THRESHOLD
        self.fingers_off = [] if self.shape_ok else matcher.fingers_off(normalized, target)
        return self.score

    def _update_motion(self, result, hand, normalized):
        motion = self.tracker.motion
        straight = matcher.extended_fingers(normalized)
        self.shape_ok = straight == motion.extended
        self.fingers_off = sorted(straight ^ motion.extended, key=list(FINGERS).index)
        tip_px = hand.points_px[motion.tip, :2]
        state = motion_update(self.tracker, result.captured_s, self.shape_ok, tip_px, palm_size(hand.points_px), hand.is_left)
        if state == MotionState.DRAWING:
            self.trail_px = (self.trail_px + [tuple(tip_px.tolist())])[-config.TRAIL_POINTS:]
        elif state != MotionState.DONE:
            self.trail_px = []
        self.score = 1.0 if state == MotionState.DONE else 0.0
        return self.score


class Ghost:
    """The target sign drawn as a silhouette over the live hand, or in the middle when no hand is seen."""

    def __init__(self, size_px, settings):
        self._renderer = GhostRenderer()
        self._idle_wrist = idle_wrist(size_px)
        self._settings = settings

    def draw(self, screen, sign, hand, matched, fingers_off):
        colors = self._settings.finger_colors
        if hand is None:
            self._renderer.draw(screen, sign, self._idle_wrist, theme.IDLE_GHOST_PALM_PX, False, False, colors)
            return
        wrist = hand.points_px[WRIST, :2].tolist()
        self._renderer.draw(screen, sign, wrist, palm_size(hand.points_px), hand.is_left, matched, colors)
        if fingers_off:
            # Marked on the player's own fingers; the ghost already shows where they should go.
            draw_finger_fixes(screen, hand.points_px, fingers_off)


class ReferenceCard:
    """A paper card with the target letter in wood type and its handshape drawn in blue, still while the hand moves."""

    def __init__(self, fonts, signs, names, settings):
        # Cards are built the first time each is shown (about a millisecond), so long words start without a pause.
        self._signs = signs
        self._cards = {}
        self._settings = settings
        self._letter_font = pygame.font.SysFont(theme.SLAB_FAMILIES, theme.CARD_LETTER_PX, bold=True)
        self._recall_font = pygame.font.SysFont(theme.SLAB_FAMILIES, theme.FONT_SIZE_DISPLAY_PX, bold=True)

    def _build_letter(self, name):
        """Recall mode: only the letter, large, with no picture of the shape."""
        card = sticker(theme.REFERENCE_CARD_SIZE_PX)
        width_px, height_px = theme.REFERENCE_CARD_SIZE_PX
        letter = self._recall_font.render(name, True, theme.BLUE)
        draw_text_centered(card, letter, (width_px // 2, height_px // 2))
        return card

    def _build(self, sign, finger_colors):
        card = sticker(theme.REFERENCE_CARD_SIZE_PX)
        width_px, height_px = theme.REFERENCE_CARD_SIZE_PX
        draw_text_centered(card, self._letter_font.render(sign.name, True, theme.BLUE), (width_px // 2, theme.GRID_PX * 5))
        rule_y = theme.GRID_PX * 10
        pygame.draw.line(card, theme.RED, (width_px // 2 - theme.GRID_PX * 3, rule_y), (width_px // 2 + theme.GRID_PX * 3, rule_y), 3)
        tints = theme.FINGER_TINTS if finger_colors else None
        drawing, wrist = line_hand(sign.outline, theme.REFERENCE_PALM_PX, theme.BLUE, tints)
        # Cropped to the drawn hand and fitted to the space under the rule, so every letter sits centred and whole,
        # sideways ones (G, H, P, Q) included.
        bounds = drawing.get_bounding_rect()
        drawing = drawing.subsurface(bounds)
        box = pygame.Rect(theme.GRID_PX * 2, theme.GRID_PX * 12, width_px - theme.GRID_PX * 4, height_px - theme.GRID_PX * 16)
        scale = min(box.width / bounds.width, box.height / bounds.height, CARD_MAX_ZOOM)
        drawing = pygame.transform.smoothscale(drawing, (round(bounds.width * scale), round(bounds.height * scale)))
        rect = card.blit(drawing, drawing.get_rect(center=box.center))
        motion = MOTION_SIGNS.get(sign.name)
        if motion is not None:
            tip = sign.outline[motion.tip, :2] * theme.REFERENCE_PALM_PX
            start = (rect.left + (wrist[0] + tip[0] - bounds.left) * scale, rect.top + (wrist[1] + tip[1] - bounds.top) * scale)
            draw_guide(card, guide_points(motion, start, theme.REFERENCE_PALM_PX * theme.CARD_PATH_SCALE * scale, False))
        return card

    def draw(self, screen, name, progress=None, letter_only=False):
        """progress, from 0 to 1, draws a red line along the inside of the card's lower edge."""
        key = (name, "letter" if letter_only else self._settings.finger_colors)
        if key not in self._cards:
            self._cards[key] = self._build_letter(name) if letter_only else self._build(self._signs[name], key[1])
        screen.blit(self._cards[key], CARD_TOPLEFT_PX)
        if progress:
            width_px, height_px = theme.REFERENCE_CARD_SIZE_PX
            left_px = CARD_TOPLEFT_PX[0] + theme.GRID_PX * 2
            y_px = CARD_TOPLEFT_PX[1] + height_px - theme.GRID_PX * 2
            length_px = width_px - theme.GRID_PX * 4
            pygame.draw.line(screen, theme.PAPER_SHADE, (left_px, y_px), (left_px + length_px, y_px), 6)
            end_px = left_px + int(length_px * min(1.0, progress))
            pygame.draw.line(screen, theme.RED, (left_px, y_px), (end_px, y_px), 6)


class TopBar:
    """A paper band along the top of play screens, its lower edge breaking into dots, with a pause button at the right."""

    def __init__(self, size_px):
        self._panel = band((size_px[0], theme.TOP_BAR_HEIGHT_PX))
        self.pause_rect = pygame.Rect(0, 0, theme.ICON_BUTTON_PX, theme.ICON_BUTTON_PX)
        self.pause_rect.midright = (size_px[0] - theme.MARGIN_PX, theme.TOP_BAR_CENTER_Y_PX)

    def pause_clicked(self, event):
        return clicked(event, self.pause_rect)

    def draw(self, screen):
        screen.blit(self._panel, (0, 0))
        if self.pause_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, theme.PAPER_SHADE, self.pause_rect, border_radius=theme.GRID_PX // 2)
        pygame.draw.rect(screen, theme.BLUE, self.pause_rect, 3, border_radius=theme.GRID_PX // 2)
        bar = pygame.Rect(0, 0, theme.GRID_PX, theme.ICON_BUTTON_PX // 2)
        for offset_px in (-theme.GRID_PX, theme.GRID_PX):
            bar.center = (self.pause_rect.centerx + offset_px, self.pause_rect.centery)
            pygame.draw.rect(screen, theme.BLUE, bar, border_radius=theme.GRID_PX // 4)


class FixHint:
    """Names the fingers to fix, one ink chip per finger under the reference card. Each chip is made once."""

    def __init__(self, fonts):
        self._chips = {name: self._chip(fonts.body, name) for name in FINGERS}
        self._center_x_px = CARD_TOPLEFT_PX[0] + theme.REFERENCE_CARD_SIZE_PX[0] // 2
        self._top_px = CARD_TOPLEFT_PX[1] + theme.REFERENCE_CARD_SIZE_PX[1] + theme.GRID_PX * 2

    @staticmethod
    def _chip(font, name):
        label = font.render(name, True, theme.PAPER)
        chip = make_panel((label.get_width() + theme.GRID_PX * 5, label.get_height() + theme.GRID_PX), (*theme.BLUE, 230), theme.GRID_PX)
        pygame.draw.circle(chip, theme.FINGER_FIX, (theme.GRID_PX * 1.5, chip.get_height() // 2), theme.GRID_PX // 2 + 1)
        chip.blit(label, (theme.GRID_PX * 3, theme.GRID_PX // 2))
        return chip

    def draw(self, screen, fingers_off):
        y_px = self._top_px
        for name in fingers_off:
            chip = self._chips[name]
            screen.blit(chip, chip.get_rect(midtop=(self._center_x_px, y_px)))
            y_px += chip.get_height() + theme.GRID_PX // 2


def draw_motion(screen, scorer, sign, hand, idle_wrist_px, now_s, show_guide):
    """For J and Z: the path to draw, starting at the fingertip, and the stroke drawn so far."""
    motion = MOTION_SIGNS.get(sign.name)
    if motion is None:
        return
    if show_guide:
        if hand is not None:
            tracker = scorer.tracker
            if tracker is not None and tracker.anchor_px is not None:
                palm_px, start = tracker.anchor_palm_px, tuple(tracker.anchor_px.tolist())
            else:
                palm_px, start = palm_size(hand.points_px), tuple(hand.points_px[motion.tip, :2].tolist())
            is_left = hand.is_left
        else:
            palm_px = theme.IDLE_GHOST_PALM_PX
            tip = sign.outline[motion.tip, :2] * palm_px
            start = (idle_wrist_px[0] + tip[0], idle_wrist_px[1] + tip[1])
            is_left = False
        phase = (now_s % theme.GUIDE_PERIOD_S) / theme.GUIDE_PERIOD_S
        draw_guide(screen, guide_points(motion, start, palm_px, is_left), phase)
    draw_trail(screen, scorer.trail_px)
