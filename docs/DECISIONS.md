# Decisions

A short log of choices and why. Newest at the bottom. One entry per decision.

## Learning game, not a translator

Full ASL translation is out of reach and not what the brief asks for. A focused trainer on a defined sign set is achievable, honest, and more fun.

## Hand landmarks, not image classification

Landmarks from a tracking model are small, fast to compare, and less sensitive to lighting and background than raw images.

## Template matching on our own recordings

Recorded templates checked against a trusted reference give reliable results without training a model. One matcher powers both recognition and scoring.

## pygame for the GUI

A rhythm game needs a tight frame loop with custom drawing every frame. pygame fits that better than a widget toolkit and is much lighter.

## Visual timing first

Every timing cue is visual so the game works without sound. Music is an extra layer for players who can hear it.

## Media stays local

Songs and videos are used for a private demo only and are never committed to the repo.

## MediaPipe Tasks API in VIDEO mode

HandLandmarker from the Tasks API replaces the legacy `mp.solutions` API. VIDEO mode runs synchronously on the tracker thread, so the thread always works on the newest frame and drops the rest, with no callback plumbing.

## Normalize in image space, keep orientation

Landmarks are normalized from image coordinates: wrist at the origin, scaled by mean palm size, left hands mirrored to match right hands. The same transform inverted places the ghost outline on the live hand. Rotation is not removed, because orientation is part of some handshapes, such as H versus U.

## pygame loads before OpenCV

opencv-contrib-python and pygame each bundle SDL2. On macOS the first copy loaded wins, so every entry point imports the runtime, which imports pygame, before anything that imports OpenCV.

## Hold-to-confirm with two thresholds

A sign counts once the score stays high for a short hold. Starting a hold needs the match threshold; breaking it needs a drop below a lower release threshold, so tracking jitter near the line does not keep restarting the hold.

## Fingerspelling without J and Z

J and Z are traced with motion, and templates hold a single still handshape. Learn mode words avoid them until movement is supported.

## Templates from a public landmark dataset

Recording every letter by hand needs a fluent signer and time. The ASL-Now dataset already holds MediaPipe landmarks for each letter from several signers, so the import tool normalizes them into templates. Its frames are treated as 16:9 because bone proportions are most consistent there. Signers used both hands, so each letter's samples are mirrored to one side, seeded by palm direction, or by pointing direction for sideways letters (G, H, P, Q). Held-out samples match the right letter 94% of the time; most misses are true look-alikes such as R and U.

## Reject a target when a rival fits clearly better

A target only passes when no other sign outscores it by more than a small margin. This cut wrong-letter accepts by about two thirds on held-out data for a one point drop in right-letter accepts.
