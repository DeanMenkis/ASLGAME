"""The top-level screen state machine."""

from enum import Enum, auto


class AppState(Enum):
    BOOT = auto()
    MENU = auto()
    LEARN = auto()
    RECALL = auto()
    RHYTHM = auto()
    MUSIC = auto()
    RUSH = auto()
    RESULTS = auto()
    PAUSED = auto()
    QUIT = auto()


class Action(Enum):
    READY = auto()
    START_LEARN = auto()
    START_RECALL = auto()
    START_RHYTHM = auto()
    START_MUSIC = auto()
    START_RUSH = auto()
    RETRY = auto()
    FINISH = auto()
    PAUSE = auto()
    RESUME = auto()
    TO_MENU = auto()
    QUIT = auto()


PLAY_STATES = (AppState.LEARN, AppState.RECALL, AppState.RHYTHM, AppState.MUSIC, AppState.RUSH)
TIMED_STATES = (AppState.RHYTHM, AppState.MUSIC, AppState.RUSH)

TRANSITIONS = {
    (AppState.BOOT, Action.READY): AppState.MENU,
    (AppState.MENU, Action.START_LEARN): AppState.LEARN,
    (AppState.MENU, Action.START_RECALL): AppState.RECALL,
    (AppState.MENU, Action.START_RHYTHM): AppState.RHYTHM,
    (AppState.MENU, Action.START_MUSIC): AppState.MUSIC,
    (AppState.LEARN, Action.PAUSE): AppState.PAUSED,
    (AppState.LEARN, Action.TO_MENU): AppState.MENU,
    (AppState.RECALL, Action.PAUSE): AppState.PAUSED,
    (AppState.RECALL, Action.TO_MENU): AppState.MENU,
    (AppState.RHYTHM, Action.PAUSE): AppState.PAUSED,
    (AppState.RHYTHM, Action.FINISH): AppState.RESULTS,
    (AppState.MUSIC, Action.PAUSE): AppState.PAUSED,
    (AppState.MUSIC, Action.FINISH): AppState.RESULTS,
    (AppState.MENU, Action.START_RUSH): AppState.RUSH,
    (AppState.RUSH, Action.PAUSE): AppState.PAUSED,
    (AppState.RUSH, Action.FINISH): AppState.RESULTS,
    (AppState.RESULTS, Action.TO_MENU): AppState.MENU,
    (AppState.PAUSED, Action.TO_MENU): AppState.MENU,
}


def next_state(state, action, play_state):
    """Return the state after action. play_state is the mode being played, used to resume and retry.

    Actions that do not apply leave the state unchanged.
    """
    if action == Action.QUIT:
        return AppState.QUIT
    if (state, action) in ((AppState.PAUSED, Action.RESUME), (AppState.RESULTS, Action.RETRY)):
        return play_state
    return TRANSITIONS.get((state, action), state)
