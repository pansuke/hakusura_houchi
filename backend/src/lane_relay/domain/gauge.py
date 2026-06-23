from dataclasses import dataclass


@dataclass(frozen=True)
class Gauge:
    value: int
    threshold: int = 100
