from board_base import GO_POINT
from board import GoBoard

DEFAULT_KOMI = 6.5

class GoEngine:
    def __init__(self, name: str, version: float) -> None:
        """
        name : name of the player used by the GTP interface
        version : version number used by the GTP interface
        """
        self.name: str = name
        self.version: float = version
        self.komi: float = DEFAULT_KOMI
        self.policy_type:  str = "rule_based"

    def get_move(self, board: GoBoard, color: int) -> GO_POINT:
        """
        name : name of the player used by the GTP interface
        version : version number used by the GTP interface
        """
        pass
    def set_policy(self, policy_type: str) -> None:
        self.policy_type = policy_type

