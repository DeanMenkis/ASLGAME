# Decisions

A short log of choices and why. Newest at the bottom. One entry per decision.

## Learning game, not a translator

Full ASL translation is out of reach. A focused trainer on a defined sign set is achievable, honest, and more fun.

## Hand landmarks, not image classification

Landmarks from a tracking model are small, fast to compare, and less sensitive to lighting and background than raw images.

## Template matching on recorded examples

Recorded templates checked against a trusted reference give reliable results without training a model. One matcher powers both recognition and scoring.

## pygame for the GUI

A rhythm game needs a tight frame loop with custom drawing every frame. pygame fits that better than a widget toolkit and is much lighter.

## Visual timing first

Every timing cue is visual so the game works without sound. Music is an extra layer for players who can hear it.

## Songs are included

Songs are included in `media/` because every track is CC0, CC-BY 4.0 (credited in-game and in Credits), or synthesized by the project. Videos are not committed.

## MediaPipe Tasks API in VIDEO mode

HandLandmarker from the Tasks API replaces the legacy `mp.solutions` API. VIDEO mode runs synchronously on the tracker thread, so the thread always works on the newest frame and drops the rest, with no callback plumbing.

## Normalize in image space, keep orientation

Landmarks are normalized from image coordinates: wrist at the origin, scaled by mean palm size, left hands mirrored to match right hands. The same transform inverted places the ghost outline on the live hand. Rotation is not removed, because orientation is part of some handshapes, such as H versus U.

## pygame loads before OpenCV

opencv-contrib-python and pygame each bundle SDL2. On macOS the first copy loaded wins, so every entry point imports the runtime, which imports pygame, before anything that imports OpenCV.

## Hold-to-confirm with two thresholds

A sign counts once the score stays high for a short hold. Starting a hold needs the match threshold; breaking it needs a drop below a lower release threshold, so tracking jitter near the line does not keep restarting the hold.

## Fingerspelling without J and Z

J and Z are traced with motion, and templates hold a single still handshape. Learn mode words avoid them until movement is supported. Superseded by "J and Z by finger straightness and path" below.

## Templates from a public landmark dataset

Recording every letter by hand needs a fluent signer and time. The ASL-Now dataset already holds MediaPipe landmarks for each letter from several signers, so the import tool normalizes them into templates. Its frames are treated as 16:9 because bone proportions are most consistent there. Signers used both hands, so each letter's samples are mirrored to one side, seeded by palm direction, or by pointing direction for sideways letters (G, H, P, Q). Held-out samples match the right letter 94% of the time; most misses are true look-alikes such as R and U.

## Reject a target when a rival fits clearly better

A target only passes when no other sign outscores it by more than a small margin. This cut wrong-letter accepts by about two thirds on held-out data for a one point drop in right-letter accepts.

## Rhythm charts are generated during play

Adaptive speed changes the gap between notes, so a fixed list of note times cannot work. Rhythm mode schedules each note a few beats ahead from the current speed, and the word is repeated so speed has room to change. Notes land on beats, so the beat pulse and the approach ring agree.

## The approach ring closes on the hand

The hit ring sits around the player's palm rather than in a fixed lane, so the timing cue is where the player is already looking.

## Handedness label is swapped for mirrored frames

The MediaPipe docs say handedness assumes a mirrored image, but in play testing the Tasks API reported the player's right hand as "Left" on the mirrored frames, which mirrored the ghost. The tracker now swaps the label when the camera is mirrored.

## Silhouette ghost instead of a skeleton

A white skeleton blended into the camera image and did not read as a hand. The ghost is now a filled hand silhouette with a dark and light traced edge, so it stands out on any background. Fingers that are clearly off are traced in a warning color on the player's own hand and named under a reference card.

## Music clock starts with playback

Tracks load into memory at startup. The game clock starts at the moment the sound starts and pauses with it, so chart times line up with the music. An offset setting was planned for camera, tracking, and audio delay; see the next entry.

## No audio offset setting

Play testing showed the default timing felt right, and the setting added a control nobody needed. It was removed with the code behind it.

## Sounds are synthesized

Sound effects and the two demo songs are generated with NumPy, so there are no files to license and they always match the beat. The other songs are licensed tracks; see Credits.

## Scaled window

The game draws at the camera's 1280 by 720 and pygame scales it to a larger, resizable window, so layout and mouse positions never change with the window size.

## The shown outline always matches

Some letters (G, O, P) vary a lot between signers, so their averaged outline sat between clusters and scored under the threshold. Copying the ghost exactly did not count. The outline is now one of each sign's samples, so the shape on screen is always a valid answer.

## Recall reuses the judgement look

Recall marks letters signed from memory like a Perfect and letters that needed a hint like an OK, so the strip speaks one visual language across modes.

## Songs are charted from the phrase list

The chart tool fills each song with the phrase list, so every song practises real words rather than random letters.

## J and Z by finger straightness and path

Dataset samples of J and Z were caught mid-stroke, so their average shape is a blur. Instead the game checks which fingers are straight, which holds however the wrist turns, then matches the fingertip's path after resampling it by distance and scaling it to unit size. Speed and size do not matter; direction and shape do. Reversed, mirrored, and straight strokes are rejected in tests.

## One Settings button

Four header controls (About, two toggles, keys) competed with the title. Settings now holds the toggles and About, leaving the header with the title, Settings, and the keys button.
