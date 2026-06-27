import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

from fastapi import APIRouter, HTTPException

from lane_relay.api.schemas import (
    BattlePrototypeStatus,
    BattleReplayResponse,
    BattleSimulateRequest,
)
from lane_relay.engine.battle_engine import (
    BattleCard,
    BattleEffect,
    BattleEngine,
    BattleParticipantSetup,
    BattleRuleConfig,
    BattleScenario,
    BattleScenarioError,
    DamageType,
    EffectScope,
    EffectTarget,
    EffectType,
    LaneId,
    Side,
)

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("/prototype-status", response_model=BattlePrototypeStatus)
def get_battle_prototype_status() -> BattlePrototypeStatus:
    return BattlePrototypeStatus(
        engine="m3_ready",
        viewer_contract="m3_replay",
        note=(
            "BattleEngine supports three lanes, respawn, push, "
            "scoped cards and Nexus combat."
        ),
    )


@router.post("/simulate", response_model=BattleReplayResponse)
def simulate_battle(request: BattleSimulateRequest) -> dict[str, object]:
    try:
        replay = BattleEngine().simulate(to_scenario(request))
    except BattleScenarioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload = asdict(replay)
    payload["display_catalog"] = build_display_catalog(request, payload["display_catalog"])
    return payload


def to_scenario(request: BattleSimulateRequest) -> BattleScenario:
    return BattleScenario(
        battle_id=request.battle_id,
        participants=[
            BattleParticipantSetup(
                participant_id=participant.participant_id,
                side=cast(Side, participant.side),
                character_master_id=participant.character_master_id,
                max_hp=participant.max_hp,
                max_mp=participant.max_mp,
                initial_hp=participant.initial_hp,
                initial_mp=participant.initial_mp,
                ds=participant.ds,
                mpr=participant.mpr,
                hpr=participant.hpr,
                lane_id=cast(LaneId | None, participant.lane_id),
                ad=participant.ad,
                ap=participant.ap,
                ar=participant.ar,
                mr=participant.mr,
                push=participant.push,
                slot_type=participant.slot_type,
                trait_ids=tuple(participant.trait_ids),
                deck=[
                    BattleCard(
                        card_id=card.card_id,
                        mp_cost=card.mp_cost,
                        effects=[
                            BattleEffect(
                                effect_type=cast(EffectType, effect.effect_type),
                                target=cast(EffectTarget, effect.target),
                                value=effect.value,
                                scope=cast(EffectScope, effect.scope),
                                damage_type=cast(DamageType, effect.damage_type or "true"),
                                base_damage=effect.base_damage,
                                scaling=[
                                    scaling.model_dump() for scaling in effect.scaling
                                ],
                            )
                            for effect in card.effects
                        ],
                        support_enabled=card.support.enabled,
                        support_request_reduction=card.support.request_reduction,
                    )
                    for card in participant.deck
                ],
            )
            for participant in request.participants
        ],
        turn_order=request.turn_order,
        seed=request.seed,
        rule_config=BattleRuleConfig(
            initial_hand_size=request.rule_config.initial_hand_size,
            max_hand_size=request.rule_config.max_hand_size,
            draw_gauge_threshold=request.rule_config.draw_gauge_threshold,
            respawn_skip_turns=request.rule_config.respawn_skip_turns,
            ally_nexus_position=request.rule_config.ally_nexus_position,
            enemy_nexus_position=request.rule_config.enemy_nexus_position,
            initial_position=request.rule_config.initial_position,
            nexus_max_hp=request.rule_config.nexus_max_hp,
            nexus_ar=request.rule_config.nexus_ar,
            nexus_mr=request.rule_config.nexus_mr,
            defense_constant=request.rule_config.defense_constant,
            minimum_damage=request.rule_config.minimum_damage,
            simulation_safety_limit=request.rule_config.simulation_safety_limit,
            simulation_card_play_limit_per_action=(
                request.rule_config.simulation_card_play_limit_per_action
            ),
            support_request_max=request.rule_config.support_request_max,
            support_normal_effect_multiplier_bp=(
                request.rule_config.support_normal_effect_multiplier_bp
            ),
            support_normal_request_reduction=(
                request.rule_config.support_normal_request_reduction
            ),
        ),
    )


def build_display_catalog(
    request: BattleSimulateRequest,
    fallback_catalog: object,
) -> dict[str, object]:
    fallback = fallback_catalog if isinstance(fallback_catalog, dict) else {}
    fallback_cards = fallback.get("cards", {}) if isinstance(fallback.get("cards"), dict) else {}
    master_data = load_generated_master_data()
    characters = {
        character["id"]: character
        for character in master_data.get("characters", [])
        if isinstance(character, dict) and isinstance(character.get("id"), str)
    }
    cards = {
        card["id"]: card
        for card in master_data.get("cards", [])
        if isinstance(card, dict) and isinstance(card.get("id"), str)
    }

    return {
        "participants": {
            participant.participant_id: {
                "name": display_name_from_master(
                    characters.get(participant.character_master_id)
                ),
            }
            for participant in request.participants
        },
        "cards": {
            card.card_id: {
                "name": display_name_from_master(cards.get(card.card_id)),
                "mp_cost": master_card_mp_cost(cards.get(card.card_id), card.mp_cost),
                "description": fallback_card_description(fallback_cards, card.card_id),
            }
            for participant in request.participants
            for card in participant.deck
        },
    }


def load_generated_master_data() -> dict[str, object]:
    data_path = Path("/workspace/data/generated/game-data.json")
    if not data_path.exists():
        return {}
    with data_path.open(encoding="utf-8") as data_file:
        data = json.load(data_file)
    return data if isinstance(data, dict) else {}


def display_name_from_master(master: object) -> str:
    if isinstance(master, dict) and isinstance(master.get("name"), str):
        return master["name"]
    return "名称未設定"


def master_card_mp_cost(master: object, fallback: int) -> int:
    if isinstance(master, dict) and isinstance(master.get("mp_cost"), int):
        return master["mp_cost"]
    return fallback


def fallback_card_description(fallback_cards: object, card_id: str) -> str:
    if not isinstance(fallback_cards, dict):
        return ""
    card = fallback_cards.get(card_id)
    if isinstance(card, dict) and isinstance(card.get("description"), str):
        return card["description"]
    return ""
