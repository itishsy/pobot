from enum import Enum

class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check" # Note: CHECK is semantically different from CALL $0

class Action:
    def __init__(self, action_type: ActionType, amount: int = 0):
        self.type = action_type
        self.amount = amount # Relevant only for RAISE
