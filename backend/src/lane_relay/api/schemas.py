from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiSchema(BaseModel):
    model_config = ConfigDict(frozen=True)


class HealthResponse(ApiSchema):
    status: str
    service: str


class BattlePrototypeStatus(ApiSchema):
    engine: str
    viewer_contract: str
    note: str


class MasterDataStatus(ApiSchema):
    source_dir: str
    generated_file: str


class BattleEffectRequest(ApiSchema):
    effect_type: Literal["damage", "heal", "gain_mana", "draw_card"]
    target: Literal["self", "enemy"]
    value: int = Field(ge=1)


class BattleCardRequest(ApiSchema):
    card_id: str
    mp_cost: int = Field(ge=0)
    effects: list[BattleEffectRequest]


class BattleParticipantRequest(ApiSchema):
    participant_id: str
    side: Literal["ally", "enemy"]
    character_master_id: str
    max_hp: int = Field(ge=1)
    max_mp: int = Field(ge=0)
    initial_hp: int = Field(ge=1)
    initial_mp: int = Field(ge=0)
    ds: int = Field(ge=0)
    mrg: int = Field(ge=0)
    hrg: int = Field(ge=0)
    deck: list[BattleCardRequest]


class BattleSimulateRequest(ApiSchema):
    battle_id: str
    participants: list[BattleParticipantRequest]
    turn_order: list[str]
    max_actions: int = Field(default=1000, ge=1, le=100000)
    seed: int = 0
