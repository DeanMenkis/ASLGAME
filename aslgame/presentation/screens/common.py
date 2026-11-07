"""Helpers shared by the screens: scoring the target, the ghost, the reference card, and the top bar."""

import pygame

from aslgame import config, theme
from aslgame.game.motion import MOTION_SIGNS, MotionState, MotionTracker
from aslgame.game.motion import update as motion_update
from aslgame.game.rhythm import Judgement
from aslgame.hand import FINGERS, WRIST
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, palm_size
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.hand_shape import GhostRenderer, draw_finger_fixes, render_silhouette
from aslgame.presentation.motion_path import draw_guide, draw_trail, guide_points
from aslgame.presentation.ui import clicked, make_panel

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_SPACE)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
JUDGEMENT_TEXT = {Judgement.PERFECT: "Perfect", Judgement.GOOD: "Good", Judgement.OK: "OK", Judgement.MISS: "Miss"}
CARD_TOPLEFT_PX = (theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX + theme.GRID_PX * 2)


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
                motion_update(self.tracker, 0.0, False, None, False)
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
        state = motion_update(self.tracker, result.captured_s, self.shape_ok, tip_px / palm_size(hand.points_px), hand.is_left)
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
    """A large, still picture of the target sign, so the shape is clear even while the hand moves."""

    def __init__(self, fonts, signs, names, settings):
        # Cards are built the first time each is shown (about a millisecond), so long words start without a pause.
        self._fonts = fonts
        self._signs = signs
        self._cards = {}
        self._settings = settings

    def _build_letter(self, fonts, name):
        """Recall mode: only the letter, large, with no picture of the shape."""
        card = make_panel(theme.REFERENCE_CARD_SIZE_PX)
        letter = fonts.display.render(name, True, theme.INK)
        draw_text_centered(card, letter, (card.get_width() // 2, card.get_height() // 2))
        return card

    def _build(self, fonts, sign, finger_colors):
        card = make_panel(theme.REFERENCE_CARD_SIZE_PX)
        width_px, height_px = theme.REFERENCE_CARD_SIZE_PX
        draw_text_centered(card, fonts.large.render(sign.name, True, theme.INK), (width_px // 2, theme.GRID_PX * 6))
        silhouette, wrist = render_silhouette(sign.outline, theme.REFERENCE_PALM_PX, False, finger_colors)
        bottom_px = height_px - theme.GRID_PX * 4
        # Placed by the wrist, then pulled back inside the card if the shape runs over an edge.
        rect = silhouette.get_rect(topleft=(width_px // 2 - wrist[0], bottom_px - wrist[1] - theme.REFERENCE_PALM_PX))
        rect.clamp_ip(pygame.Rect(0, theme.GRID_PX * 11, width_px, height_px - theme.GRID_PX * 12))
        card.blit(silhouette, rect)
        motion = MOTION_SIGNS.get(sign.name)
        if motion is not None:
            tip = sign.outline[motion.tip, :2] * theme.REFERENCE_PALM_PX
            start = (rect.left + wrist[0] + tip[0], rect.top + wrist[1] + tip[1])
            draw_guide(card, guide_points(motion, start, theme.REFERENCE_PALM_PX * theme.CARD_PATH_SCALE, False))
        return card

    def draw(self, screen, name, progress=None, letter_only=False):
        """progress, from 0 to 1, fills a bar along the card's bottom edge."""
        key = (name, "letter" if letter_only else self._settings.finger_colors)
        if key not in self._cards:
            sign = self._signs[name]
            self._cards[key] = self._build_letter(self._fonts, name) if letter_only else self._build(self._fonts, sign, key[1])
        card = self._cards[key]
        rect = screen.blit(card, CARD_TOPLEFT_PX)
        if progress:
            fill = pygame.Rect(rect.left, rect.bottom - theme.GRID_PX, int(rect.width * min(1.0, progress)), theme.GRID_PX)
            pygame.draw.rect(screen, theme.ACCENT, fill, border_radius=theme.GRID_PX // 2)


class TopBar:
    """The bar along the top of play screens, with a pause button at the right."""

    def __init__(self, size_px):
        self._panel = make_panel((size_px[0], theme.TOP_BAR_HEIGHT_PX), theme.SURFACE, 0)
        self.pause_rect = pygame.Rect(0, 0, theme.ICON_BUTTON_PX, theme.ICON_BUTTON_PX)
        self.pause_rect.midright = (size_px[0] - theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2)

    def pause_clicked(self, event):
        return clicked(event, self.pause_rect)

    def draw(self, screen):
        screen.blit(self._panel, (0, 0))
        hovered = self.pause_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, theme.SURFACE_HOVER if hovered else theme.SURFACE_RAISED, self.pause_rect, border_radius=theme.CORNER_PX)
        bar = pygame.Rect(0, 0, theme.GRID_PX, theme.ICON_BUTTON_PX // 2)
        for offset_px in (-theme.GRID_PX, theme.GRID_PX):
            bar.center = (self.pause_rect.centerx + offset_px, self.pause_rect.centery)
            pygame.draw.rect(screen, theme.INK, bar, border_radius=theme.GRID_PX // 4)


class FixHint:
    """Names the fingers to fix, one per line under the reference card. Each name is rendered once."""

    def __init__(self, fonts):
        self._names = {name: fonts.body.render(name, True, theme.FINGER_FIX) for name in FINGERS}
        self._center_x_px = CARD_TOPLEFT_PX[0] + theme.REFERENCE_CARD_SIZE_PX[0] // 2
        self._top_px = CARD_TOPLEFT_PX[1] + theme.REFERENCE_CARD_SIZE_PX[1] + theme.GRID_PX * 2

    def draw(self, screen, fingers_off):
        y_px = self._top_px
        for name in fingers_off:
            surface = self._names[name]
            screen.blit(surface, surface.get_rect(midtop=(self._center_x_px, y_px)))
            y_px += surface.get_height()


def draw_motion(screen, scorer, sign, hand, idle_wrist_px, now_s, show_guide):
    """For J and Z: the path to draw, starting at the fingertip, and the stroke drawn so far."""
    motion = MOTION_SIGNS.get(sign.name)
    if motion is None:
        return
    if show_guide:
        if hand is not None:
            palm_px = palm_size(hand.points_px)
            start = scorer.trail_px[0] if scorer.trail_px else tuple(hand.points_px[motion.tip, :2].tolist())
            is_left = hand.is_left
        else:
            palm_px = theme.IDLE_GHOST_PALM_PX
            tip = sign.outline[motion.tip, :2] * palm_px
            start = (idle_wrist_px[0] + tip[0], idle_wrist_px[1] + tip[1])
            is_left = False
        phase = (now_s % theme.GUIDE_PERIOD_S) / theme.GUIDE_PERIOD_S
        draw_guide(screen, guide_points(motion, start, palm_px, is_left), phase)
    draw_trail(screen, scorer.trail_px)
