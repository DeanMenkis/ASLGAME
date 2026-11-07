"""The top-level screen state machine."""

from enum import Enum, auto


class AppState(Enum):
    BOOT = auto()
    MENU = auto()
    LEARN = auto()
    RHYTHM = auto()
    RESULTS = auto()
    PAUSED = auto()
    QUIT = auto()


class Action(Enum):
    READY = auto()
    START_LEARN = auto()
    START_RHYTHM = auto()
    FINISH = auto()
    PAUSE = auto()
    RESUME = auto()
    TO_MENU = auto()
    QUIT = auto()


TRANSITIONS = {
    (AppState.BOOT, Action.READY): AppState.MENU,
    (AppState.MENU, Action.START_LEARN): AppState.LEARN,
    (AppState.MENU, Action.START_RHYTHM): AppState.RHYTHM,
    (AppState.LEARN, Action.PAUSE): AppState.PAUSED,
    (AppState.LEARN, Action.TO_MENU): AppState.MENU,
    (AppState.RHYTHM, Action.PAUSE): AppState.PAUSED,
    (AppState.RHYTHM, Action.FINISH): AppState.RESULTS,
    (AppState.RESULTS, Action.TO_MENU): AppState.MENU,
    (AppState.PAUSED, Action.TO_MENU): AppState.MENU,
}


def next_state(state, action, paused_from):
    """Return the state after action. Actions that do not apply leave the state unchanged."""
    if action == Action.QUIT:
        return AppState.QUIT
    if state == AppState.PAUSED and action == Action.RESUME:
        return paused_from
    return TRANSITIONS.get((state, action), state)
