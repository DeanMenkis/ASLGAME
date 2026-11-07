# ASLGAME

A camera-based game for learning ASL handshapes. Karaoke meets osu meets ASL.

The player sees a target handshape drawn over their own hand, matches it on the beat, and earns points for speed and accuracy. The better they sign, the faster it goes.

## Modes

- **Learn**: untimed. Match each handshape at your own pace.
- **Rhythm**: handshapes arrive on a beat. Speed adapts to how well you sign.
- **Music**: sign along to a song or music video. Rhythm mode with a soundtrack.

Timing cues are always visual. Sound is never required to play.

## Design

The interface should explain itself through form, not words. If a screen needs a paragraph to explain it, the design is wrong.

- No emojis anywhere, in the GUI, the code, or the docs.
- No extra headers, captions, or italic lines explaining what a control does. Labels are short and only where a symbol can't do the job.
- Meaning comes from symbols, layout, and motion. A shrinking ring means "now". A filled shape means "done". Position shows order.
- Contrast: one clear focal point per screen. The thing to do next is the strongest element.
- Repetition: the same idea always looks the same. One shape language, one type family, a small fixed palette.
- Alignment: everything sits on a grid. Nothing is placed by eye.
- Proximity: related things sit together, unrelated things are spaced apart.
- Feedback: every action gets an immediate visible response.
- Restraint: remove anything that doesn't help the player sign. Less, but better.
- Color is never the only signal (see Architecture).

References:

- Don Norman, *The Design of Everyday Things*: affordances, signifiers, mapping, feedback
- Robin Williams, *The Non-Designer's Design Book*: contrast, repetition, alignment, proximity
- Dieter Rams, ten principles of good design: less, but better
- Josef Müller-Brockmann, *Grid Systems in Graphic Design*: layout on a grid
- Lidwell, Holden and Butler, *Universal Principles of Design*: general reference
- Steve Krug, *Don't Make Me Think*: self-evident interfaces

## Running

Python 3.11 on macOS.

```
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p models
curl -L -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

- `.venv/bin/python -m aslgame`: the live hand with the target sign's ghost. Left and Right change the target.
- `.venv/bin/python -m aslgame.tools.capture A`: record templates for sign A. Space records a burst after a short countdown, Backspace drops the last burst. Saved to `data/signs/` on close.
- `.venv/bin/python -m unittest`: tests that need no camera or window.
- F3 toggles the debug overlay. Escape quits.

On first run macOS asks for camera access for the app that launched Python, such as Terminal.

## Docs

- [Coding standards](docs/CODING_STANDARDS.md): how we write code
- [Architecture](docs/ARCHITECTURE.md): how the program is shaped
- [Roadmap](docs/ROADMAP.md): what's done, what's next
- [Decisions](docs/DECISIONS.md): why we chose what we chose
- [Credits](docs/CREDITS.md): sources, models, libraries, AI use

## Scope and limits

This is a learning tool, not a translator. It supports a defined set of handshapes and does not understand full ASL grammar, movement, or facial expression. See the roadmap for what is currently supported.

This project is private and for demo use only. Media files are kept out of the repo.
