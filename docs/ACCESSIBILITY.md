# Accessibility

Audit of every cue in the game against the rules in the architecture doc: nothing that matters is sound-only or color-only.

## Cues

| Cue | Visible form | Not color alone because | Sound |
| --- | --- | --- | --- |
| Target sign | Silhouette over the hand and a large picture on the reference card | Shape | None |
| Sign matched | Silhouette fills, "Hold it" label, card bar fills | Fill, text, and motion | Chime when confirmed |
| Fingers to fix | Fingers traced on the player's hand, names listed under the card | Finger names in text | None |
| Timing | The fuse arc around the palm shortening, beat dot growing and shrinking | Size and motion | Music beat (optional) |
| Judgement | A label reading "PERFECT", "GOOD", "OK", or "MISS" by the hand | Text | Distinct sound per judgement |
| Score and multiplier | Rolling score and "x2.4" in the top bar, "+300" pops on each hit | Text and motion | None |
| Combo milestone | "10 combo" banner | Text | Sparkle |
| Heat (multiplier) | The camera print gains its yellow plate; halftone dots rise from the bottom edge | The multiplier number is always shown | Crackle, whoosh |
| Heat lost to a miss | "x5 OUT" banner, the dots drop away, the print slips out of register for a moment | Text | Hiss |
| Fuse running out | The arc shortens, leaving dots behind, and in its last quarter swells and pulses | Length and shape | None |
| Progress through a word | Type blocks: a solid block is done, a framed block on a shadow is now, an outlined block is next | Fill, frame, and shadow | None |
| Result per letter (timed modes) | Block printed in red, blue, yellow, or grey | Dots under the letter (3 Perfect, 2 Good, 1 OK) and a strike for Miss | None |
| Letter mastery (menu alphabet) | A solid block is known, an outlined block with a dot under it is weak, a faint outline is untested | Fill and the dot, and the weak letters named on the Practise row | None |
| Unplayable menu row | Dimmed, with "Needs ..." | Text | None |
| Settings toggles (in the Settings panel) | "On" or "Off" in the label | Text | Click |
| J and Z path | Dashed guide with an arrowhead and a moving dot; the player's stroke as a trail | Shape and motion | None |

## Options

- **Finger colors (C):** each finger of the ghost and reference card gets its own tint from the Okabe-Ito palette, which stays distinct with common color blindness.
- **Motion (Settings):** turns off the rising dots, flying paper, screen shake, slipping plates, and the menu's drifting discs for anyone who finds motion uncomfortable. The print look and every cue stay.
- **Print camera (Settings):** off shows the plain camera picture instead of the three-ink print, for anyone who sees their hand better that way.
- **Sound (S):** every sound has a visible cue, so the game plays fully with sound off or without hearing.
- **Fullscreen (F)** and a resizable window for a larger view.
- **Keys panel (H):** every action is reachable by keyboard and by mouse.

## Other checks

- Smallest text is 18 px; play screens use 24 px and up.
- The ghost has a blue outer edge and a paper inner edge, so it stays visible on light and dark parts of the print. Ink drawn over the camera always has the picture knocked out to paper around it.
- No full-screen flashing. The beat pulse changes size, not brightness. Heat changes over about a second, never in a jump.
- Learn and Recall modes have no time limit.

## Known gaps

- Only one hand is tracked, and the player must be able to form handshapes with it.
- Strong backlight lowers tracking quality. Low light is warned about ("More light" with a sun icon), but backlight is not detected.
