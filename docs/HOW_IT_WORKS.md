# How It Works

ASLGAME is a desktop game written in **Python**. It runs entirely on the laptop: no server, no internet.

1. **Camera:** OpenCV reads the webcam.
2. **Tracking:** Google's MediaPipe finds 21 points on your hand.
3. **Normalize:** the points are moved, scaled, and mirrored so position, distance, and left or right hand don't matter.
4. **Match:** NumPy compares your points to recorded examples of each letter from a public dataset. Close enough, held briefly, counts. J and Z also check the path your fingertip draws.
5. **Game:** pygame draws everything and plays sound. Score grows with combo, accuracy, and speed.

Camera and tracking run on background threads, so the game stays at 60 FPS.

Tunable numbers live in `config.py`, visual values in `theme.py`.
