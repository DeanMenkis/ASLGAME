"""Phase 1 viewer: the live hand with the target sign's ghost outline and match score."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import pygame

from aslgame import config, theme
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, place_on
from aslgame.presentation.draw import draw_hand, draw_ring, draw_text_centered
from aslgame.signs import load_signs

RING_CENTER_PX = (theme.MARGIN_PX + theme.RING_RADIUS_PX, theme.MARGIN_PX + theme.RING_RADIUS_PX)
STEP_KEYS = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1}


def main():
    signs = load_signs(config.SIGNS_DIR)
    names = list(signs)
    runtime = Runtime(config.WINDOW_TITLE)
    labels = {name: runtime.font_large.render(name, True, theme.INK) for name in names}
    target_index = 0
    running = True
    while running:
        for event in pygame.event.get():
            if runtime.handle_common(event):
                running = False
            elif event.type == pygame.KEYDOWN and event.key in STEP_KEYS and names:
                target_index = (target_index + STEP_KEYS[event.key]) % len(names)
        runtime.begin_frame()
        hand = runtime.result.hand if runtime.result else None
        if hand is not None:
            draw_hand(runtime.screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
        if names:
            target = signs[names[target_index]]
            draw_target(runtime.screen, target, labels[target.name], hand)
        runtime.end_frame()
    runtime.close()


def draw_target(screen, sign, label, hand):
    score = 0.0
    if hand is not None:
        score = matcher.score(normalize(hand.points_px, hand.is_left), sign.samples)
        ghost_px = place_on(sign.outline, hand.points_px, hand.is_left)
        matched = score >= config.MATCH_THRESHOLD
        draw_hand(screen, ghost_px, theme.GHOST, theme.GHOST_LINE_PX, theme.GHOST_JOINT_RADIUS_PX, matched)
    ring_color = theme.ACCENT if score >= config.MATCH_THRESHOLD else theme.INK
    draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, 1.0, theme.INK_DIM)
    draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, score, ring_color)
    draw_text_centered(screen, label, RING_CENTER_PX)


if __name__ == "__main__":
    main()
