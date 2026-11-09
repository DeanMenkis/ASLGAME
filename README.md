# ASLGAME

Learn the ASL alphabet by signing along to music.

![Three players dancing while one signs letters at the webcam, with the game projected behind them](docs/demo.jpg)

Apps like Duolingo work well for spoken languages but leave out visual ones like American Sign Language. ASLGAME is a rhythm game in the spirit of osu!: your webcam watches your hand, a target handshape appears over it, and you match each letter on the beat. The goal is to bring movement, music, and play into learning ASL, in a classroom or at home.

Runs locally.

Developed for BEC 2026

## Install

You need a webcam and about 650 MB of free space: Python, the game's libraries (MediaPipe, OpenCV, NumPy, pygame), and the game with its songs. Setup downloads everything it needs the first time it runs.

### Mac

Needs Apple Silicon (M1 or newer). Open Terminal, paste this line, and press Return:

```
git clone https://github.com/DeanMenkis/ASLGAME.git ~/ASLGAME && ~/ASLGAME/ASLGAME.command
```

The first run takes a few minutes to set up, then the game opens. Allow camera access when macOS asks. To play again later, double-click `ASLGAME.command` in the `ASLGAME` folder in your home folder.

If macOS asks to install developer tools when you run the line, click Install, then run the line again.

### Windows (untested)

Windows support has not been tested yet. If you try it, please report what happens.

Open PowerShell, paste this line, and press Return:

```
irm https://github.com/DeanMenkis/ASLGAME/archive/refs/heads/main.zip -OutFile $env:TEMP\aslgame.zip; Expand-Archive $env:TEMP\aslgame.zip $HOME -Force; & $HOME\ASLGAME-main\ASLGAME.bat
```

The first run takes a few minutes to set up, then the game opens. To play again later, double-click `ASLGAME.bat` in the `ASLGAME-main` folder in your user folder.

## Modes

- **Learn**: untimed. Match each handshape at your own pace.
- **Recall**: untimed and harder. Only the letter is shown; sign it from memory.
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

## Developer notes

- Keys: mouse or keyboard; press H or the ? button for the full list.
- All 26 letters. J and Z are drawn in the air: make the handshape, then trace the path shown.
- `.venv/bin/python -m aslgame`: runs the game directly.
- `.venv/bin/python -m aslgame.tools.make_demo_track`: rebuilds the two synthesized songs (Warm-up 90, Hardstyle 150) in `media/`.
- `.venv/bin/python -m aslgame.tools.chart_track song.mp3 "Title"`: charts any song in `media/` (finds tempo and first beat). Add `--bpm` if it picks double time.
- `.venv/bin/python -m aslgame.tools.import_dataset datasets/asl-now-fingerspelling`: rebuilds the letter templates.
- `.venv/bin/python -m aslgame.tools.capture A`: record templates for sign A. Space records a burst after a short countdown, Backspace drops the last burst. Saved to `data/signs/` on close.
- `.venv/bin/python -m unittest`: tests that need no camera or window.
- F3 toggles the performance overlay and the tracked skeleton. F9 records a demo video to `recordings/`.
- A word is playable once every letter in it has a recorded template. The menu lists the missing letters.

## Docs

- [How it works](docs/HOW_IT_WORKS.md): start here, a one-minute overview
- [Coding standards](docs/CODING_STANDARDS.md): how we write code
- [Architecture](docs/ARCHITECTURE.md): how the program is shaped
- [Roadmap](docs/ROADMAP.md): what's done, what's next
- [Decisions](docs/DECISIONS.md): why we chose what we chose
- [Credits](docs/CREDITS.md): sources, models, libraries, AI use
- [Accessibility](docs/ACCESSIBILITY.md): cues, options, and known gaps
- [Presentation](docs/PRESENTATION.md): talk outline and demo checklist

## Scope and limits

The letter shapes come from a public dataset and have not yet been checked by a fluent signer. Corrections are very welcome.

This is a learning tool, not a translator. It supports the fingerspelled alphabet (J and Z by their drawn path) and does not understand word signs, full ASL grammar, or facial expression. See the roadmap for what is currently supported.

All songs and the hand tracking model are included under their licenses; see [Credits](docs/CREDITS.md).
