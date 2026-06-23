"""
テスト一覧:
- 固定シナリオは同一入力から同一Replayを生成する
- 戦闘開始直前のAction #0 Snapshotと初期手札3枚を生成する
- MP不足カードは捨てず、後続の発動可能カードを使う
- discard済みカードはdraw_pile枯渇後に決定的に再利用される
- 手札上限5枚では追加ドローがblockedになる
- DS / MRG / HRGは複数回しきい値到達を処理し、MP / HPは上限を超えない
- damage / heal / gain_mana / draw_cardの4Effectを順番に解決する
- HPが0になったキャラクターは一度だけdefeatedになり勝敗が確定する
- 最大Action数に到達すると引き分けになる
- Event / Snapshot / SummaryのAction Indexと件数が整合する
- 最終Actionではaction_completedがbattle_completedより先に出る
- turn_orderは不足・重複・余分な要素を拒否する
- card_held.reasonは具体的な理由になる
- gauge_changedはbefore/gain/trigger_count/afterを返す
- Snapshotはacted_actor_idとnext_actor_idを返す
"""

from dataclasses import asdict

import pytest

from lane_relay.engine.battle_engine import (
    BattleCard,
    BattleEffect,
    BattleEngine,
    BattleParticipantSetup,
    BattleScenario,
    BattleScenarioError,
)


def damage_card(card_id: str, power: int, mp_cost: int = 0) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=mp_cost,
        effects=[BattleEffect(effect_type="damage", target="enemy", value=power)],
    )


def heal_card(card_id: str, power: int, mp_cost: int = 0) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=mp_cost,
        effects=[BattleEffect(effect_type="heal", target="self", value=power)],
    )


def gain_mana_card(card_id: str, power: int, mp_cost: int = 0) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=mp_cost,
        effects=[BattleEffect(effect_type="gain_mana", target="self", value=power)],
    )


def draw_card(card_id: str, power: int, mp_cost: int = 0) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=mp_cost,
        effects=[BattleEffect(effect_type="draw_card", target="self", value=power)],
    )


def participant(
    participant_id: str,
    side: str,
    deck: list[BattleCard],
    hp: int = 30,
    mp: int = 3,
    ds: int = 0,
    mrg: int = 0,
    hrg: int = 0,
) -> BattleParticipantSetup:
    return BattleParticipantSetup(
        participant_id=participant_id,
        side=side,
        character_master_id=f"character_{participant_id}",
        max_hp=hp,
        max_mp=mp,
        initial_hp=hp,
        initial_mp=mp,
        ds=ds,
        mrg=mrg,
        hrg=hrg,
        deck=deck,
    )


def scenario(
    ally: BattleParticipantSetup,
    enemy: BattleParticipantSetup,
    max_actions: int = 20,
) -> BattleScenario:
    return BattleScenario(
        battle_id="battle_test_001",
        participants=[ally, enemy],
        turn_order=[ally.participant_id, enemy.participant_id],
        max_actions=max_actions,
        seed=1,
    )


def test_same_input_generates_same_replay() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_slash", 3)]),
        participant("enemy_001", "enemy", [damage_card("card_claw", 2)]),
        max_actions=4,
    )

    first = BattleEngine().simulate(battle_scenario)
    second = BattleEngine().simulate(battle_scenario)

    assert asdict(first) == asdict(second)


def test_action_zero_snapshot_and_initial_hand_are_created() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [
                damage_card("card_a", 1),
                damage_card("card_b", 1),
                damage_card("card_c", 1),
                damage_card("card_d", 1),
            ],
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 1)]),
        max_actions=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    initial_snapshot = replay.snapshots[0]
    assert initial_snapshot.action_index == 0
    assert initial_snapshot.participants["ally_001"].hand == ["card_a", "card_b", "card_c"]
    assert initial_snapshot.participants["ally_001"].draw_pile == ["card_d"]
    assert replay.events[0].event_type == "battle_started"


def test_mana_shortage_holds_card_and_uses_later_playable_card() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [damage_card("card_expensive", 8, mp_cost=5), damage_card("card_cheap", 4)],
            mp=0,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 1)]),
        max_actions=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    event_types = [event.event_type for event in replay.events]
    assert "card_held" in event_types
    assert any(
        event.event_type == "card_held"
        and event.payload.get("reason") == "insufficient_mana"
        for event in replay.events
    )
    assert any(event.payload.get("card_id") == "card_cheap" for event in replay.events)
    snapshot = replay.snapshots[-1].participants["ally_001"]
    assert "card_expensive" in snapshot.hand
    assert "card_cheap" in snapshot.discard_pile


def test_discard_recycles_deterministically_when_draw_pile_is_empty() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [draw_card("card_draw", 1), damage_card("card_hit", 1)]),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        max_actions=3,
    )

    replay = BattleEngine().simulate(battle_scenario)

    ally_snapshot = replay.snapshots[-1].participants["ally_001"]
    assert sorted(ally_snapshot.hand + ally_snapshot.draw_pile + ally_snapshot.discard_pile) == [
        "card_draw",
        "card_hit",
    ]
    assert any(event.event_type == "card_drawn" for event in replay.events)


