# Roadmap

Build the core first, then the game on top. Each phase should run end to end before the next starts.

## Phase 1: Core

- [x] Camera feed in a window
- [x] Hand tracking on a background thread
- [x] Landmark normalization
- [x] Capture tool to record sign templates
- [x] Matcher that scores a hand against a target
- [x] Ghost hand outline drawn over the live hand

## Phase 2: Learn mode

- [x] App state machine and menu
- [x] Sign queue for a word or sentence
- [x] Match detector with hold-to-confirm
- [x] Karaoke strip showing progress through the word
- [x] Clear on-screen instructions

## Phase 3: Rhythm mode

- [x] Game clock and charts
- [x] Approach circles and beat pulse
- [x] Timing judgements and scoring
- [x] Combo system
- [x] Adaptive speed based on recent accuracy
- [x] Results screen with weakest signs

## Phase 4: Music mode

- [x] Local music playback (video not supported yet)
- [x] Chart synced to the media clock
- [x] Latency offset setting (later removed as not needed)

## Phase 5: Polish and demo

- [x] Accessibility pass (no sound-only or color-only cues), see [Accessibility](ACCESSIBILITY.md)
- [x] Credits and limitations screen
- [x] Debug overlay for FPS and latency
- [x] Demo clip in the README
- [x] Presentation

## Phase 6: Depth

- [x] Recall mode: sign from memory with an optional hint
- [x] Longer phrase list and a scrolling menu
- [x] More songs, charted automatically
- [x] Per-letter judgement colors in the strip
- [x] Low light warning
- [x] J and Z as motion signs: handshape plus a drawn path
- [x] Settings panel in place of header toggles
- [x] Arcade scoring: multiplier from combo, Perfect streak, and speed; score pops, particles, combo banners, grades

## Phase 7: Arcade overhaul

Built on the `arcade-overhaul` branch. Each item is ticked when its feature is finished and its decision is logged.

- [x] Judging that rewards a ready hand, and grades from D to S that can be earned
- [x] Faster recognition in timed modes
- [x] Word decks: themed word lists, drawn fresh each run, split into Easy, Medium, and Hard
- [x] Level and run length chosen in the menu; each song has its own deck
- [x] Multiplier tiers up to x10, word clear bonuses, and louder feedback
- [x] J and Z by checkpoints as well as by shape
- [x] 3, 2, 1 countdown before timed modes
- [x] Rush mode: no beat, sign as fast as you can before the clock runs out
- [x] Menu redesign: paper, ink, and a live hand reader
- [x] Results with a grade seal, and best scores kept between runs
- [x] Art direction: ink that catches fire, from the menu through play to results
- [ ] Play test all of the above with a camera and tune the numbers

## Phase 8: A game that teaches

- [x] Letter mastery: every letter's record is kept between runs and shown as an alphabet in the menu
- [x] Practise deck: words dealt by how much their letters need work, in every mode
- [x] Practise button on the results screen
- [ ] Play test: check that two Perfects for known and one miss for weak feel fair

## Open questions

- Review of the letter templates by a fluent signer
- Whether to add common word signs, which need movement and location
- Detecting backlight, not just low light
