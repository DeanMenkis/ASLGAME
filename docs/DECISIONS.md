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
