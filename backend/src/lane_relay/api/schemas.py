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
    mpr: int = Field(ge=0)
    hpr: int = Field(ge=0)
    deck: list[BattleCardRequest]


class BattleSimulateRequest(ApiSchema):
    battle_id: str
    participants: list[BattleParticipantRequest]
    turn_order: list[str]
    max_actions: int = Field(default=1000, ge=1, le=100000)
    seed: int = 0


class BattleEventResponse(ApiSchema):
    event_id: int
    action_index: int
    sequence: int
    event_type: str
    actor_id: str | None
    target_id: str | None
    payload: dict[str, object]


class ParticipantSnapshotResponse(ApiSchema):
    participant_id: str
    character_master_id: str
    side: Literal["ally", "enemy"]
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    alive: bool
    ds: int
    mpr: int
    hpr: int
    draw_gauge: int
    hand: list[str]
    draw_pile: list[str]
    discard_pile: list[str]


class BattleSnapshotResponse(ApiSchema):
    action_index: int
    battle_status: Literal["running", "completed"]
    battle_result: Literal["undecided", "ally_win", "ally_loss", "draw"]
    acted_actor_id: str | None
    next_actor_id: str | None
    participants: dict[str, ParticipantSnapshotResponse]


class ParticipantSummaryResponse(ApiSchema):
    participant_id: str
    side: Literal["ally", "enemy"]
    hp: int
    mp: int
    alive: bool
    damage_dealt: int
    damage_taken: int
    cards_used: int


class BattleSummaryResponse(ApiSchema):
    battle_id: str
    status: Literal["running", "completed"]
    result: Literal["undecided", "ally_win", "ally_loss", "draw"]
    end_reason: str
    action_count: int
    event_count: int
    snapshot_count: int
    participants: dict[str, ParticipantSummaryResponse]


class DisplayParticipantResponse(ApiSchema):
    name: str


class DisplayCardResponse(ApiSchema):
    name: str
    mp_cost: int
    description: str


class DisplayCatalogResponse(ApiSchema):
    participants: dict[str, DisplayParticipantResponse]
    cards: dict[str, DisplayCardResponse]


class BattleReplayResponse(ApiSchema):
    events: list[BattleEventResponse]
    snapshots: list[BattleSnapshotResponse]
    summary: BattleSummaryResponse
    display_catalog: DisplayCatalogResponse
