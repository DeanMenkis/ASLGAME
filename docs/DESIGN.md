# Design

The interface should explain itself through form, not words. If a screen needs a paragraph to explain it, the design is wrong.

- No emojis anywhere, in the GUI, the code, or the docs.
- No extra headers, captions, or italic lines explaining what a control does. Labels are short and only where a symbol can't do the job.
- Meaning comes from symbols, layout, and motion. A shrinking ring means "now". A filled shape means "done". Position shows order.
- Contrast: one clear focal point per screen. The thing to do next is the strongest element.
- Repetition: the same idea always looks the same. One shape language, one type family, a small fixed palette.
- Alignment: everything sits on a grid. Nothing is placed by eye.
- Proximity: related things sit together, unrelated things are spaced apart.
- Feedback: every action gets an immediate visible response.
- Restraint: remove anything that doesn't help the player sign. Less, but better.
- Color is never the only signal (see [Architecture](ARCHITECTURE.md)).

## Art direction: the print shop

Fingerspelling is spelling, so the game is a press and the player is setting type. Everything on screen is uncoated paper and three spot inks, blue, red, and yellow, printed a little out of register. Nothing is black: the darkest color is blue printed over red. The look borrows from risograph gig posters and wood type broadsides, and puts a live camera inside them.

- **The camera is printed.** Shadows go to the blue plate, skin and warm things to the red, each as soft halftone dots. The player sees themself as a two-color print.
- **Color is the reward.** The multiplier is heat. As it climbs the yellow plate joins the print and the room turns full color, halftone dots rise from the bottom edge in one ink, then two, then three, and loose dots lift off. A miss is a misprint: the plates slip out of register, the yellow drops out, and the dots fall away.
- **Type is wood type.** Letters, numbers, and titles are a bold slab; labels are condensed capitals. Big type is printed twice, red under blue, so both plates show.
- **Panels are paper stickers** with a blue edge and a hard blue shadow, never soft. Buttons lift off their shadow when hovered or focused.
- **Timing is registration.** In Rhythm a red ring closes on the blue ring around the hand; when the two plates meet, that is the beat. The fuse in Music and Rush is an arc of ink that leaves dots where it has been.
- **The word strip is type blocks.** Each signed letter is printed in its judgement's ink, with dots and text as well as color.
- **The menu is a poster.** Flat discs of ink drift behind it, the camera sits in a proof frame with trim marks, and the letter it reads is set on a yellow star. The alphabet is a case of type: a solid block is a letter you know.
- **The results are a proof sheet.** The grade sits in a registration mark, and the words signed without a miss are printed as a broadside, each line stretched to the full measure, so every run ends with a poster of what was spelled.
- Ink drawn over the camera always has the picture knocked out to paper around it, so it reads on any room.
- Effects respect the Motion setting; with it off the print holds still. Print camera off shows the plain camera.

References:

- Don Norman, *The Design of Everyday Things*: affordances, signifiers, mapping, feedback
- Robin Williams, *The Non-Designer's Design Book*: contrast, repetition, alignment, proximity
- Dieter Rams, ten principles of good design: less, but better
- Josef Müller-Brockmann, *Grid Systems in Graphic Design*: layout on a grid
- Lidwell, Holden and Butler, *Universal Principles of Design*: general reference
- Steve Krug, *Don't Make Me Think*: self-evident interfaces
