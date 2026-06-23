from dataclasses import dataclass


@dataclass(frozen=True)
class BattleState:
    action_index: int = 0
