from enum import Enum

class Stage(Enum):
    """Allowed actions"""
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END_HIDDEN = 4
    SHOWDOWN = 5