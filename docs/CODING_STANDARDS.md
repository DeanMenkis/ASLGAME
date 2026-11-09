# Coding Standards

Simple and concise, in both code and comments. Fast by default.

## Simplicity

- Write the plainest code that works. No clever tricks.
- Small functions that do one thing. If a name needs "and", split it.
- Prefer plain functions and small data classes over deep class trees.
- No abstraction until something is needed in at least two places.
- Delete dead code. Git remembers it.

## Comments

- Comment *why*, not *what*. The code says what.
- One line where possible. No essays, no banner blocks.
- Every module starts with a one-line docstring saying what it is for.
- No commented-out code.

## Naming

- Names say what a thing is. Avoid abbreviations except well-known ones.
- Units go in the name when it matters (`_ms`, `_px`, `_s`).
- Constants live in one config module, in caps. No magic numbers in logic.

## State

- Anything with modes or phases gets an explicit state machine.
- States are an `Enum`. Transitions happen in one place per machine.
- No hidden state in globals. Pass what a function needs.
- Each state handles its own input, update, and draw.

## Performance

- The frame loop is sacred. Nothing slow runs inside it.
- No disk, network, or model loading in the loop. Load once at startup.
- Slow work (camera, hand tracking) runs off the main thread and hands results over through a queue or latest-value slot.
- Never block the game loop waiting on tracking. Use the most recent result.
- Use NumPy for landmark math. No Python loops over points when a vector op works.
- Reuse buffers and surfaces. Avoid creating objects every frame.
- Measure before optimizing. Keep an on-screen FPS and latency readout in debug mode.

## Structure

- One module per concern. Folders follow the architecture doc.
- Game logic never imports the GUI, so it can be tested without a window.
- Tunable values go in config, not scattered through the code.

## Git

- Small commits with short, present-tense messages ("Add approach circle").
- `main` always runs. Work in short branches if more than one person is coding.
- Only commit media and models whose license allows it, and credit them in `docs/CREDITS.md`. Never commit personal recordings. See `.gitignore`.

## GUI

- Follow [Design](DESIGN.md).
- No emojis in code, strings, or comments.
- Layout values (grid, spacing, sizes, palette, fonts) come from one theme module.

## AI use

- AI-written code is allowed and must be disclosed in the credits doc.
- Commits made with Claude Code end with a `Co-Authored-By: Claude <noreply@anthropic.com>` line.
- Read and understand any AI-written code before committing it.
