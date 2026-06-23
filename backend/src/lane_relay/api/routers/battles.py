from fastapi import APIRouter

from lane_relay.api.schemas import BattlePrototypeStatus

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("/prototype-status", response_model=BattlePrototypeStatus)
def get_battle_prototype_status() -> BattlePrototypeStatus:
    return BattlePrototypeStatus(
        engine="not_implemented",
        viewer_contract="pending",
        note="BattleEngine is intentionally outside the M0 infrastructure scope.",
    )
