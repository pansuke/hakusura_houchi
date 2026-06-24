from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Side = Literal["ally", "enemy"]
BattleStatus = Literal["running", "completed"]
BattleResult = Literal["undecided", "ally_win", "ally_loss", "draw"]
EffectType = Literal["damage", "heal", "gain_mana", "draw_card"]
EffectTarget = Literal["self", "enemy"]

GAUGE_THRESHOLD = 100
HAND_LIMIT = 5
INITIAL_HAND_SIZE = 3
ALLOWED_EFFECT_TYPES: set[str] = {"damage", "heal", "gain_mana", "draw_card"}
ALLOWED_EFFECT_TARGETS: set[str] = {"self", "enemy"}


class BattleScenarioError(ValueError):
    pass


@dataclass(frozen=True)
class BattleEffect:
    effect_type: EffectType
    target: EffectTarget
    value: int


@dataclass(frozen=True)
class BattleCard:
    card_id: str
    mp_cost: int
    effects: list[BattleEffect]


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


@dataclass(frozen=True)
class BattleScenario:
    battle_id: str
    participants: list[BattleParticipantSetup]
    turn_order: list[str]
    max_actions: int = 1000
    seed: int = 0


@dataclass(frozen=True)
class BattleEvent:
    event_id: int
    action_index: int
    sequence: int
    event_type: str
    actor_id: str | None
    target_id: str | None
    payload: dict[str, object]


@dataclass(frozen=True)
class ParticipantSnapshot:
    participant_id: str
    character_master_id: str
    side: Side
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


@dataclass(frozen=True)
class BattleSnapshot:
    action_index: int
    battle_status: BattleStatus
    battle_result: BattleResult
    acted_actor_id: str | None
    next_actor_id: str | None
    participants: dict[str, ParticipantSnapshot]


@dataclass(frozen=True)
class ParticipantSummary:
    participant_id: str
    side: Side
    hp: int
    mp: int
    alive: bool
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
    hp: int
    mp: int
    alive: bool
    draw_gauge: int = 0
    hand: list[BattleCard] = field(default_factory=list)
    draw_pile: list[BattleCard] = field(default_factory=list)
    discard_pile: list[BattleCard] = field(default_factory=list)
    defeated_event_emitted: bool = False
    damage_dealt: int = 0
    damage_taken: int = 0
    cards_used: int = 0


@dataclass
class BattleRuntime:
    scenario: BattleScenario
    participants: dict[str, ParticipantRuntime]
    action_index: int = 0
    current_turn_index: int = 0
    battle_status: BattleStatus = "running"
    battle_result: BattleResult = "undecided"
    end_reason: str = "running"


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
            )
        )
        self._next_event_id += 1


class BattleEngine:
    def simulate(self, scenario: BattleScenario) -> BattleReplay:
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
            if runtime.action_index >= scenario.max_actions:
                self._complete_battle(runtime, recorder, "draw", "max_actions")
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

    def _validate_scenario(self, scenario: BattleScenario) -> None:
        if scenario.max_actions < 1:
            raise BattleScenarioError("max_actions must be greater than or equal to 1.")
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
        if runtime.action_index >= runtime.scenario.max_actions:
            return "draw", "max_actions"
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
        next_actor_id = (
            None if runtime.battle_status == "completed" else self._peek_active_actor_id(runtime)
        )
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
                    hp=participant.hp,
                    max_hp=participant.setup.max_hp,
                    mp=participant.mp,
                    max_mp=participant.setup.max_mp,
                    alive=participant.alive,
                    ds=participant.setup.ds,
                    mpr=participant.setup.mpr,
                    hpr=participant.setup.hpr,
                    draw_gauge=participant.draw_gauge,
                    hand=[card.card_id for card in participant.hand],
                    draw_pile=[card.card_id for card in participant.draw_pile],
                    discard_pile=[card.card_id for card in participant.discard_pile],
                )
                for participant_id, participant in runtime.participants.items()
            },
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
