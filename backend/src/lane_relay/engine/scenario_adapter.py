from typing import cast

from lane_relay.engine.battle_engine import (
    BattleCard,
    BattleParticipantSetup,
    LaneId,
    Side,
)


def participant_from_character_master(
    *,
    participant_id: str,
    side: Side,
    lane_id: LaneId,
    character_master: dict[str, object],
    deck: list[BattleCard],
) -> BattleParticipantSetup:
    resources = _dict_value(character_master, "resources")
    action_resources = _dict_value(character_master, "action_resources")
    combat_stats = _dict_value(character_master, "combat_stats")
    max_hp = _int_value(resources, "max_hp")
    max_mp = _int_value(resources, "max_mp")
    initial_mp = _int_value(resources, "initial_mp")
    return BattleParticipantSetup(
        participant_id=participant_id,
        side=side,
        lane_id=lane_id,
        character_master_id=str(character_master["id"]),
        max_hp=max_hp,
        max_mp=max_mp,
        initial_hp=max_hp,
        initial_mp=min(initial_mp, max_mp),
        ds=_int_value(action_resources, "ds"),
        mpr=_int_value(action_resources, "mpr"),
        hpr=_int_value(action_resources, "hpr"),
        ad=_int_value(combat_stats, "ad"),
        ap=_int_value(combat_stats, "ap"),
        ar=_int_value(combat_stats, "ar"),
        mr=_int_value(combat_stats, "mr"),
        push=_int_value(combat_stats, "push"),
        deck=deck,
    )


def _dict_value(data: dict[str, object], key: str) -> dict[str, object]:
    value = data[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object.")
    return cast(dict[str, object], value)


def _int_value(data: dict[str, object], key: str) -> int:
    value = data[key]
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer.")
    return value
