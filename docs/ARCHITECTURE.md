# Architecture

How the program is shaped. Specific values live in config, not here.

## Big picture

```
Camera thread  ->  Tracker thread  ->  latest landmarks
                                          |
Main loop:  input -> state machine update -> draw -> display
                                          |
                               Matcher scores hand vs target
```

The main loop owns the window and runs at a steady frame rate. Camera capture and hand tracking run on background threads and publish only their newest result. The main loop reads whatever is newest and never waits.

## Layers

- **Capture**: reads camera frames.
- **Tracking**: turns frames into hand landmarks.
- **Matching**: normalizes landmarks and scores them against a target handshape. Pure math, no GUI.
- **Game**: charts, timing, judgement, scoring, speed changes. Pure logic, no GUI.
- **Presentation**: draws the camera feed, ghost hand, approach circles, HUD, and menus.
- **Media**: plays music and reports the playback clock.

Dependencies point downward only. Game logic can be tested without a camera or window.

## State machines

**App**: the top-level screen.

```
Boot -> Menu -> (Learn | Recall | Rhythm | Music) -> Results -> Menu
                              \-> Paused -/
```

**Note**: one handshape in a chart.

```
Waiting -> Approaching -> Hittable -> (Hit | Missed) -> Done
```

**Match detector**: turns noisy per-frame scores into a clean "matched" event.

```
NoHand -> Searching -> Holding -> Matched
```

Each machine has its states in an `Enum` and its transitions in one function.

## Data

- **Signs**: one template set per handshape, recorded and checked against a cited reference.
- **Charts**: a list of notes with target sign and beat time. Learn mode ignores time.
- **Tracks**: a chart plus a song in `media/`.

## Timing

The game clock is the single source of truth for when notes are due. In music mode, the media playback clock drives it. Notes are judged against this clock, so the music and the approach rings stay in step.

## Accessibility rules

- Every cue that matters is visible: approach circles, beat pulse, text judgements.
- Color is never the only signal. Pair it with shape, text, or motion.
- Sound adds feel but is never required.
