# Developer notes

Commands are shown for Mac. On Windows, use `.venv\Scripts\python` in place of `.venv/bin/python`.

- Keys: mouse or keyboard; press H or the ? button for the full list.
- All 26 letters. J and Z are drawn in the air: make the handshape, then trace the path shown.
- `.venv/bin/python -m aslgame`: runs the game directly.
- `.venv/bin/python -m aslgame.tools.make_demo_track`: rebuilds the two synthesized songs (Warm-up 90, Hardstyle 150) in `media/`.
- `.venv/bin/python -m aslgame.tools.chart_track song.mp3 "Title"`: charts any song in `media/` (finds tempo and first beat). Add `--bpm` if it picks double time.
- `.venv/bin/python -m aslgame.tools.import_dataset datasets/asl-now-fingerspelling`: rebuilds the letter templates.
- `.venv/bin/python -m aslgame.tools.capture A`: record templates for sign A. Space records a burst after a short countdown, Backspace drops the last burst. Saved to `data/signs/` on close.
- `.venv/bin/python -m unittest`: tests that need no camera or window.
- F3 toggles the performance overlay and the tracked skeleton. On a Mac keyboard, hold fn.
- A word is playable once every letter in it has a recorded template. The menu lists the missing letters.
