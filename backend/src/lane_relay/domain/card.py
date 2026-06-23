from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    card_id: str
    name: str