def test_hand_limit_blocks_draw_when_hand_is_full() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [
                damage_card("card_expensive_1", 1, mp_cost=99),
                damage_card("card_expensive_2", 1, mp_cost=99),
                damage_card("card_expensive_3", 1, mp_cost=99),
                damage_card("card_expensive_4", 1, mp_cost=99),
                damage_card("card_expensive_5", 1, mp_cost=99),
                damage_card("card_extra", 1, mp_cost=99),
            ],
            ds=200,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        max_actions=2,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert any(
        event.event_type == "card_draw_blocked" and event.actor_id == "ally_001"
        for event in replay.events
    )
    assert len(replay.snapshots[-1].participants["ally_001"].hand) == 5


def test_gauges_trigger_multiple_times_and_cap_hp_mp() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [damage_card("card_expensive", 1, mp_cost=99)],
            hp=20,
            mp=3,
            ds=0,
            mrg=250,
            hrg=250,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        max_actions=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    ally_snapshot = replay.snapshots[-1].participants["ally_001"]
    assert ally_snapshot.mp == 3
    assert ally_snapshot.hp == 20
    assert ally_snapshot.mana_gauge == 50
    assert ally_snapshot.health_gauge == 50
    mana_gauge_event = next(
        event
        for event in replay.events
        if event.event_type == "gauge_changed"
        and event.actor_id == "ally_001"
        and event.payload["gauge_type"] == "mana"
    )
    assert mana_gauge_event.payload == {
        "gauge_type": "mana",
        "before": 0,
        "gain": 250,
        "trigger_count": 2,
        "after": 50,
        "blocked_reason": None,
    }


def test_four_effect_types_are_resolved_in_order() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [
                BattleCard(
                    card_id="card_combo",
                    mp_cost=1,
                    effects=[
                        BattleEffect(effect_type="gain_mana", target="self", value=1),
                        BattleEffect(effect_type="draw_card", target="self", value=1),
                        BattleEffect(effect_type="heal", target="self", value=2),
                        BattleEffect(effect_type="damage", target="enemy", value=5),
                    ],
                ),
                damage_card("card_follow", 1),
                damage_card("card_other", 1),
                damage_card("card_drawn", 1),
            ],
            hp=10,
            mp=2,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)], hp=12),
        max_actions=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    effect_events = [
        event.event_type
        for event in replay.events
        if event.event_type in {"mana_gained", "card_drawn", "health_recovered", "damage_applied"}
        and event.action_index == 1
    ]
    assert effect_events[-4:] == [
        "mana_gained",
        "card_drawn",
        "health_recovered",
        "damage_applied",
    ]
    assert replay.snapshots[-1].participants["enemy_001"].hp == 7


def test_death_and_win_result_are_emitted_once() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_finish", 99)]),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 1)], hp=10),
        max_actions=5,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert replay.summary.result == "ally_win"
    assert replay.summary.end_reason == "enemy_defeated"
    assert [event.event_type for event in replay.events].count("character_defeated") == 1
    assert replay.snapshots[-1].battle_status == "completed"
    final_action_events = [
        event.event_type
        for event in replay.events
        if event.action_index == replay.summary.action_count
    ]
    assert final_action_events[-4:] == [
        "damage_applied",
        "character_defeated",
        "action_completed",
        "battle_completed",
    ]


def test_max_action_boundary_results_in_draw() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_none", 0)]),
        participant("enemy_001", "enemy", [damage_card("card_none_enemy", 0)]),
        max_actions=3,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert replay.summary.result == "draw"
    assert replay.summary.end_reason == "max_actions"
    assert replay.summary.action_count == 3
    assert replay.snapshots[-1].action_index == 3


def test_event_snapshot_summary_are_consistent() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_hit", 2)]),
        participant("enemy_001", "enemy", [damage_card("card_claw", 1)]),
        max_actions=2,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert replay.summary.event_count == len(replay.events)
    assert replay.summary.snapshot_count == len(replay.snapshots)
    assert replay.snapshots[0].action_index == 0
    assert [snapshot.action_index for snapshot in replay.snapshots[1:]] == [1, 2]
    assert all(event.event_id == index + 1 for index, event in enumerate(replay.events))
    assert any(event.event_type == "battle_completed" for event in replay.events)
    assert replay.snapshots[0].acted_actor_id is None
    assert replay.snapshots[0].next_actor_id == "ally_001"
    assert replay.snapshots[1].acted_actor_id == "ally_001"
    assert replay.snapshots[1].next_actor_id == "enemy_001"


@pytest.mark.parametrize(
    "turn_order",
    [
        ["ally_001"],
        ["ally_001", "ally_001"],
        ["ally_001", "enemy_001", "ghost_001"],
    ],
)
def test_scenario_validation_rejects_invalid_turn_order(turn_order: list[str]) -> None:
    battle_scenario = BattleScenario(
        battle_id="battle_invalid",
        participants=[
            participant("ally_001", "ally", [damage_card("card_hit", 1)]),
            participant("enemy_001", "enemy", [damage_card("card_claw", 1)]),
        ],
        turn_order=turn_order,
        max_actions=1,
        seed=1,
    )

    with pytest.raises(BattleScenarioError):
        BattleEngine().simulate(battle_scenario)
