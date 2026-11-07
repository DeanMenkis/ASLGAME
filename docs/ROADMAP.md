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
- [x] Latency offset setting

## Phase 5: Polish and demo

- [ ] Accessibility pass (no sound-only or color-only cues)
- [ ] Credits and limitations screen
- [x] Debug overlay for FPS and latency
- [ ] Backup demo recording
- [ ] Presentation

## Open questions

- Which handshapes make the supported set
- How to handle signs that look alike
- Which songs or tracks to use for the demo
