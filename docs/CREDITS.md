# Credits

Everything external that the project uses. Keep this up to date as things are added.

## Sign language references

- Letter templates are built from the [ASL-Now fingerspelling dataset](https://huggingface.co/datasets/sid220/asl-now-fingerspelling) (sid220, MIT License, DOI 10.57967/hf/1494, commit 9b3c96a): MediaPipe hand landmarks from several signers. Rebuild with `python -m aslgame.tools.import_dataset datasets/asl-now-fingerspelling`.
- The templates have not yet been reviewed by a fluent signer. Each letter should be checked against a trusted reference such as [Lifeprint](https://www.lifeprint.com/asl101/fingerspelling/abc.htm) before any demo.

## Libraries and models

- [MediaPipe](https://github.com/google-ai-edge/mediapipe) and its Tasks API, Apache 2.0
- [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) model by Google (float16 bundle: palm detector plus 21-point hand landmark model), Apache 2.0, included as `models/hand_landmarker.task`
- [pygame](https://www.pygame.org), LGPL 2.1
- [NumPy](https://numpy.org), BSD 3-Clause
- [OpenCV](https://opencv.org) (opencv-contrib-python, installed by MediaPipe), Apache 2.0

## Media

Songs by **Of Far Different Nature** from OpenGameArt, included in `media/`:

- "Bouncer", [CC0](https://opengameart.org/node/107501)
- "Vengeance", [CC0](https://opengameart.org/content/vengeance-electro)
- "Liquid Flame", [CC0](https://opengameart.org/content/liquid-flame)
- "Funky House", [CC0](https://opengameart.org/content/funky-house)
- "Electric Dream", [CC-BY 4.0](https://opengameart.org/content/electric-dream)
- "Victory Party", [CC-BY 4.0](https://opengameart.org/content/victory-party)
- "Whrghah!step", [CC-BY 4.0](https://opengameart.org/content/whrghahstep)

CC-BY 4.0 tracks are credited here and on the in-game About panel, as the license requires.

- "Warm-up 90" and "Hardstyle 150": original tracks synthesized by `aslgame/tools/make_demo_track.py`.
- Sound effects: synthesized in code by `aslgame/media/sfx.py`.

## AI use

Claude Code by Anthropic was used extensively to build this project.
