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

## Rhythm charts are generated as you play

Adaptive speed changes the gap between notes, so a fixed list of note times cannot work. Rhythm mode schedules each note a few beats ahead from the current speed, and the word is repeated so speed has room to change. Notes land on beats, so the beat pulse and the approach ring agree.

## The approach ring closes on the hand

The hit ring sits around the player's palm rather than in a fixed lane, so the timing cue is where the player is already looking.

## Handedness label is swapped for mirrored frames

The MediaPipe docs say handedness assumes a mirrored image, but in play testing the Tasks API reported the player's right hand as "Left" on our mirrored frames, which mirrored the ghost. The tracker now swaps the label when the camera is mirrored.

## Silhouette ghost instead of a skeleton

A white skeleton blended into the camera image and did not read as a hand. The ghost is now a filled hand silhouette with a dark and light traced edge, so it stands out on any background. Fingers that are clearly off are traced in a warning color on the player's own hand and named under a reference card.

## Music clock starts with playback

Tracks load into memory at startup. The game clock starts at the moment the sound starts and pauses with it, so chart times line up with the music. A player-set offset in the menu cancels camera, tracking, and audio delay.

## No audio offset setting

Play testing showed the default timing felt right, and the setting added a control nobody needed. It was removed with the code behind it.

## Sounds are synthesized

Sound effects and the two demo songs are generated with NumPy, so there are no files to license and they always match the beat. Bouncer, a CC0 track, gives the demo a real song.

## Scaled window

The game draws at the camera's 1280 by 720 and pygame scales it to a larger, resizable window, so layout and mouse positions never change with the window size.
