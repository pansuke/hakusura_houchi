from __future__ import annotations

import random
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

Side = Literal["ally", "enemy"]
BattleStatus = Literal["running", "completed"]
BattleResult = Literal["undecided", "ally_win", "ally_loss", "draw"]
EffectType = Literal[
    "damage",
    "heal",
    "gain_mana",
    "draw_card",
    "grant_card_play",
    "add_support_request",
    "gain_draw_gauge",
]
EffectTarget = Literal["self", "enemy"]
LaneId = Literal["top", "mid", "bot"]
SlotType = Literal["lane", "support"]
DamageType = Literal["physical", "magic", "true"]
EffectScope = Literal["local", "adjacent", "global"]

GAUGE_THRESHOLD = 100
HAND_LIMIT = 5
INITIAL_HAND_SIZE = 3
M3_LANE_ORDER: tuple[LaneId, ...] = ("top", "mid", "bot")
M3_TURN_SLOTS: tuple[tuple[LaneId, Side], ...] = (
    ("top", "ally"),
    ("top", "enemy"),
    ("mid", "ally"),
    ("mid", "enemy"),
    ("bot", "ally"),
    ("bot", "enemy"),
)
M4_TURN_SLOTS: tuple[tuple[LaneId | Literal["support"], Side], ...] = (
    *M3_TURN_SLOTS,
    ("support", "ally"),
    ("support", "enemy"),
)
ALLOWED_EFFECT_TYPES: set[str] = {
    "damage",
    "heal",
    "gain_mana",
    "draw_card",
    "grant_card_play",
    "add_support_request",
    "gain_draw_gauge",
}
ALLOWED_EFFECT_TARGETS: set[str] = {"self", "enemy"}
ALLOWED_EFFECT_SCOPES: set[str] = {"local", "adjacent", "global"}
ALLOWED_DAMAGE_TYPES: set[str] = {"physical", "magic", "true"}


class BattleScenarioError(ValueError):
    pass


