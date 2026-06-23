from dataclasses import asdict
from typing import cast

from fastapi import APIRouter, HTTPException

from lane_relay.api.schemas import BattlePrototypeStatus, BattleSimulateRequest
from lane_relay.engine.battle_engine import (
    BattleCard,
    BattleEffect,
    BattleEngine,
    BattleParticipantSetup,
    BattleScenario,
    BattleScenarioError,
    EffectTarget,
    EffectType,
    Side,
)

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("/prototype-status", response_model=BattlePrototypeStatus)
def get_battle_prototype_status() -> BattlePrototypeStatus:
    return BattlePrototypeStatus(
        engine="m1_ready",
        viewer_contract="m2_replay",
        note="BattleEngine runs stateless M1 simulations and returns replay data.",
    )


@router.post("/simulate")
def simulate_battle(request: BattleSimulateRequest) -> dict[str, object]:
    try:
        replay = BattleEngine().simulate(to_scenario(request))
    except BattleScenarioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return asdict(replay)


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
                deck=[
                    BattleCard(
                        card_id=card.card_id,
                        mp_cost=card.mp_cost,
                        effects=[
                            BattleEffect(
                                effect_type=cast(EffectType, effect.effect_type),
                                target=cast(EffectTarget, effect.target),
                                value=effect.value,
                            )
                            for effect in card.effects
                        ],
                    )
                    for card in participant.deck
                ],
            )
            for participant in request.participants
        ],
        turn_order=request.turn_order,
        max_actions=request.max_actions,
        seed=request.seed,
    )
