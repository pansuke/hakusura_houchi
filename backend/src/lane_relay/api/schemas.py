from pydantic import BaseModel, ConfigDict


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
    effect_type: str
    target: str
    value: int


class BattleCardRequest(ApiSchema):
    card_id: str
    mp_cost: int
    effects: list[BattleEffectRequest]


class BattleParticipantRequest(ApiSchema):
    participant_id: str
    side: str
    character_master_id: str
    max_hp: int
    max_mp: int
    initial_hp: int
    initial_mp: int
    ds: int
    mrg: int
    hrg: int
    deck: list[BattleCardRequest]


class BattleSimulateRequest(ApiSchema):
    battle_id: str
    participants: list[BattleParticipantRequest]
    turn_order: list[str]
    max_actions: int = 1000
    seed: int = 0
