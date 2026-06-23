from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    character_id: str
    name: str
