# Accessibility

Audit of every cue in the game against the rules in the architecture doc: nothing that matters is sound-only or color-only.

## Cues

| Cue | Visible form | Not color alone because | Sound |
| --- | --- | --- | --- |
| Target sign | Silhouette over the hand and a large picture on the reference card | Shape | None |
| Sign matched | Silhouette fills, "Hold it" label, card bar fills | Fill, text, and motion | Chime when confirmed |
| Fingers to fix | Fingers traced on the player's hand, names listed under the card | Finger names in text | None |
| Timing | Ring closing on the palm, beat pulse growing and shrinking | Size and motion | Music beat (optional) |
| Judgement | A seal stamp reading "PERFECT", "GOOD", "OK", or "MISS" by the hand | Text | Distinct sound per judgement |
| Score and multiplier | Rolling score and "x2.4" in the top bar, "+300" pops on each hit | Text and motion | None |
| Combo milestone | "10 combo" banner | Text | Sparkle |
| Heat (multiplier) | Ink warms to vermilion, ember, gold; fire rises from the bottom | The multiplier number is always shown | Crackle, whoosh |
| Fire put out by a miss | "x5 out" banner, smoke, falling ash, a dimmed camera | Text | Hiss |
| Fuse running out | The stroke shortens and, in its last quarter, swells and pulses | Length and shape | None |
| Progress through a word | Strip cells: filled is done, thick outline is now, thin outline is next | Fill and line weight | None |
| Result per letter (rhythm, music) | Strip cell in green, yellow, orange, or red | Dots under the letter (3 Perfect, 2 Good, 1 OK) and a strike for Miss | None |
| Unplayable menu row | Dimmed, with "Needs ..." | Text | None |
| Settings toggles (in the Settings panel) | "On" or "Off" in the label | Text | Click |
| J and Z path | Dashed guide with an arrowhead and a moving dot; the player's stroke as a trail | Shape and motion | None |

## Options

- **Finger colors (C):** each finger of the ghost and reference card gets its own tint from the Okabe-Ito palette, which stays distinct with common color blindness.
- **Fire (Settings):** turns off flames, smoke, ash, and screen shake for anyone who finds motion uncomfortable. The ink look and every cue stay.
- **Sound (S):** every sound has a visible cue, so the game plays fully with sound off or without hearing.
- **Fullscreen (F)** and a resizable window for a larger view.
- **Keys panel (H):** every action is reachable by keyboard and by mouse.

## Other checks

- Smallest text is 18 px; play screens use 24 px and up.
- The ghost has a dark outer edge and a light inner edge, so it stays visible on light and dark backgrounds.
- No full-screen flashing. The beat pulse changes size, not brightness. Heat changes over about a second, never in a jump, and the fire flickers locally rather than flashing.
- Learn and Recall modes have no time limit.

## Known gaps

- Only one hand is tracked, and the player must be able to form handshapes with it.
- Strong backlight lowers tracking quality. Low light is warned about ("More light" with a sun icon), but backlight is not detected.
