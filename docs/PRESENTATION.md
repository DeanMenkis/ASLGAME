# Presentation

Notes for a five minute talk with a live demo. A backup recording covers camera or lighting problems.

## Before the talk

- Charge the laptop and close other camera apps.
- Run `.venv/bin/python -m aslgame.tools.make_demo_track` if `media/` is empty, and check Bouncer is in `media/`.
- Record a backup run: start the game, press F9, play one Learn word and one Music song, press F9 again. The file is in `recordings/`.
- Face a light source; avoid a bright window behind you.

## Outline

1. **The problem (30 s).** Learning handshapes from pictures gives no feedback on your own hand.
2. **The idea (30 s).** Karaoke meets osu meets ASL: the target shape is drawn over your hand, and you match it on the beat.
3. **Live demo (2 min).**
   - Menu: modes, words, settings.
   - Learn, "HI": silhouette, finger hints, hold to confirm, strip fills.
   - Turn on Finger colors (C).
   - Music, Hardstyle 150 or Bouncer: approach ring, judgements, combo, sounds.
   - Results: score, accuracy, signs to practise.
4. **How it works (1 min).**
   - Camera and hand tracking run on background threads; the frame loop never waits.
   - MediaPipe finds 21 landmarks; they are normalized for position, size, and hand side.
   - Templates come from a public landmark dataset; held-out samples match the right letter 94% of the time.
   - A rival check rejects look-alikes; per-finger distances drive the hints.
5. **Design (30 s).** One focal point, shape over words, color never the only signal.
6. **Limits and next steps (30 s).** Letters only, no J or Z, templates not yet checked by a fluent signer. Next: signer review, motion signs, more songs.

## If the live demo fails

Play the backup recording from `recordings/`, and talk over it with the same outline.
