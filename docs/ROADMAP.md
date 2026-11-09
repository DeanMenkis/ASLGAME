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

## Open questions

- Review of the letter templates by a fluent signer
- Whether to add common word signs, which need movement and location
- Detecting backlight, not just low light
