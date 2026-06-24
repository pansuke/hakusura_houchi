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
    scope: Literal["local", "adjacent", "global"] = "local"
    damage_type: Literal["physical", "magic", "true"] = "true"
    base_damage: int | None = Field(default=None, ge=0)
    scaling: list[dict[str, int]] = Field(default_factory=list)


class BattleCardRequest(ApiSchema):
    card_id: str
    mp_cost: int = Field(ge=0)
    effects: list[BattleEffectRequest]
    consumes_action: bool = True


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
    lane_id: Literal["top", "mid", "bot"] | None = None
    ad: int = Field(default=0, ge=0)
    ap: int = Field(default=0, ge=0)
    ar: int = Field(default=0, ge=0)
    mr: int = Field(default=0, ge=0)
    push: int = Field(default=0, ge=0)


class BattleRuleConfigRequest(ApiSchema):
    initial_hand_size: int = Field(default=3, ge=0)
    max_hand_size: int = Field(default=7, ge=0)
    draw_gauge_threshold: int = Field(default=100, ge=1)
    respawn_skip_turns: int = Field(default=3, ge=0)
    ally_nexus_position: int = -1000
    enemy_nexus_position: int = 1000
    initial_position: int = 0
    nexus_max_hp: int = Field(default=8000, ge=1)
    nexus_ar: int = Field(default=0, ge=0)
    nexus_mr: int = Field(default=0, ge=0)
    defense_constant: int = Field(default=100, ge=1)


class BattleSimulateRequest(ApiSchema):
    battle_id: str
    participants: list[BattleParticipantRequest]
    turn_order: list[str]
    max_actions: int = Field(default=1000, ge=1, le=100000)
    seed: int = 0
    rule_config: BattleRuleConfigRequest = Field(default_factory=BattleRuleConfigRequest)


class BattleEventResponse(ApiSchema):
    event_id: int
    action_index: int
    sequence: int
    event_type: str
    actor_id: str | None
    target_id: str | None
    payload: dict[str, object]
    lane_id: Literal["top", "mid", "bot"] | None = None


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
    lane_id: Literal["top", "mid", "bot"] | None = None
    position: int | None = None
    push: int | None = None
    engaged_with_participant_id: str | None = None
    respawn_turns_remaining: int | None = None


class NexusSnapshotResponse(ApiSchema):
    side: Literal["ally", "enemy"]
    hp: int
    max_hp: int
    ar: int
    mr: int


class BattleRuleConfigResponse(ApiSchema):
    initial_hand_size: int
    max_hand_size: int
    draw_gauge_threshold: int
    respawn_skip_turns: int
    ally_nexus_position: int
    enemy_nexus_position: int
    initial_position: int
    nexus_max_hp: int
    nexus_ar: int
    nexus_mr: int
    defense_constant: int


class BattleSnapshotResponse(ApiSchema):
    action_index: int
    battle_status: Literal["running", "completed"]
    battle_result: Literal["undecided", "ally_win", "ally_loss", "draw"]
    acted_actor_id: str | None
    next_actor_id: str | None
    participants: dict[str, ParticipantSnapshotResponse]
    nexus_states: dict[str, NexusSnapshotResponse] = Field(default_factory=dict)
    applied_rule_config: BattleRuleConfigResponse | None = None


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
