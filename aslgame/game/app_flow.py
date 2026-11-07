"""The top-level screen state machine."""

from enum import Enum, auto


class AppState(Enum):
    BOOT = auto()
    MENU = auto()
    LEARN = auto()
    PAUSED = auto()
    QUIT = auto()


class Action(Enum):
    READY = auto()
    START_LEARN = auto()
    PAUSE = auto()
    RESUME = auto()
    TO_MENU = auto()
    QUIT = auto()


TRANSITIONS = {
    (AppState.BOOT, Action.READY): AppState.MENU,
    (AppState.MENU, Action.START_LEARN): AppState.LEARN,
    (AppState.LEARN, Action.PAUSE): AppState.PAUSED,
    (AppState.LEARN, Action.TO_MENU): AppState.MENU,
    (AppState.PAUSED, Action.RESUME): AppState.LEARN,
    (AppState.PAUSED, Action.TO_MENU): AppState.MENU,
}


def next_state(state, action):
    """Return the state after action. Actions that do not apply leave the state unchanged."""
    if action == Action.QUIT:
        return AppState.QUIT
    return TRANSITIONS.get((state, action), state)