@dataclass(frozen=True)
class BattleEffect:
    effect_type: EffectType
    target: EffectTarget
    value: int
    scope: EffectScope = "local"
    damage_type: DamageType = "true"
    base_damage: int | None = None
    scaling: list[dict[str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class BattleCard:
    card_id: str
    mp_cost: int
    effects: list[BattleEffect]
    support_enabled: bool = False
    support_request_reduction: int = 0


@dataclass(frozen=True)
class BattleParticipantSetup:
    participant_id: str
    side: Side
    character_master_id: str
    max_hp: int
    max_mp: int
    initial_hp: int
    initial_mp: int
    ds: int
    mpr: int
    hpr: int
    deck: list[BattleCard]
    lane_id: LaneId | None = None
    ad: int = 0
    ap: int = 0
    ar: int = 0
    mr: int = 0
    push: int = 0
    slot_type: SlotType = "lane"
    trait_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BattleRuleConfig:
    initial_hand_size: int = 3
    max_hand_size: int = 7
    draw_gauge_threshold: int = 100
    respawn_skip_turns: int = 3
    ally_nexus_position: int = -1000
    enemy_nexus_position: int = 1000
    initial_position: int = 0
    nexus_max_hp: int = 8000
    nexus_ar: int = 0
    nexus_mr: int = 0
    defense_constant: int = 100
    minimum_damage: int = 1
    simulation_safety_limit: int = 1000
    simulation_card_play_limit_per_action: int = 100
    support_request_max: int = 9
    support_normal_effect_multiplier_bp: int = 1000
    support_normal_request_reduction: int = 1


@dataclass(frozen=True)
class BattleScenario:
    battle_id: str
    participants: list[BattleParticipantSetup]
    turn_order: list[str]
    seed: int = 0
    rule_config: BattleRuleConfig = field(default_factory=BattleRuleConfig)


@dataclass(frozen=True)
class BattleEvent:
    event_id: int
    action_index: int
    sequence: int
    event_type: str
    actor_id: str | None
    target_id: str | None
    payload: dict[str, object]
    lane_id: LaneId | None = None


@dataclass(frozen=True)
class ParticipantSnapshot:
    participant_id: str
    character_master_id: str
    side: Side
    slot_type: SlotType
    hp: int | None
    max_hp: int | None
    mp: int
    max_mp: int
    alive: bool | None
    ds: int
    mpr: int
    hpr: int | None
    ad: int
    ap: int
    ar: int
    mr: int
    draw_gauge: int
    hand: list[str]
    draw_pile: list[str]
    discard_pile: list[str]
    lane_id: LaneId | None = None
    position: int | None = None
    push: int | None = None
    engaged_with_participant_id: str | None = None
    respawn_turns_remaining: int | None = None
    trait_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NexusSnapshot:
    side: Side
    hp: int
    max_hp: int
    ar: int
    mr: int


@dataclass(frozen=True)
class BattleSnapshot:
    action_index: int
    battle_status: BattleStatus
    battle_result: BattleResult
    acted_actor_id: str | None
    next_actor_id: str | None
    participants: dict[str, ParticipantSnapshot]
    nexus_states: dict[str, NexusSnapshot] = field(default_factory=dict)
    support_requests: dict[Side, dict[LaneId, int]] = field(default_factory=dict)
    applied_rule_config: BattleRuleConfig | None = None


@dataclass(frozen=True)
class ParticipantSummary:
    participant_id: str
    side: Side
    hp: int | None
    mp: int
    alive: bool | None
    damage_dealt: int
    damage_taken: int
    cards_used: int


@dataclass(frozen=True)
class BattleSummary:
    battle_id: str
    status: BattleStatus
    result: BattleResult
    end_reason: str
    action_count: int
    event_count: int
    snapshot_count: int
    participants: dict[str, ParticipantSummary]


@dataclass(frozen=True)
class BattleReplay:
    events: list[BattleEvent]
    snapshots: list[BattleSnapshot]
    summary: BattleSummary
    display_catalog: dict[str, object]


@dataclass
class ParticipantRuntime:
    setup: BattleParticipantSetup
    hp: int | None
    mp: int
    alive: bool | None
    draw_gauge: int = 0
    hand: list[BattleCard] = field(default_factory=list)
    draw_pile: list[BattleCard] = field(default_factory=list)
    discard_pile: list[BattleCard] = field(default_factory=list)
    defeated_event_emitted: bool = False
    damage_dealt: int = 0
    damage_taken: int = 0
    cards_used: int = 0
    lane_id: LaneId | None = None
    position: int | None = None
    engaged_with_participant_id: str | None = None
    respawn_turns_remaining: int | None = None
    shuffle_count: int = 0
    initial_shuffle_count: int = 0
    recycle_shuffle_count: int = 0
    respawn_shuffle_count: int = 0


@dataclass
class BattleRuntime:
    scenario: BattleScenario
    participants: dict[str, ParticipantRuntime]
    action_index: int = 0
    current_turn_index: int = 0
    battle_status: BattleStatus = "running"
    battle_result: BattleResult = "undecided"
    end_reason: str = "running"
    nexus_states: dict[str, NexusSnapshot] = field(default_factory=dict)
    rule_config: BattleRuleConfig | None = None
    adjacent_selection_count: int = 0
    support_lane_selection_count: dict[Side, int] = field(
        default_factory=lambda: {"ally": 0, "enemy": 0}
    )
    support_requests: dict[Side, dict[LaneId, int]] = field(
        default_factory=lambda: {
            "ally": {"top": 0, "mid": 0, "bot": 0},
            "enemy": {"top": 0, "mid": 0, "bot": 0},
        }
    )


class EventRecorder:
    def __init__(self) -> None:
        self.events: list[BattleEvent] = []
        self._next_event_id = 1
        self._sequence_by_action: dict[int, int] = {}

    def record(
        self,
        action_index: int,
        event_type: str,
        actor_id: str | None = None,
        target_id: str | None = None,
        payload: dict[str, object] | None = None,
        lane_id: LaneId | None = None,
    ) -> None:
        sequence = self._sequence_by_action.get(action_index, 0) + 1
        self._sequence_by_action[action_index] = sequence
        self.events.append(
            BattleEvent(
                event_id=self._next_event_id,
                action_index=action_index,
                sequence=sequence,
                event_type=event_type,
                actor_id=actor_id,
                target_id=target_id,
                payload=payload or {},
                lane_id=lane_id,
            )
        )
        self._next_event_id += 1


class BattleEngine:
    def simulate(self, scenario: BattleScenario) -> BattleReplay:
        if self._is_m3_scenario(scenario):
            return self._simulate_m3(scenario)
        self._validate_scenario(scenario)
        runtime = self._create_runtime(scenario)
        recorder = EventRecorder()
        snapshots = [self._snapshot(runtime, acted_actor_id=None)]
        recorder.record(
            action_index=0,
            event_type="battle_started",
            payload={"battle_id": scenario.battle_id, "seed": scenario.seed},
        )

        while runtime.battle_status == "running":
            if runtime.action_index >= scenario.rule_config.simulation_safety_limit:
                self._complete_battle(runtime, recorder, "draw", "simulation_safety_limit")
                snapshots.append(self._snapshot(runtime, acted_actor_id=None))
                break
            actor_id = self._active_actor_id(runtime)
            if actor_id is None:
                self._complete_battle(runtime, recorder, "draw", "no_actor")
                snapshots.append(self._snapshot(runtime, acted_actor_id=None))
                break
            runtime.action_index += 1
            self._run_action(runtime, recorder, actor_id)
            acted_actor_id = actor_id
            if runtime.battle_status == "running":
                self._advance_turn(runtime)
            snapshots.append(self._snapshot(runtime, acted_actor_id=acted_actor_id))

        return BattleReplay(
            events=recorder.events,
            snapshots=snapshots,
            summary=self._summary(runtime, recorder, snapshots),
            display_catalog=self._display_catalog(scenario),
        )

    def _is_m3_scenario(self, scenario: BattleScenario) -> bool:
        return len(scenario.participants) == 6 or any(
            participant.lane_id is not None for participant in scenario.participants
        )

    def _validate_scenario(self, scenario: BattleScenario) -> None:
        if scenario.rule_config.simulation_safety_limit < 1:
            raise BattleScenarioError(
                "simulation_safety_limit must be greater than or equal to 1."
            )
        if self._is_m3_scenario(scenario):
            self._validate_m3_scenario(scenario)
            return
        if len(scenario.participants) != 2:
            raise BattleScenarioError("M1 scenario must have exactly two participants.")
        participant_ids = [participant.participant_id for participant in scenario.participants]
        if len(set(participant_ids)) != 2:
            raise BattleScenarioError("participant_id must be unique.")
        sides = {participant.side for participant in scenario.participants}
        if sides != {"ally", "enemy"}:
            raise BattleScenarioError("M1 scenario must have one ally and one enemy.")
        if (
            len(scenario.turn_order) != len(participant_ids)
            or len(set(scenario.turn_order)) != len(scenario.turn_order)
            or set(scenario.turn_order) != set(participant_ids)
        ):
            raise BattleScenarioError(
                "turn_order must contain every participant_id exactly once."
            )
        for participant in scenario.participants:
            if not participant.deck:
                raise BattleScenarioError("deck must not be empty.")
            if participant.initial_hp < 1 or participant.initial_hp > participant.max_hp:
                raise BattleScenarioError("initial_hp must be between 1 and max_hp.")
            if participant.initial_mp < 0 or participant.initial_mp > participant.max_mp:
                raise BattleScenarioError("initial_mp must be between 0 and max_mp.")
            if participant.ds < 0:
                raise BattleScenarioError("ds must be greater than or equal to 0.")
            if participant.mpr < 0:
                raise BattleScenarioError("mpr must be greater than or equal to 0.")
            if participant.hpr < 0:
                raise BattleScenarioError("hpr must be greater than or equal to 0.")
            for card in participant.deck:
                if card.mp_cost < 0:
                    raise BattleScenarioError("card mp_cost must be greater than or equal to 0.")
                if not card.effects:
                    raise BattleScenarioError("card effects must not be empty.")
                for effect in card.effects:
                    if effect.effect_type not in ALLOWED_EFFECT_TYPES:
                        raise BattleScenarioError("effect_type must be supported.")
                    if effect.target not in ALLOWED_EFFECT_TARGETS:
                        raise BattleScenarioError("effect target must be supported.")
                    if effect.value < 0:
                        raise BattleScenarioError(
                            "effect value must be greater than or equal to 0."
                        )
                    if effect.scope not in ALLOWED_EFFECT_SCOPES:
                        raise BattleScenarioError("effect scope must be supported.")
                    if effect.damage_type not in ALLOWED_DAMAGE_TYPES:
                        raise BattleScenarioError("damage_type must be supported.")
                    if effect.base_damage is not None and effect.base_damage < 0:
                        raise BattleScenarioError(
                            "base_damage must be greater than or equal to 0."
                        )
                    self._validate_effect_specific_fields(effect)

    def _validate_m3_scenario(self, scenario: BattleScenario) -> None:
        if len(scenario.participants) not in {6, 8}:
            raise BattleScenarioError("M3/M4 scenario must have six or eight participants.")
        participant_ids = [participant.participant_id for participant in scenario.participants]
        if len(set(participant_ids)) != len(participant_ids):
            raise BattleScenarioError("participant_id must be unique.")
        by_slot = {
            (
                "support" if participant.slot_type == "support" else participant.lane_id,
                participant.side,
            ): participant
            for participant in scenario.participants
        }
        turn_slots = M4_TURN_SLOTS if len(scenario.participants) == 8 else M3_TURN_SLOTS
        expected_slots = set(turn_slots)
        if set(by_slot) != expected_slots:
            raise BattleScenarioError(
                "scenario must contain ally and enemy for every configured slot."
            )
        expected_turn_order = [
            by_slot[(lane_id, side)].participant_id for lane_id, side in turn_slots
        ]
        if scenario.turn_order != expected_turn_order:
            raise BattleScenarioError(
                "turn_order must follow top/mid/bot and optional support fixed slots."
            )
        config = scenario.rule_config
        if (
            config.initial_hand_size < 0
            or config.max_hand_size < 1
            or config.max_hand_size < config.initial_hand_size
        ):
            raise BattleScenarioError("invalid hand size rule config.")
        if config.draw_gauge_threshold < 1:
            raise BattleScenarioError("draw_gauge_threshold must be greater than 0.")
        if config.respawn_skip_turns < 0:
            raise BattleScenarioError("respawn_skip_turns must be greater than or equal to 0.")
        if config.nexus_max_hp < 1:
            raise BattleScenarioError("nexus_max_hp must be greater than 0.")
        if config.defense_constant < 1:
            raise BattleScenarioError("defense_constant must be greater than 0.")
        if config.minimum_damage < 1:
            raise BattleScenarioError("minimum_damage must be greater than 0.")
        if config.simulation_safety_limit < 1:
            raise BattleScenarioError("simulation_safety_limit must be greater than 0.")
        if config.simulation_card_play_limit_per_action < 1:
            raise BattleScenarioError(
                "simulation_card_play_limit_per_action must be greater than 0."
            )
        if config.support_request_max < 1:
            raise BattleScenarioError("support_request_max must be greater than 0.")
        if not 0 <= config.support_normal_effect_multiplier_bp <= 10000:
            raise BattleScenarioError(
                "support_normal_effect_multiplier_bp must be between 0 and 10000."
            )
        if config.support_normal_request_reduction < 0:
            raise BattleScenarioError(
                "support_normal_request_reduction must be greater than or equal to 0."
            )
        if not (
            config.ally_nexus_position
            < config.initial_position
            < config.enemy_nexus_position
        ):
            raise BattleScenarioError("nexus positions must contain initial_position.")
        for participant in scenario.participants:
            if not participant.deck:
                raise BattleScenarioError("deck must not be empty.")
            if participant.slot_type == "support":
                if participant.lane_id is not None:
                    raise BattleScenarioError("support must not have lane_id.")
            elif participant.initial_hp < 1 or participant.initial_hp > participant.max_hp:
                raise BattleScenarioError("initial_hp must be between 1 and max_hp.")
            if participant.initial_mp < 0 or participant.initial_mp > participant.max_mp:
                raise BattleScenarioError("initial_mp must be between 0 and max_mp.")
            combat_stats = (
                participant.ds,
                participant.mpr,
                0 if participant.slot_type == "support" else participant.hpr,
                participant.ad,
                participant.ap,
                participant.ar,
                participant.mr,
                participant.push,
            )
            if min(combat_stats) < 0:
                raise BattleScenarioError("combat stats must be greater than or equal to 0.")
            for card in participant.deck:
                if card.mp_cost < 0:
                    raise BattleScenarioError("card mp_cost must be greater than or equal to 0.")
                if not card.effects:
                    raise BattleScenarioError("card effects must not be empty.")
                if card.support_request_reduction < 0:
                    raise BattleScenarioError(
                        "support_request_reduction must be greater than or equal to 0."
                    )
                if not card.support_enabled and card.support_request_reduction:
                    raise BattleScenarioError(
                        "normal card must not define support_request_reduction."
                    )
                for effect in card.effects:
                    if effect.effect_type not in ALLOWED_EFFECT_TYPES:
                        raise BattleScenarioError("effect_type must be supported.")
                    if effect.target not in ALLOWED_EFFECT_TARGETS:
                        raise BattleScenarioError("effect target must be supported.")
                    if effect.scope not in ALLOWED_EFFECT_SCOPES:
                        raise BattleScenarioError("effect scope must be supported.")
                    if effect.damage_type not in ALLOWED_DAMAGE_TYPES:
                        raise BattleScenarioError("damage_type must be supported.")
                    if effect.value < 0:
                        raise BattleScenarioError(
                            "effect value must be greater than or equal to 0."
                        )
                    if effect.base_damage is not None and effect.base_damage < 0:
                        raise BattleScenarioError(
                            "base_damage must be greater than or equal to 0."
                        )
                    if effect.target == "self" and effect.scope != "local":
                        raise BattleScenarioError("self target effects must use local scope.")
                    self._validate_effect_specific_fields(effect)

    def _validate_effect_specific_fields(self, effect: BattleEffect) -> None:
        allowed_scaling_stats = {"ad", "ap", "max_hp", "current_hp", "missing_hp"}
        if len(effect.scaling) > 8:
            raise BattleScenarioError("scaling must contain at most 8 entries.")
        for scaling in effect.scaling:
            if scaling.get("stat") not in allowed_scaling_stats:
                raise BattleScenarioError("scaling stat must be supported.")
            if scaling.get("ratio_bp", 0) < 0:
                raise BattleScenarioError("scaling ratio_bp must be greater than or equal to 0.")
        if effect.effect_type == "damage":
            return
        if effect.base_damage is not None:
            raise BattleScenarioError("base_damage is only allowed for damage effects.")
        if effect.damage_type != "true":
            raise BattleScenarioError("damage_type is only allowed for damage effects.")
        if effect.scaling:
            raise BattleScenarioError("scaling is only allowed for damage effects.")

    def _simulate_m3(self, scenario: BattleScenario) -> BattleReplay:
        self._validate_m3_scenario(scenario)
        runtime = self._create_m3_runtime(scenario)
        recorder = EventRecorder()
        snapshots = [self._snapshot(runtime, acted_actor_id=None)]
        recorder.record(
            action_index=0,
            event_type="battle_started",
            payload={
                "battle_id": scenario.battle_id,
                "seed": scenario.seed,
                "rule_config": self._rule_config_payload(scenario.rule_config),
            },
        )

        while runtime.battle_status == "running":
            if runtime.action_index >= scenario.rule_config.simulation_safety_limit:
                raise BattleScenarioError("simulation_safety_limit reached.")
            actor_id = scenario.turn_order[runtime.current_turn_index]
            runtime.action_index += 1
            self._run_m3_action(runtime, recorder, actor_id)
            snapshots.append(self._snapshot(runtime, acted_actor_id=actor_id))
            if runtime.battle_status == "running":
                runtime.current_turn_index = (runtime.current_turn_index + 1) % len(
                    scenario.turn_order
                )

        return BattleReplay(
            events=recorder.events,
            snapshots=snapshots,
            summary=self._summary(runtime, recorder, snapshots),
            display_catalog=self._display_catalog(scenario),
        )

    def _rule_config_payload(self, config: BattleRuleConfig) -> dict[str, int]:
        return {
            "initial_hand_size": config.initial_hand_size,
            "max_hand_size": config.max_hand_size,
            "draw_gauge_threshold": config.draw_gauge_threshold,
            "respawn_skip_turns": config.respawn_skip_turns,
            "ally_nexus_position": config.ally_nexus_position,
            "enemy_nexus_position": config.enemy_nexus_position,
            "initial_position": config.initial_position,
            "nexus_max_hp": config.nexus_max_hp,
            "nexus_ar": config.nexus_ar,
            "nexus_mr": config.nexus_mr,
            "defense_constant": config.defense_constant,
            "minimum_damage": config.minimum_damage,
            "simulation_safety_limit": config.simulation_safety_limit,
            "simulation_card_play_limit_per_action": (
                config.simulation_card_play_limit_per_action
            ),
            "support_request_max": config.support_request_max,
            "support_normal_effect_multiplier_bp": (
                config.support_normal_effect_multiplier_bp
            ),
            "support_normal_request_reduction": (
                config.support_normal_request_reduction
            ),
        }

    def _create_m3_runtime(self, scenario: BattleScenario) -> BattleRuntime:
        config = scenario.rule_config
        participants: dict[str, ParticipantRuntime] = {}
        for setup in scenario.participants:
            is_support = setup.slot_type == "support"
            runtime = ParticipantRuntime(
                setup=setup,
                hp=None if is_support else setup.initial_hp,
                mp=setup.initial_mp,
                alive=None if is_support else True,
                lane_id=None if is_support else setup.lane_id,
                position=None if is_support else config.initial_position,
                engaged_with_participant_id=None,
                respawn_turns_remaining=None,
            )
            self._initialize_m3_deck(
                runtime,
                scenario.seed,
                config,
                stream_name="deck_initial_shuffle",
            )
            participants[setup.participant_id] = runtime
        runtime = BattleRuntime(
            scenario=scenario,
            participants=participants,
            nexus_states={
                "ally": NexusSnapshot(
                    side="ally",
                    hp=config.nexus_max_hp,
                    max_hp=config.nexus_max_hp,
                    ar=config.nexus_ar,
                    mr=config.nexus_mr,
                ),
                "enemy": NexusSnapshot(
                    side="enemy",
                    hp=config.nexus_max_hp,
                    max_hp=config.nexus_max_hp,
                    ar=config.nexus_ar,
                    mr=config.nexus_mr,
                ),
            },
            rule_config=config,
        )
        for lane_id in M3_LANE_ORDER:
            ally = self._participant_in_slot(runtime, lane_id, "ally")
            enemy = self._participant_in_slot(runtime, lane_id, "enemy")
            ally.engaged_with_participant_id = enemy.setup.participant_id
            enemy.engaged_with_participant_id = ally.setup.participant_id
        return runtime

    def _initialize_m3_deck(
        self,
        participant: ParticipantRuntime,
        seed: int,
        config: BattleRuleConfig,
        stream_name: str,
    ) -> None:
        cards = list(participant.setup.deck)
        if stream_name == "deck_initial_shuffle":
            stream_count = participant.initial_shuffle_count
            participant.initial_shuffle_count += 1
        elif stream_name == "deck_respawn_shuffle":
            stream_count = participant.respawn_shuffle_count
            participant.respawn_shuffle_count += 1
        else:
            raise BattleScenarioError("unsupported deck shuffle stream.")
        rng = self._rng(seed, stream_name, participant.setup.participant_id, stream_count)
        rng.shuffle(cards)
        participant.hand = cards[: config.initial_hand_size]
        participant.draw_pile = cards[config.initial_hand_size :]
        participant.discard_pile = []
        participant.draw_gauge = 0
        participant.shuffle_count += 1

    def _rng(
        self,
        battle_seed: int,
        stream_name: str,
        key: str,
        stream_count: int,
    ) -> random.Random:
        digest = sha256(f"{battle_seed}:{stream_name}:{key}:{stream_count}".encode()).hexdigest()
        return random.Random(digest)

    def _run_m3_action(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor_id: str,
    ) -> None:
        actor = runtime.participants[actor_id]
        lane_id = actor.lane_id
        recorder.record(
            runtime.action_index,
            "action_started",
            actor_id=actor_id,
            lane_id=lane_id,
        )
        if actor.setup.slot_type == "support":
            self._run_support_action(runtime, recorder, actor)
            self._record_m3_action_completed(runtime, recorder, actor)
            return
        if not actor.alive:
            if actor.respawn_turns_remaining and actor.respawn_turns_remaining > 0:
                before = actor.respawn_turns_remaining
                actor.respawn_turns_remaining -= 1
                recorder.record(
                    runtime.action_index,
                    "respawn_waited",
                    actor_id=actor_id,
                    lane_id=lane_id,
                    payload={
                        "before": before,
                        "after": actor.respawn_turns_remaining,
                    },
                )
                self._record_m3_action_completed(runtime, recorder, actor)
                return
            self._respawn_m3(runtime, recorder, actor)

        can_act = self._move_and_resolve_engagement(runtime, recorder, actor)
        if can_act:
            self._apply_action_right_recovery(runtime, recorder, actor)
            self._increase_m3_draw_gauge(runtime, recorder, actor)
            self._attempt_m3_cards(runtime, recorder, actor)
        else:
            recorder.record(
                runtime.action_index,
                "target_selection_failed",
                actor_id=actor_id,
                lane_id=lane_id,
                payload={"reason": "no_local_target_or_nexus"},
            )
        self._record_m3_action_completed(runtime, recorder, actor)

    def _run_support_action(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> None:
        selected_lane, selection_reason = self._select_support_lane(runtime, actor)
        recorder.record(
            runtime.action_index,
            "support_lane_selected",
            actor_id=actor.setup.participant_id,
            payload={
                "selected_lane_id": selected_lane,
                "requests": dict(runtime.support_requests[actor.setup.side]),
                "selection_reason": selection_reason,
            },
        )
        self._recover_mana(
            runtime,
            recorder,
            actor,
            actor.setup.mpr,
            reason="action_right",
        )
        self._increase_m3_draw_gauge(runtime, recorder, actor)
        self._attempt_m3_cards(runtime, recorder, actor, support_lane=selected_lane)

    def _select_support_lane(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
    ) -> tuple[LaneId, str]:
        requests = runtime.support_requests[actor.setup.side]
        maximum = max(requests.values())
        candidates = [lane_id for lane_id in M3_LANE_ORDER if requests[lane_id] == maximum]
        if len(candidates) == 1:
            return candidates[0], "highest"
        count = runtime.support_lane_selection_count[actor.setup.side]
        rng = self._rng(
            runtime.scenario.seed,
            "support_lane_selection",
            actor.setup.participant_id,
            count,
        )
        runtime.support_lane_selection_count[actor.setup.side] += 1
        reason = "all_zero_random" if maximum == 0 else "highest_tie_random"
        return rng.choice(candidates), reason

    def _record_m3_action_completed(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> None:
        recorder.record(
            runtime.action_index,
            "action_completed",
            actor_id=actor.setup.participant_id,
            lane_id=actor.lane_id,
            payload={
                "acted_actor_id": actor.setup.participant_id,
                "next_actor_id": None
                if runtime.battle_status == "completed"
                else self._peek_m3_next_actor_id(runtime),
                "battle_status": runtime.battle_status,
            },
        )
        if runtime.battle_status == "completed":
            self._record_battle_completed(runtime, recorder)

    def _respawn_m3(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> None:
        config = runtime.scenario.rule_config
        actor.alive = True
        actor.defeated_event_emitted = False
        actor.hp = actor.setup.max_hp
        actor.mp = actor.setup.max_mp
        actor.position = (
            config.ally_nexus_position
            if actor.setup.side == "ally"
            else config.enemy_nexus_position
        )
        actor.engaged_with_participant_id = None
        actor.respawn_turns_remaining = None
        self._initialize_m3_deck(
            actor,
            runtime.scenario.seed,
            config,
            stream_name="deck_respawn_shuffle",
        )
        recorder.record(
            runtime.action_index,
            "deck_shuffled",
            actor_id=actor.setup.participant_id,
            lane_id=actor.lane_id,
            payload={"reason": "respawn", "shuffle_count": actor.shuffle_count},
        )
        recorder.record(
            runtime.action_index,
            "character_respawned",
            actor_id=actor.setup.participant_id,
            lane_id=actor.lane_id,
            payload={
                "hp": actor.hp,
                "mp": actor.mp,
                "position": actor.position,
            },
        )

    def _move_and_resolve_engagement(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> bool:
        opponent = self._lane_opponent(runtime, actor)
        if opponent is None or not opponent.alive:
            self._clear_engagement(actor, opponent)
            self._move_without_opponent(runtime, recorder, actor)
            return self._at_enemy_nexus(runtime, actor)
        if actor.position == opponent.position:
            actor.engaged_with_participant_id = opponent.setup.participant_id
            opponent.engaged_with_participant_id = actor.setup.participant_id
            self._push_engaged_pair(runtime, recorder, actor, opponent)
            return True
        self._move_toward_opponent(runtime, recorder, actor, opponent)
        return actor.position == opponent.position

    def _move_without_opponent(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> None:
        before = actor.position or 0
        direction = self._direction(actor)
        target_position = self._enemy_nexus_position(runtime, actor)
        after = self._clamp_position(runtime, before + direction * actor.setup.push)
        if direction > 0:
            after = min(after, target_position)
        else:
            after = max(after, target_position)
        actor.position = after
        if before != after:
            recorder.record(
                runtime.action_index,
                "lane_moved",
                actor_id=actor.setup.participant_id,
                lane_id=actor.lane_id,
                payload={"before": before, "after": after, "mode": "unopposed"},
            )

    def _move_toward_opponent(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        opponent: ParticipantRuntime,
    ) -> None:
        before = actor.position or 0
        direction = self._direction(actor)
        target_position = opponent.position or 0
        after = before + direction * actor.setup.push
        if direction > 0:
            after = min(after, target_position)
        else:
            after = max(after, target_position)
        actor.position = after
        if before != after:
            recorder.record(
                runtime.action_index,
                "lane_moved",
                actor_id=actor.setup.participant_id,
                target_id=opponent.setup.participant_id,
                lane_id=actor.lane_id,
                payload={"before": before, "after": after, "mode": "approach"},
            )
        if actor.position == opponent.position:
            actor.engaged_with_participant_id = opponent.setup.participant_id
            opponent.engaged_with_participant_id = actor.setup.participant_id
            recorder.record(
                runtime.action_index,
                "engagement_started",
                actor_id=actor.setup.participant_id,
                target_id=opponent.setup.participant_id,
                lane_id=actor.lane_id,
                payload={"position": actor.position or 0},
            )

    def _push_engaged_pair(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        opponent: ParticipantRuntime,
    ) -> None:
        advance = max(0, actor.setup.push - opponent.setup.push)
        if advance == 0:
            return
        before = actor.position or 0
        after = self._clamp_position(runtime, before + self._direction(actor) * advance)
        actor.position = after
        opponent.position = after
        recorder.record(
            runtime.action_index,
            "lane_moved",
            actor_id=actor.setup.participant_id,
            target_id=opponent.setup.participant_id,
            lane_id=actor.lane_id,
            payload={"before": before, "after": after, "mode": "push", "advance": advance},
        )

    def _increase_m3_draw_gauge(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
    ) -> None:
        config = runtime.scenario.rule_config
        before = participant.draw_gauge
        participant.draw_gauge += participant.setup.ds
        trigger_count = participant.draw_gauge // config.draw_gauge_threshold
        participant.draw_gauge %= config.draw_gauge_threshold
        recorder.record(
            runtime.action_index,
            "gauge_changed",
            actor_id=participant.setup.participant_id,
            lane_id=participant.lane_id,
            payload={
                "gauge_type": "draw",
                "before": before,
                "gain": participant.setup.ds,
                "trigger_count": trigger_count,
                "after": participant.draw_gauge,
                "blocked_reason": None,
            },
        )
        for _draw_index in range(trigger_count):
            self._draw_one_m3(runtime, recorder, participant, draw_source="draw_gauge")

    def _gain_draw_gauge_m3(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
        amount: int,
    ) -> None:
        config = runtime.scenario.rule_config
        before = participant.draw_gauge
        participant.draw_gauge += amount
        trigger_count = participant.draw_gauge // config.draw_gauge_threshold
        participant.draw_gauge %= config.draw_gauge_threshold
        recorder.record(
            runtime.action_index,
            "gauge_changed",
            actor_id=participant.setup.participant_id,
            lane_id=participant.lane_id,
            payload={
                "gauge_type": "draw",
                "before": before,
                "gain": amount,
                "trigger_count": trigger_count,
                "after": participant.draw_gauge,
                "reason": "card_effect",
                "blocked_reason": None,
            },
        )
        for _draw_index in range(trigger_count):
            self._draw_one_m3(runtime, recorder, participant, draw_source="card_effect")

    def _change_support_request(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        *,
        actor_id: str,
        side: Side,
        lane_id: LaneId,
        change: int,
        source: str,
    ) -> None:
        before = runtime.support_requests[side][lane_id]
        after = min(
            runtime.scenario.rule_config.support_request_max,
            max(0, before + change),
        )
        runtime.support_requests[side][lane_id] = after
        recorder.record(
            runtime.action_index,
            "support_request_changed",
            actor_id=actor_id,
            lane_id=lane_id,
            payload={
                "side": side,
                "lane_id": lane_id,
                "before": before,
                "requested_change": change,
                "applied_change": after - before,
                "after": after,
                "source": source,
            },
        )

    def _draw_one_m3(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
        draw_source: str,
    ) -> None:
        config = runtime.scenario.rule_config
        if not participant.draw_pile and participant.discard_pile:
            rng = self._rng(
                runtime.scenario.seed,
                "deck_recycle_shuffle",
                participant.setup.participant_id,
                participant.recycle_shuffle_count,
            )
            participant.draw_pile = list(participant.discard_pile)
            rng.shuffle(participant.draw_pile)
            participant.discard_pile.clear()
            participant.recycle_shuffle_count += 1
            participant.shuffle_count += 1
            recorder.record(
                runtime.action_index,
                "discard_recycled",
                actor_id=participant.setup.participant_id,
                lane_id=participant.lane_id,
                payload={"shuffle_count": participant.shuffle_count},
            )
        if not participant.draw_pile:
            recorder.record(
                runtime.action_index,
                "card_draw_blocked",
                actor_id=participant.setup.participant_id,
                lane_id=participant.lane_id,
                payload={
                    "blocked_reason": "empty_deck",
                    "draw_source": draw_source,
                    "hand_size": len(participant.hand),
                },
            )
            return
        if len(participant.hand) >= config.max_hand_size:
            discarded = participant.hand.pop(0)
            participant.discard_pile.append(discarded)
            recorder.record(
                runtime.action_index,
                "card_overflow_discarded",
                actor_id=participant.setup.participant_id,
                lane_id=participant.lane_id,
                payload={"card_id": discarded.card_id, "hand_limit": config.max_hand_size},
            )
        hand_size_before = len(participant.hand)
        card = participant.draw_pile.pop(0)
        participant.hand.append(card)
        recorder.record(
            runtime.action_index,
            "card_drawn",
            actor_id=participant.setup.participant_id,
            lane_id=participant.lane_id,
            payload={
                "card_id": card.card_id,
                "reason": draw_source,
                "draw_source": draw_source,
                "hand_size_before": hand_size_before,
                "hand_size_after": len(participant.hand),
            },
        )

    def _attempt_m3_cards(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        support_lane: LaneId | None = None,
    ) -> None:
        remaining_card_plays = 1
        card_play_count = 0
        while (
            remaining_card_plays > 0
            and actor.hand
            and runtime.battle_status == "running"
        ):
            card = actor.hand[0]
            targets = self._m3_targets_for_card(
                runtime, recorder, actor, card, support_lane=support_lane
            )
            playable = bool(targets) and actor.mp >= card.mp_cost
            primary_target_id = self._target_id_for_payload(targets[0]) if targets else None
            recorder.record(
                runtime.action_index,
                "card_attempted",
                actor_id=actor.setup.participant_id,
                target_id=primary_target_id,
                lane_id=actor.lane_id,
                payload={
                    "card_id": card.card_id,
                    "required_mp": card.mp_cost,
                    "current_mp": actor.mp,
                    "playable": playable,
                    "remaining_card_plays": remaining_card_plays,
                },
            )
            if not playable:
                reason = "no_valid_target" if not targets else "insufficient_mana"
                recorder.record(
                    runtime.action_index,
                    "card_held",
                    actor_id=actor.setup.participant_id,
                    target_id=primary_target_id,
                    lane_id=actor.lane_id,
                    payload={
                        "card_id": card.card_id,
                        "reason": reason,
                        "required_mp": card.mp_cost,
                        "current_mp": actor.mp,
                        "remaining_card_plays": remaining_card_plays,
                    },
                )
                return
            remaining_card_plays -= 1
            card_play_count += 1
            if card_play_count > runtime.scenario.rule_config.simulation_card_play_limit_per_action:
                raise BattleScenarioError("card_play_safety_limit reached.")
            remaining_card_plays += self._use_m3_card(
                runtime,
                recorder,
                actor,
                card,
                targets,
                card_play_index=card_play_count,
                remaining_card_plays=remaining_card_plays,
                support_lane=support_lane,
            )

    def _use_m3_card(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        card: BattleCard,
        targets: list[ParticipantRuntime | str],
        card_play_index: int,
        remaining_card_plays: int,
        support_lane: LaneId | None = None,
    ) -> int:
        granted_card_plays = 0
        actor.hand.pop(0)
        actor.cards_used += 1
        if card.mp_cost:
            before_mp = actor.mp
            actor.mp -= card.mp_cost
            recorder.record(
                runtime.action_index,
                "mana_spent",
                actor_id=actor.setup.participant_id,
                lane_id=actor.lane_id,
                payload={
                    "card_id": card.card_id,
                    "card_play_index": card_play_index,
                    "before": before_mp,
                    "amount": card.mp_cost,
                    "after": actor.mp,
                },
            )
        recorder.record(
            runtime.action_index,
            "card_used",
            actor_id=actor.setup.participant_id,
            target_id=self._target_id_for_payload(targets[0]) if targets else None,
            lane_id=actor.lane_id,
            payload={
                "card_id": card.card_id,
                "card_play_index": card_play_index,
                "remaining_card_plays": remaining_card_plays,
            },
        )
        for effect in card.effects:
            effect_targets = self._m3_targets_for_effect(
                runtime, recorder, actor, effect, support_lane=support_lane
            )
            for target in effect_targets:
                granted_card_plays += self._resolve_m3_effect(
                    runtime,
                    recorder,
                    actor,
                    target,
                    effect,
                    card_play_index=card_play_index,
                    remaining_card_plays=remaining_card_plays + granted_card_plays,
                    support_card_enabled=card.support_enabled,
                )
                if runtime.battle_status == "completed":
                    break
            if runtime.battle_status == "completed":
                break
        actor.discard_pile.append(card)
        if actor.setup.slot_type == "support" and support_lane is not None:
            reduction = (
                card.support_request_reduction
                if card.support_enabled
                else runtime.scenario.rule_config.support_normal_request_reduction
            )
            self._change_support_request(
                runtime,
                recorder,
                actor_id=actor.setup.participant_id,
                side=actor.setup.side,
                lane_id=support_lane,
                change=-reduction,
                source="support_card" if card.support_enabled else "normal_card",
            )
        return granted_card_plays

    def _resolve_m3_effect(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        target: ParticipantRuntime | str,
        effect: BattleEffect,
        card_play_index: int,
        remaining_card_plays: int,
        support_card_enabled: bool = True,
    ) -> int:
        support_penalty = actor.setup.slot_type == "support" and not support_card_enabled
        multiplier_bp = (
            runtime.scenario.rule_config.support_normal_effect_multiplier_bp
            if support_penalty
            else 10000
        )
        if support_penalty and effect.effect_type in {"damage", "heal", "gain_draw_gauge"}:
            recorder.record(
                runtime.action_index,
                "support_effect_reduced",
                actor_id=actor.setup.participant_id,
                target_id=self._target_id_for_payload(target),
                payload={
                    "effect_type": effect.effect_type,
                    "multiplier_bp": multiplier_bp,
                },
            )
        if effect.effect_type == "damage":
            self._damage_m3(
                runtime, recorder, actor, target, effect, multiplier_bp=multiplier_bp
            )
        elif isinstance(target, ParticipantRuntime) and effect.effect_type == "heal":
            self._heal(
                runtime,
                recorder,
                actor,
                target,
                effect.value * multiplier_bp // 10000,
                reason="card_effect",
            )
        elif isinstance(target, ParticipantRuntime) and effect.effect_type == "gain_mana":
            self._gain_mana(runtime, recorder, target, effect.value, reason="card_effect")
        elif isinstance(target, ParticipantRuntime) and effect.effect_type == "draw_card":
            for _draw_index in range(effect.value):
                self._draw_one_m3(runtime, recorder, target, draw_source="card_effect")
        elif isinstance(target, ParticipantRuntime) and effect.effect_type == "gain_draw_gauge":
            self._gain_draw_gauge_m3(
                runtime,
                recorder,
                target,
                effect.value * multiplier_bp // 10000,
            )
        elif effect.effect_type == "add_support_request" and actor.lane_id is not None:
            self._change_support_request(
                runtime,
                recorder,
                actor_id=actor.setup.participant_id,
                side=actor.setup.side,
                lane_id=actor.lane_id,
                change=effect.value,
                source="lane_card",
            )
        elif isinstance(target, ParticipantRuntime) and effect.effect_type == "grant_card_play":
            recorder.record(
                runtime.action_index,
                "grant_card_play",
                actor_id=actor.setup.participant_id,
                target_id=target.setup.participant_id,
                lane_id=actor.lane_id,
                payload={
                    "amount": effect.value,
                    "remaining_card_plays": remaining_card_plays + effect.value,
                    "card_play_index": card_play_index,
                },
            )
            return effect.value
        return 0

    def _damage_m3(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        target: ParticipantRuntime | str,
        effect: BattleEffect,
        multiplier_bp: int = 10000,
    ) -> None:
        requested = self._calculate_m3_damage(
            runtime, actor, target, effect, multiplier_bp=multiplier_bp
        )
        if isinstance(target, ParticipantRuntime):
            before = target.hp
            target.hp = max(0, target.hp - requested)
            applied = before - target.hp
            actor.damage_dealt += applied
            target.damage_taken += applied
            if target.hp == 0:
                target.alive = False
                target.respawn_turns_remaining = runtime.scenario.rule_config.respawn_skip_turns
                self._clear_engagement(target, actor)
            recorder.record(
                runtime.action_index,
                "damage_applied",
                actor_id=actor.setup.participant_id,
                target_id=target.setup.participant_id,
                lane_id=actor.lane_id,
                payload={
                    "before": before,
                    "requested": requested,
                    "applied": applied,
                    "after": target.hp,
                    "damage_type": effect.damage_type,
                },
            )
            self._emit_defeated_events(runtime, recorder)
            return

        nexus = runtime.nexus_states[target]
        before = nexus.hp
        after = max(0, before - requested)
        applied = before - after
        runtime.nexus_states[target] = NexusSnapshot(
            side=nexus.side,
            hp=after,
            max_hp=nexus.max_hp,
            ar=nexus.ar,
            mr=nexus.mr,
        )
        actor.damage_dealt += applied
        recorder.record(
            runtime.action_index,
            "nexus_damaged",
            actor_id=actor.setup.participant_id,
            target_id=f"{target}_nexus",
            lane_id=actor.lane_id,
            payload={
                "side": target,
                "before": before,
                "requested": requested,
                "applied": applied,
                "after": after,
                "damage_type": effect.damage_type,
            },
        )
        if after == 0:
            recorder.record(
                runtime.action_index,
                "nexus_destroyed",
                actor_id=actor.setup.participant_id,
                target_id=f"{target}_nexus",
                lane_id=actor.lane_id,
                payload={"side": target},
            )
            result: BattleResult = "ally_win" if target == "enemy" else "ally_loss"
            self._mark_battle_completed(runtime, result, "nexus_destroyed")

    def _calculate_m3_damage(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
        target: ParticipantRuntime | str,
        effect: BattleEffect,
        multiplier_bp: int = 10000,
    ) -> int:
        config = runtime.scenario.rule_config
        raw_bp = (effect.base_damage if effect.base_damage is not None else effect.value) * 10000
        for scaling in effect.scaling:
            stat = scaling.get("stat", "")
            ratio_bp = scaling.get("ratio_bp", 0)
            raw_bp += self._m3_stat_value(actor, stat) * ratio_bp
        raw_bp = raw_bp * multiplier_bp // 10000
        if effect.damage_type == "true":
            final = raw_bp // 10000
        else:
            defense = self._m3_defense_value(runtime, target, effect.damage_type)
            final = raw_bp * config.defense_constant // (
                10000 * (config.defense_constant + defense)
            )
        return max(config.minimum_damage, final)

    def _m3_stat_value(self, actor: ParticipantRuntime, stat: str) -> int:
        if stat == "ad":
            return actor.setup.ad
        if stat == "ap":
            return actor.setup.ap
        if stat == "max_hp":
            return actor.setup.max_hp
        if stat == "current_hp":
            return actor.hp
        if stat == "missing_hp":
            return actor.setup.max_hp - actor.hp
        return 0

    def _m3_defense_value(
        self,
        runtime: BattleRuntime,
        target: ParticipantRuntime | str,
        damage_type: str,
    ) -> int:
        if isinstance(target, ParticipantRuntime):
            return target.setup.ar if damage_type == "physical" else target.setup.mr
        nexus = runtime.nexus_states[target]
        return nexus.ar if damage_type == "physical" else nexus.mr

    def _m3_targets_for_card(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        card: BattleCard,
        support_lane: LaneId | None = None,
    ) -> list[ParticipantRuntime | str]:
        for effect in card.effects:
            targets = self._m3_targets_for_effect(
                runtime, recorder, actor, effect, support_lane=support_lane
            )
            if not targets:
                return []
        return self._m3_targets_for_effect(
            runtime, recorder, actor, card.effects[0], support_lane=support_lane
        )

    def _m3_targets_for_effect(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        effect: BattleEffect,
        support_lane: LaneId | None = None,
    ) -> list[ParticipantRuntime | str]:
        if actor.setup.slot_type == "support":
            return self._support_targets_for_effect(
                runtime, recorder, actor, effect, support_lane
            )
        if effect.target == "self":
            return [actor] if actor.alive is True else []
        if effect.scope == "local":
            opponent = self._lane_opponent(runtime, actor)
            if (
                opponent
                and opponent.alive
                and actor.engaged_with_participant_id == opponent.setup.participant_id
            ):
                return [opponent]
            if self._at_enemy_nexus(runtime, actor) and effect.effect_type == "damage":
                return [self._opposite_side(actor.setup.side)]
            recorder.record(
                runtime.action_index,
                "target_selection_failed",
                actor_id=actor.setup.participant_id,
                lane_id=actor.lane_id,
                payload={"reason": "no_valid_local_target"},
            )
            return []
        if effect.scope == "adjacent":
            targets = self._adjacent_targets(runtime, actor)
            if not targets:
                recorder.record(
                    runtime.action_index,
                    "target_selection_failed",
                    actor_id=actor.setup.participant_id,
                    lane_id=actor.lane_id,
                    payload={"reason": "no_valid_adjacent_target"},
                )
            return targets[:1]
        targets = self._global_targets(runtime, actor)
        if not targets:
            recorder.record(
                runtime.action_index,
                "target_selection_failed",
                actor_id=actor.setup.participant_id,
                lane_id=actor.lane_id,
                payload={"reason": "no_valid_global_target"},
            )
        return targets

    def _support_targets_for_effect(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        effect: BattleEffect,
        support_lane: LaneId | None,
    ) -> list[ParticipantRuntime | str]:
        if support_lane is None:
            return []
        if effect.effect_type in {"gain_mana", "draw_card", "grant_card_play"}:
            return [actor] if effect.target == "self" else []
        if effect.effect_type == "add_support_request":
            return []
        target_side = (
            actor.setup.side
            if effect.target == "self"
            else self._opposite_side(actor.setup.side)
        )
        lanes = self._support_scope_lanes(runtime, actor, support_lane, effect.scope)
        candidates = [
            participant
            for lane_id in lanes
            for participant in runtime.participants.values()
            if participant.setup.slot_type == "lane"
            and participant.lane_id == lane_id
            and participant.setup.side == target_side
            and participant.alive is True
        ]
        if not candidates:
            recorder.record(
                runtime.action_index,
                "target_selection_failed",
                actor_id=actor.setup.participant_id,
                payload={"reason": "no_valid_support_target", "selected_lane_id": support_lane},
            )
        return candidates

    def _support_scope_lanes(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
        support_lane: LaneId,
        scope: EffectScope,
    ) -> list[LaneId]:
        if scope == "local":
            return [support_lane]
        if scope == "global":
            return list(M3_LANE_ORDER)
        if support_lane in {"top", "bot"}:
            return ["mid"]
        rng = self._rng(
            runtime.scenario.seed,
            "support_adjacent_target_selection",
            actor.setup.participant_id,
            runtime.adjacent_selection_count,
        )
        runtime.adjacent_selection_count += 1
        return [rng.choice(["top", "bot"])]

    def _adjacent_targets(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
    ) -> list[ParticipantRuntime]:
        lane_id = actor.lane_id
        lanes: list[LaneId]
        if lane_id == "top":
            lanes = ["mid"]
        elif lane_id == "bot":
            lanes = ["mid"]
        else:
            lanes = ["top", "bot"]
        candidates = [
            participant
            for participant in runtime.participants.values()
            if participant.lane_id in lanes
            and participant.setup.side != actor.setup.side
            and participant.alive
        ]
        if lane_id == "mid" and len(candidates) > 1:
            rng = self._rng(
                runtime.scenario.seed,
                "adjacent_target_selection",
                actor.setup.participant_id,
                runtime.adjacent_selection_count,
            )
            runtime.adjacent_selection_count += 1
            return [rng.choice(candidates)]
        return candidates

    def _global_targets(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
    ) -> list[ParticipantRuntime]:
        return [
            participant
            for lane_id in M3_LANE_ORDER
            for participant in runtime.participants.values()
            if participant.lane_id == lane_id
            and participant.setup.side != actor.setup.side
            and participant.alive
        ]

    def _participant_in_slot(
        self,
        runtime: BattleRuntime,
        lane_id: LaneId,
        side: Side,
    ) -> ParticipantRuntime:
        return next(
            participant
            for participant in runtime.participants.values()
            if participant.lane_id == lane_id and participant.setup.side == side
        )

    def _lane_opponent(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
    ) -> ParticipantRuntime | None:
        for participant in runtime.participants.values():
            if participant.lane_id == actor.lane_id and participant.setup.side != actor.setup.side:
                return participant
        return None

    def _direction(self, actor: ParticipantRuntime) -> int:
        return 1 if actor.setup.side == "ally" else -1

    def _opposite_side(self, side: Side) -> Side:
        return "enemy" if side == "ally" else "ally"

    def _enemy_nexus_position(self, runtime: BattleRuntime, actor: ParticipantRuntime) -> int:
        config = runtime.scenario.rule_config
        if actor.setup.side == "ally":
            return config.enemy_nexus_position
        return config.ally_nexus_position

    def _at_enemy_nexus(self, runtime: BattleRuntime, actor: ParticipantRuntime) -> bool:
        return actor.position == self._enemy_nexus_position(runtime, actor)

    def _clamp_position(self, runtime: BattleRuntime, position: int) -> int:
        config = runtime.scenario.rule_config
        return min(max(position, config.ally_nexus_position), config.enemy_nexus_position)

    def _clear_engagement(
        self,
        participant: ParticipantRuntime,
        opponent: ParticipantRuntime | None,
    ) -> None:
        participant.engaged_with_participant_id = None
        if opponent:
            opponent.engaged_with_participant_id = None

    def _target_id_for_payload(self, target: ParticipantRuntime | str) -> str:
        if isinstance(target, ParticipantRuntime):
            return target.setup.participant_id
        return f"{target}_nexus"

    def _peek_m3_next_actor_id(self, runtime: BattleRuntime) -> str:
        next_index = (runtime.current_turn_index + 1) % len(runtime.scenario.turn_order)
        return runtime.scenario.turn_order[next_index]

    def _create_runtime(self, scenario: BattleScenario) -> BattleRuntime:
        participants: dict[str, ParticipantRuntime] = {}
        for setup in scenario.participants:
            runtime = ParticipantRuntime(
                setup=setup,
                hp=setup.initial_hp,
                mp=setup.initial_mp,
                alive=True,
            )
            runtime.hand = list(setup.deck[:INITIAL_HAND_SIZE])
            runtime.draw_pile = list(setup.deck[INITIAL_HAND_SIZE:])
            participants[setup.participant_id] = runtime
        return BattleRuntime(scenario=scenario, participants=participants)

    def _run_action(self, runtime: BattleRuntime, recorder: EventRecorder, actor_id: str) -> None:
        action_index = runtime.action_index
        recorder.record(action_index, "action_started", actor_id=actor_id)
        actor = runtime.participants[actor_id]
        if actor.alive:
            self._apply_action_right_recovery(runtime, recorder, actor)
            self._increase_draw_gauge(runtime, recorder, actor)
            self._attempt_card(runtime, recorder, actor)
        completion = self._completion_result(runtime)
        if completion is not None:
            result, end_reason = completion
            self._mark_battle_completed(runtime, result, end_reason)
        recorder.record(
            action_index,
            "action_completed",
            actor_id=actor_id,
            payload={
                "acted_actor_id": actor_id,
                "next_actor_id": None
                if runtime.battle_status == "completed"
                else self._peek_next_actor_id(runtime),
                "battle_status": runtime.battle_status,
            },
        )
        if completion is not None:
            self._record_battle_completed(runtime, recorder)

    def _apply_action_right_recovery(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
    ) -> None:
        self._heal(
            runtime,
            recorder,
            participant,
            participant,
            participant.setup.hpr,
            reason="action_right",
        )
        self._recover_mana(
            runtime,
            recorder,
            participant,
            participant.setup.mpr,
            reason="action_right",
        )

    def _increase_draw_gauge(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
    ) -> None:
        before = participant.draw_gauge
        participant.draw_gauge += participant.setup.ds
        trigger_count = participant.draw_gauge // GAUGE_THRESHOLD
        participant.draw_gauge %= GAUGE_THRESHOLD
        recorder.record(
            runtime.action_index,
            "gauge_changed",
            actor_id=participant.setup.participant_id,
            lane_id=participant.lane_id,
            payload={
                "gauge_type": "draw",
                "before": before,
                "gain": participant.setup.ds,
                "trigger_count": trigger_count,
                "after": participant.draw_gauge,
                "blocked_reason": None,
            },
        )
        for _draw_index in range(trigger_count):
            self._draw_one(runtime, recorder, participant, draw_source="draw_gauge")

    def _attempt_card(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
    ) -> None:
        for card in list(actor.hand):
            target = self._target_for_card(runtime, actor, card)
            playable = target is not None and actor.mp >= card.mp_cost
            recorder.record(
                runtime.action_index,
                "card_attempted",
                actor_id=actor.setup.participant_id,
                target_id=target.setup.participant_id if target else None,
                payload={
                    "card_id": card.card_id,
                    "required_mp": card.mp_cost,
                    "current_mp": actor.mp,
                    "playable": playable,
                },
            )
            if not playable:
                reason = "no_valid_target" if target is None else "insufficient_mana"
                recorder.record(
                    runtime.action_index,
                    "card_held",
                    actor_id=actor.setup.participant_id,
                    target_id=target.setup.participant_id if target else None,
                    payload={
                        "card_id": card.card_id,
                        "reason": reason,
                        "required_mp": card.mp_cost,
                        "current_mp": actor.mp,
                    },
                )
                continue
            self._use_card(runtime, recorder, actor, card)
            return

    def _use_card(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        card: BattleCard,
    ) -> None:
        primary_target = self._target_for_card(runtime, actor, card)
        actor.hand.remove(card)
        actor.discard_pile.append(card)
        actor.cards_used += 1
        if card.mp_cost:
            before_mp = actor.mp
            actor.mp -= card.mp_cost
            recorder.record(
                runtime.action_index,
                "mana_spent",
                actor_id=actor.setup.participant_id,
                payload={
                    "card_id": card.card_id,
                    "before": before_mp,
                    "amount": card.mp_cost,
                    "after": actor.mp,
                },
            )
        recorder.record(
            runtime.action_index,
            "card_used",
            actor_id=actor.setup.participant_id,
            target_id=primary_target.setup.participant_id if primary_target else None,
            payload={"card_id": card.card_id},
        )
        for effect in card.effects:
            target = self._target_for_effect(runtime, actor, effect)
            if target is None:
                continue
            self._resolve_effect(runtime, recorder, actor, target, effect)
            self._emit_defeated_events(runtime, recorder)

    def _resolve_effect(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        target: ParticipantRuntime,
        effect: BattleEffect,
    ) -> None:
        if effect.effect_type == "damage":
            self._damage(runtime, recorder, actor, target, effect.value)
        elif effect.effect_type == "heal":
            self._heal(runtime, recorder, actor, target, effect.value, reason="card_effect")
        elif effect.effect_type == "gain_mana":
            self._gain_mana(runtime, recorder, target, effect.value, reason="card_effect")
        elif effect.effect_type == "draw_card":
            for _draw_index in range(effect.value):
                self._draw_one(runtime, recorder, target, draw_source="card_effect")

    def _target_for_card(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
        card: BattleCard,
    ) -> ParticipantRuntime | None:
        for effect in card.effects:
            target = self._target_for_effect(runtime, actor, effect)
            if target is None:
                return None
        return self._target_for_effect(runtime, actor, card.effects[0])

    def _target_for_effect(
        self,
        runtime: BattleRuntime,
        actor: ParticipantRuntime,
        effect: BattleEffect,
    ) -> ParticipantRuntime | None:
        if effect.target == "self":
            return actor if actor.alive else None
        enemies = [
            participant
            for participant in runtime.participants.values()
            if participant.setup.side != actor.setup.side and participant.alive
        ]
        return enemies[0] if enemies else None

    def _draw_one(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
        draw_source: str,
    ) -> None:
        if len(participant.hand) >= HAND_LIMIT:
            recorder.record(
                runtime.action_index,
                "card_draw_blocked",
                actor_id=participant.setup.participant_id,
                payload={
                    "blocked_reason": "hand_full",
                    "draw_source": draw_source,
                    "hand_size": len(participant.hand),
                    "hand_limit": HAND_LIMIT,
                },
            )
            return
        if not participant.draw_pile and participant.discard_pile:
            participant.draw_pile = list(participant.discard_pile)
            participant.discard_pile.clear()
        if not participant.draw_pile:
            recorder.record(
                runtime.action_index,
                "card_draw_blocked",
                actor_id=participant.setup.participant_id,
                payload={
                    "blocked_reason": "empty_deck",
                    "draw_source": draw_source,
                    "hand_size": len(participant.hand),
                },
            )
            return
        hand_size_before = len(participant.hand)
        card = participant.draw_pile.pop(0)
        participant.hand.append(card)
        recorder.record(
            runtime.action_index,
            "card_drawn",
            actor_id=participant.setup.participant_id,
            payload={
                "card_id": card.card_id,
                "reason": draw_source,
                "draw_source": draw_source,
                "hand_size_before": hand_size_before,
                "hand_size_after": len(participant.hand),
            },
        )

    def _gain_mana(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
        amount: int,
        reason: str,
    ) -> None:
        before = participant.mp
        participant.mp = min(participant.setup.max_mp, participant.mp + amount)
        recorder.record(
            runtime.action_index,
            "mana_gained",
            actor_id=participant.setup.participant_id,
            payload={
                "before": before,
                "requested": amount,
                "applied": participant.mp - before,
                "after": participant.mp,
                "reason": reason,
            },
        )

    def _recover_mana(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        participant: ParticipantRuntime,
        amount: int,
        reason: str,
    ) -> None:
        before = participant.mp
        participant.mp = min(participant.setup.max_mp, participant.mp + amount)
        recorder.record(
            runtime.action_index,
            "mana_recovered",
            actor_id=participant.setup.participant_id,
            target_id=participant.setup.participant_id,
            lane_id=participant.lane_id,
            payload={
                "before": before,
                "requested": amount,
                "applied": participant.mp - before,
                "after": participant.mp,
                "reason": reason,
            },
        )

    def _heal(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        target: ParticipantRuntime,
        amount: int,
        reason: str,
    ) -> None:
        before = target.hp
        target.hp = min(target.setup.max_hp, target.hp + amount)
        recorder.record(
            runtime.action_index,
            "health_recovered",
            actor_id=actor.setup.participant_id,
            target_id=target.setup.participant_id,
            lane_id=actor.lane_id,
            payload={
                "before": before,
                "requested": amount,
                "applied": target.hp - before,
                "after": target.hp,
                "reason": reason,
            },
        )

    def _damage(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        actor: ParticipantRuntime,
        target: ParticipantRuntime,
        amount: int,
    ) -> None:
        before = target.hp
        target.hp = max(0, target.hp - amount)
        actual_damage = before - target.hp
        actor.damage_dealt += actual_damage
        target.damage_taken += actual_damage
        if target.hp == 0:
            target.alive = False
        recorder.record(
            runtime.action_index,
            "damage_applied",
            actor_id=actor.setup.participant_id,
            target_id=target.setup.participant_id,
            lane_id=actor.lane_id,
            payload={
                "before": before,
                "requested": amount,
                "applied": actual_damage,
                "after": target.hp,
            },
        )

    def _emit_defeated_events(self, runtime: BattleRuntime, recorder: EventRecorder) -> None:
        for participant in runtime.participants.values():
            if participant.alive or participant.defeated_event_emitted:
                continue
            participant.defeated_event_emitted = True
            recorder.record(
                runtime.action_index,
                "character_defeated",
                actor_id=participant.setup.participant_id,
                lane_id=participant.lane_id,
                payload={"side": participant.setup.side},
            )

    def _completion_result(self, runtime: BattleRuntime) -> tuple[BattleResult, str] | None:
        ally_alive = any(
            participant.alive
            for participant in runtime.participants.values()
            if participant.setup.side == "ally"
        )
        enemy_alive = any(
            participant.alive
            for participant in runtime.participants.values()
            if participant.setup.side == "enemy"
        )
        if not ally_alive and not enemy_alive:
            return "draw", "all_defeated"
        if not enemy_alive:
            return "ally_win", "enemy_defeated"
        if not ally_alive:
            return "ally_loss", "ally_defeated"
        if runtime.action_index >= runtime.scenario.rule_config.simulation_safety_limit:
            return "draw", "simulation_safety_limit"
        return None

    def _complete_battle(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        result: BattleResult,
        end_reason: str,
    ) -> None:
        self._mark_battle_completed(runtime, result, end_reason)
        self._record_battle_completed(runtime, recorder)

    def _mark_battle_completed(
        self,
        runtime: BattleRuntime,
        result: BattleResult,
        end_reason: str,
    ) -> None:
        runtime.battle_status = "completed"
        runtime.battle_result = result
        runtime.end_reason = end_reason

    def _record_battle_completed(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
    ) -> None:
        recorder.record(
            runtime.action_index,
            "battle_completed",
            payload={"result": runtime.battle_result, "end_reason": runtime.end_reason},
        )

    def _active_actor_id(self, runtime: BattleRuntime) -> str | None:
        for offset in range(len(runtime.scenario.turn_order)):
            turn_index = (runtime.current_turn_index + offset) % len(runtime.scenario.turn_order)
            participant_id = runtime.scenario.turn_order[turn_index]
            if runtime.participants[participant_id].alive:
                runtime.current_turn_index = turn_index
                return participant_id
        return None

    def _advance_turn(self, runtime: BattleRuntime) -> None:
        for offset in range(1, len(runtime.scenario.turn_order) + 1):
            turn_index = (runtime.current_turn_index + offset) % len(runtime.scenario.turn_order)
            participant_id = runtime.scenario.turn_order[turn_index]
            if runtime.participants[participant_id].alive:
                runtime.current_turn_index = turn_index
                return

    def _peek_next_actor_id(self, runtime: BattleRuntime) -> str | None:
        for offset in range(1, len(runtime.scenario.turn_order) + 1):
            turn_index = (runtime.current_turn_index + offset) % len(runtime.scenario.turn_order)
            participant_id = runtime.scenario.turn_order[turn_index]
            if runtime.participants[participant_id].alive:
                return participant_id
        return None

    def _snapshot(self, runtime: BattleRuntime, acted_actor_id: str | None) -> BattleSnapshot:
        if runtime.battle_status == "completed":
            next_actor_id = None
        elif self._is_m3_scenario(runtime.scenario):
            next_actor_id = (
                runtime.scenario.turn_order[runtime.current_turn_index]
                if acted_actor_id is None
                else self._peek_m3_next_actor_id(runtime)
            )
        else:
            next_actor_id = self._peek_active_actor_id(runtime)
        return BattleSnapshot(
            action_index=runtime.action_index,
            battle_status=runtime.battle_status,
            battle_result=runtime.battle_result,
            acted_actor_id=acted_actor_id,
            next_actor_id=next_actor_id,
            participants={
                participant_id: ParticipantSnapshot(
                    participant_id=participant_id,
                    character_master_id=participant.setup.character_master_id,
                    side=participant.setup.side,
                    slot_type=participant.setup.slot_type,
                    hp=participant.hp,
                    max_hp=(
                        None
                        if participant.setup.slot_type == "support"
                        else participant.setup.max_hp
                    ),
                    mp=participant.mp,
                    max_mp=participant.setup.max_mp,
                    alive=participant.alive,
                    ds=participant.setup.ds,
                    mpr=participant.setup.mpr,
                    hpr=(
                        None
                        if participant.setup.slot_type == "support"
                        else participant.setup.hpr
                    ),
                    ad=participant.setup.ad,
                    ap=participant.setup.ap,
                    ar=participant.setup.ar,
                    mr=participant.setup.mr,
                    draw_gauge=participant.draw_gauge,
                    hand=[card.card_id for card in participant.hand],
                    draw_pile=[card.card_id for card in participant.draw_pile],
                    discard_pile=[card.card_id for card in participant.discard_pile],
                    lane_id=participant.lane_id,
                    position=participant.position,
                    push=(
                        participant.setup.push
                        if participant.setup.slot_type == "lane" and participant.lane_id
                        else None
                    ),
                    engaged_with_participant_id=participant.engaged_with_participant_id,
                    respawn_turns_remaining=participant.respawn_turns_remaining,
                    trait_ids=list(participant.setup.trait_ids),
                )
                for participant_id, participant in runtime.participants.items()
            },
            nexus_states=dict(runtime.nexus_states),
            support_requests={
                side: dict(requests)
                for side, requests in runtime.support_requests.items()
            },
            applied_rule_config=runtime.rule_config,
        )

    def _peek_active_actor_id(self, runtime: BattleRuntime) -> str | None:
        for offset in range(len(runtime.scenario.turn_order)):
            turn_index = (runtime.current_turn_index + offset) % len(runtime.scenario.turn_order)
            participant_id = runtime.scenario.turn_order[turn_index]
            if runtime.participants[participant_id].alive:
                return participant_id
        return None

    def _summary(
        self,
        runtime: BattleRuntime,
        recorder: EventRecorder,
        snapshots: list[BattleSnapshot],
    ) -> BattleSummary:
        return BattleSummary(
            battle_id=runtime.scenario.battle_id,
            status=runtime.battle_status,
            result=runtime.battle_result,
            end_reason=runtime.end_reason,
            action_count=runtime.action_index,
            event_count=len(recorder.events),
            snapshot_count=len(snapshots),
            participants={
                participant_id: ParticipantSummary(
                    participant_id=participant_id,
                    side=participant.setup.side,
                    hp=participant.hp,
                    mp=participant.mp,
                    alive=participant.alive,
                    damage_dealt=participant.damage_dealt,
                    damage_taken=participant.damage_taken,
                    cards_used=participant.cards_used,
                )
                for participant_id, participant in runtime.participants.items()
            },
        )

    def _display_catalog(self, scenario: BattleScenario) -> dict[str, object]:
        return {
            "participants": {
                participant.participant_id: {
                    "name": "名称未設定",
                }
                for participant in scenario.participants
            },
            "cards": {
                card.card_id: {
                    "name": "名称未設定",
                    "mp_cost": card.mp_cost,
                    "description": self._card_description(card),
                }
                for participant in scenario.participants
                for card in participant.deck
            },
        }

    def _card_description(self, card: BattleCard) -> str:
        descriptions: list[str] = []
        for effect in card.effects:
            if effect.effect_type == "damage":
                descriptions.append(f"敵に{effect.value}ダメージ")
            elif effect.effect_type == "heal":
                descriptions.append(f"自身のHPを{effect.value}回復")
            elif effect.effect_type == "gain_mana":
                descriptions.append(f"自身のMPを{effect.value}回復")
            elif effect.effect_type == "draw_card":
                descriptions.append(f"カードを{effect.value}枚引く")
        return " / ".join(descriptions)
