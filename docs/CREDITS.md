# Credits

Everything external that the project uses. Required by the brief. Keep this up to date as things are added.

## Sign language references

- Letter templates are built from the [ASL-Now fingerspelling dataset](https://huggingface.co/datasets/sid220/asl-now-fingerspelling) (sid220, MIT License, DOI 10.57967/hf/1494, commit 9b3c96a): MediaPipe hand landmarks from several signers. Rebuild with `python -m aslgame.tools.import_dataset datasets/asl-now-fingerspelling`.
- The templates have not yet been reviewed by a fluent signer. Each letter should be checked against a trusted reference such as [Lifeprint](https://www.lifeprint.com/asl101/fingerspelling/abc.htm) before any demo.

## Libraries and models

- [MediaPipe](https://github.com/google-ai-edge/mediapipe) and its Tasks API, Apache 2.0
- [MediaPipe hand landmarker model](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker), Apache 2.0, downloaded locally and not committed
- [pygame](https://www.pygame.org), LGPL 2.1
- [NumPy](https://numpy.org), BSD 3-Clause
- [OpenCV](https://opencv.org) (opencv-contrib-python, installed by MediaPipe), Apache 2.0

## Media

- (add each song or video used in the demo, with artist and title)

## AI use

- Claude Code (Anthropic) wrote the Phase 1 code (camera and tracking threads, normalization, matcher, capture tool, ghost outline, debug overlay) and the Phase 2 code (app state machine, menu, sign queue, match detector, karaoke strip, Learn mode).
