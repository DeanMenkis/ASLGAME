# How It Works

A short tour of the project for the team. Read this first, then the [Architecture](ARCHITECTURE.md) doc for the rules.

## In one paragraph

ASLGAME is a desktop game written in **Python 3.11**. It reads your webcam, finds your hand with Google's **MediaPipe** hand tracking model, and compares your hand's shape to recorded examples of each ASL letter. The game screen is drawn with **pygame**. There is no server, no internet connection, and no database: everything runs on the laptop, and the only files it reads are in this folder.

## What is used

| Piece | What it does | Where |
| --- | --- | --- |
| Python 3.11 | The only language in the project | everything in `aslgame/` |
| pygame | Window, drawing, keyboard and mouse, sound | `aslgame/presentation/`, `aslgame/media/` |
| MediaPipe Hand Landmarker | Finds 21 points on the hand in each camera frame | `aslgame/tracking/` |
| OpenCV | Reads the webcam, writes demo videos | `aslgame/capture/`, `aslgame/media/recorder.py` |
| NumPy | All the hand math, and synthesizing sounds | `aslgame/matching/`, `aslgame/media/sfx.py` |
| JSON files | Letter templates, song charts, settings | `data/`, `settings.json` |

There is no "backend" in the web sense. The closest thing is the two background threads described below.

## The three threads

The game does three jobs at once so the picture never stutters:

```
Camera thread     reads a frame from the webcam ........ about 30 times a second
Tracker thread    finds the hand in the newest frame ... about 30 times a second, ~6 ms each
Main thread       reads input, updates the game, draws . 60 times a second
```

Each background thread puts only its **newest** result in a shared slot (`aslgame/latest.py`). The main thread takes whatever is newest and never waits. If tracking is slow for a moment, the game keeps drawing at 60 FPS with the last known hand.

## From camera to points, step by step

1. **Capture** (`capture/camera.py`): grab a frame, mirror it like a selfie, measure brightness for the "More light" warning.
2. **Track** (`tracking/tracker.py`): MediaPipe returns 21 landmarks (wrist, knuckles, fingertips) as x, y, z, plus left or right hand.
3. **Normalize** (`matching/normalize.py`): move the wrist to 0, scale so the palm is size 1, and mirror left hands to look like right hands. Now the same handshape gives the same numbers anywhere on screen, at any distance, with either hand.
4. **Match** (`matching/matcher.py`): measure the average distance between your 21 points and each recorded example of the target letter. Close means a high score (0 to 1). If another letter fits clearly better, the target is rejected, which stops look-alikes passing.
5. **Confirm** (`game/match_detector.py`): a score has to stay high for a moment (a "hold") before it counts, so a single lucky frame does not.
6. **Play** (`game/rhythm.py` and the screens): turn confirmations into progress, timing judgements, score, and combos.
7. **Draw** (`presentation/`): camera picture, the ghost hand silhouette, rings, strip, and menus.

## Where things live

```
aslgame/
  capture/        webcam thread
  tracking/       hand tracking thread
  matching/       normalize and score hands (pure math, no window)
  game/           modes, timing, scoring, state machines (pure logic, no window)
  media/          music player, sound effects, demo recorder
  presentation/   everything drawn on screen
    screens/      one file per screen: menu, learn, rhythm, results, ...
  tools/          scripts you run by hand: import templates, chart songs, make tracks
  app.py          the main loop and the screen state machine
  config.py       every tunable number (thresholds, timings, paths)
  theme.py        every visual number (colors, sizes, spacing)
data/
  signs/          one JSON file per letter: recorded hand shapes
  charts/         one JSON file per song: tempo, first beat, words to sign
tests/            tests that run without a camera or window
docs/             these documents
media/, models/   songs and the tracking model (local only, not in git)
```

The rule that keeps this tidy: **game and matching code never import pygame**, so they can be tested without a window. Drawing code depends on game code, never the other way round.

## State machines

Anything with phases is an explicit `Enum` with its transitions in one place:

- **App** (`game/app_flow.py`): Boot, Menu, Learn, Recall, Rhythm, Music, Paused, Results.
- **Match detector**: No hand, Searching, Holding, Matched.
- **Note** in rhythm modes: Waiting, Approaching, Hittable, Hit or Missed, Done.
- **Motion** for J and Z (`game/motion.py`): No hand, Shaping, Drawing, Done.

## The modes

- **Learn**: the target shape is drawn over your hand. No timer.
- **Recall**: only the letter is shown; sign it from memory. Tab shows a hint.
- **Rhythm**: letters arrive on a beat; speed goes up when you do well and down when you struggle.
- **Music**: like Rhythm, locked to a song's tempo.

## J and Z

J and Z are drawn in the air, so a still shape is not enough. For these, the game checks which fingers are straight (pinky for J, index for Z), then follows that fingertip and compares its path to the letter's path, ignoring size and speed. The path is shown as a dashed guide with a moving dot, and your own stroke as a yellow trail.

## Where the letter shapes come from

We did not record the letters ourselves. `tools/import_dataset.py` reads the public **ASL-Now** dataset (MediaPipe landmarks from several signers), normalizes each sample, lines up left and right hands, drops outliers, and writes `data/signs/*.json`. Held-out tests match the right letter 94% of the time. A fluent signer still needs to check them.

## Songs and charts

Songs are audio files in `media/` (never committed). Each has a chart in `data/charts/` saying its tempo, when the first note lands, and which words to sign. `tools/chart_track.py` finds the tempo and beat of any song automatically. Two songs and all sound effects are generated from code, so they need no files or licenses.

## Running and testing

- Play: double-click `ASLGAME.command`, or `.venv/bin/python -m aslgame`.
- Tests: `.venv/bin/python -m unittest` (about 40 tests, under a second).
- Performance: press F3 in game for FPS and tracking delay.

## Changing things safely

- A number feels wrong (too strict, too fast)? Change it in `config.py`.
- A color or size feels wrong? Change it in `theme.py`.
- New word or phrase? Add it to `LEARN_WORDS` in `config.py`.
- New song? Put it in `media/`, run `tools/chart_track.py`, credit it in `docs/CREDITS.md`.
- Before committing: run the tests, and keep the [coding standards](CODING_STANDARDS.md).
