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

## Early signs land on the beat

Grades were nearly always D. A sign made before its beat was not accepted until the hit window opened, and every judgement was measured from the beat in both directions, so a ready hand scored OK at best and a fast signer was punished. Now a sign recognized at any point after its note appears is locked in and lands on the beat as Perfect; only lateness costs. Grades run D to S on accuracy rounded to the shown percentage.

## Shorter hold in timed modes

The rhythm hold dropped from 0.15 s to 0.06 s, about two tracker results: enough to ignore a one-frame flicker. Locked signs free the next note at once, so a fluent signer can spell ahead of the rings.

## Multiplier tiers to x10

The multiplier grows by 0.05 per hit and 0.1 per Perfect in a row, plus speed, capped at x10. Each whole number is a tier with its own color, sound, banner, shake, and from x3 embers. A miss that throws away x2 or more says so. A word signed with no miss pays a bonus per letter.

## Word decks instead of one phrase list

Songs repeated the same dozen words. Ten themed decks of about sixty words each (plus A to Z and Everything) are split by length into Easy (up to 4 letters), Medium (5 to 6, or a short word with J or Z), and Hard (7 and up). Each run draws words fresh and shuffled. Charts now hold only tempo, first beat, and a deck name; the level sets beats per sign (4, 2, 1).

## Run length is chosen, not fixed

The 30 s music limit is replaced by 0:30, 1:00, 2:00, or 4:00 picked in the menu. Songs shorter than the choice play to their end, and no new word starts after the time is up, so a run never ends mid word.

## J and Z by shape or by checkpoints

Paths are now compared after scaling each axis on its own (within a limit), so wide or tall strokes pass, and the fingertip is smoothed first. As a second way to pass, the guide is pinned where the stroke starts and the fingertip only has to touch its corners in order. The guide follows a fingertip that rests elsewhere, and resets if progress stalls. Drawn letters get at least two note slots in timed modes.

## Countdown before timed play

Timed runs open with 3, 2, 1, GO. The clock starts after it, so music and notes begin together.

## Rush mode

A mode with no beat: each sign has a fuse, faster signs score better, and clean words add time. It rewards fluent signers directly.

## Paper and ink menu

The menu moved to a warm paper look with serif type, a brushed ensō, and a vermilion seal, so it reads as calm and hand-made against the loud play screens. Signing at the camera in the menu shows the closest letter inside the ensō, as a quick way to warm up.

## Music plays like Rush

In play testing, beat-locked Music felt like it hung: a quick signer had to wait for each sign's beat. Music now uses the Rush engine on the song's clock. The next sign appears the moment one lands, each sign's fuse is a few beats long (6, 4, 3 by level), speed sets the judgement, and a sign that lands on a beat pays an ON BEAT bonus. The fuse ring breathes with the beat. Rhythm mode keeps the beat-locked rings for players who want strict timing.

## One look from menu to play

The paper menu felt apart from the cold grey play screens. Play now uses warm ink panels, paper-colored text, a saffron accent, and serif letters on the card and strip, with a vermilion mark under the target letter. Bold sans type is kept only for arcade banners and score, where punch matters more than calm.

## Ink that catches fire

Four directions were mocked up over a real camera frame: ink, ink on fire, neon arcade, and bright flat. Neon hid the room and felt generic; flat had no intensity. Ink on fire turns the calm menu and loud play into one arc driven by the multiplier, so it replaced the warm arcade restyle.

## The camera is graded on its own thread

Washing the camera to sepia with pygame cost about 14 ms a frame. The camera thread now applies the grade as one 3x3 color matrix with OpenCV (about half a millisecond), to a copy used only for display. Tracking still sees the untouched frame.

## Fire is drawn small and scaled up

Flames and sparks are drawn on a quarter-size layer and scaled up with additive blending, which blurs them into glow without a blur pass. A full run with fire measured about 5 ms of drawing at the median and 11 ms at the 95th percentile, inside a 60 FPS frame.

## The camera keeps its colour

Play testing found the grey camera dull and out of place next to warm paper and fire. The camera now keeps its own colour with a faint warm cast, gets warmer and slightly richer as the fire builds, and only dims for a moment when a fire goes out.

## Fire lights early

With heat starting at x1.8 a player rarely saw any fire. Heat now runs from x1.1 to x3.0: embers after about 5 clean signs in a row, flames after about 15, ablaze after about 30, sooner with Perfects. Blue fire comes at x5.

## The grade is painted, and every panel is paper

The grade as a seal stamp read as odd. It is now the letter in serif inside a brushed ensō: fire colours for S, vermilion for A, ink for the rest. The reference card, results, settings, keys, about, and pause panels are torn paper slips, and buttons are paper and ink, so nothing left from the old dark panels breaks the look.

## The reference hand is a line drawing

Solid ink hands with paper finger lines turned folded letters (A, E, M, N, S, T) into scribbles. The card now draws each finger outlined in ink and filled with paper, farthest first so folded fingers sit over the palm, cropped to the drawing and fitted in the card so sideways letters stay centred.

## The game remembers each letter

Results named the weakest signs of one run and then forgot them, so nothing told a player what to practise next. Each letter now keeps a score between runs that moves toward every new result: it starts in the middle, two Perfects make it known, a miss makes it weak again, and a letter only ever signed slowly never counts as known. Recall and the timed modes count, finished or abandoned; Learn does not, since copying an outline shows nothing about memory. The menu shows the alphabet under the best score: faint until tested, ink once known, a vermilion dot under a weak letter.

## A Practise deck, dealt by need

Practise is a deck like any other, so it works in every mode and level and keeps its own best scores. It holds every word and deals them by need: a word's weight is the mean need of its letters to the fourth power, which about doubles how often weak letters come up while every word can still appear. Untested letters count as needing some practice, so a new player is led through the whole alphabet. Its menu row names the letters it will deal, weakest first, and the results screen offers Practise whenever a run showed letters to work on.
