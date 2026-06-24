"""
テスト一覧:
- 固定シナリオは同一入力から同一Replayを生成する
- 戦闘開始直前のAction #0 Snapshotと初期手札3枚を生成する
- MP不足カードは捨てず、後続の発動可能カードを使う
- discard済みカードはdraw_pile枯渇後に決定的に再利用される
- 手札上限5枚では追加ドローがblockedになる
- HPR / MPRは行動者だけに適用され、DSはDraw Gaugeだけを進める
- damage / heal / gain_mana / draw_cardの4Effectを順番に解決する
- HPが0になったキャラクターは一度だけdefeatedになり勝敗が確定する
- 最大Action数に到達すると引き分けになる
- Event / Snapshot / SummaryのAction Indexと件数が整合する
- 最終Actionではaction_completedがbattle_completedより先に出る
- turn_orderは不足・重複・余分な要素を拒否する
- BattleScenarioは不正な参加者・カード・Effect定義を拒否する
- card_held.reasonは具体的な理由になる
- gauge_changedはbefore/gain/trigger_count/afterを返す
- Snapshotはacted_actor_idとnext_actor_idを返す
- M3はTOP味方から固定スロット順でActionを進める
- M3は本番Deck Runtimeで初期手札3・最大手札7・overflow discardを行う
- M3は最古カードだけを使用判定し、使用不能なら後続カードを探索しない
- M3はbase + scalingと防御式でDamageを計算する
- M3はgrant_card_playで同一Action内の追加カード使用権を得る
- M3はAdjacent / Global Scopeで対象を選択する
- M3は死亡後、自分の行動機会で復活待ちを数える
- M3はNexus破壊で勝敗を確定し、Safety Limit到達をerrorにする
"""

from dataclasses import asdict

import pytest

from lane_relay.engine.battle_engine import (
    BattleCard,
    BattleEffect,
    BattleEngine,
    BattleParticipantSetup,
    BattleRuleConfig,
    BattleScenario,
    BattleScenarioError,
)
from lane_relay.engine.scenario_adapter import participant_from_character_master


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


def m3_damage_card(
    card_id: str,
    value: int,
    mp_cost: int = 0,
    scope: str = "local",
    damage_type: str = "true",
    base_damage: int | None = None,
    scaling: list[dict[str, int]] | None = None,
) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=mp_cost,
        effects=[
            BattleEffect(
                effect_type="damage",
                target="enemy",
                value=value,
                scope=scope,
                damage_type=damage_type,
                base_damage=base_damage,
                scaling=scaling or [],
            )
        ],
    )


def grant_card_play_card(card_id: str, amount: int) -> BattleCard:
    return BattleCard(
        card_id=card_id,
        mp_cost=0,
        effects=[
            BattleEffect(
                effect_type="grant_card_play",
                target="self",
                value=amount,
            )
        ],
    )


def participant(
    participant_id: str,
    side: str,
    deck: list[BattleCard],
    hp: int = 30,
    mp: int = 3,
    initial_hp: int | None = None,
    initial_mp: int | None = None,
    ds: int = 0,
    mpr: int = 0,
    hpr: int = 0,
) -> BattleParticipantSetup:
    return BattleParticipantSetup(
        participant_id=participant_id,
        side=side,
        character_master_id=f"character_{participant_id}",
        max_hp=hp,
        max_mp=mp,
        initial_hp=initial_hp if initial_hp is not None else hp,
        initial_mp=initial_mp if initial_mp is not None else mp,
        ds=ds,
        mpr=mpr,
        hpr=hpr,
        deck=deck,
    )


def scenario(
    ally: BattleParticipantSetup,
    enemy: BattleParticipantSetup,
    simulation_safety_limit: int = 20,
) -> BattleScenario:
    return BattleScenario(
        battle_id="battle_test_001",
        participants=[ally, enemy],
        turn_order=[ally.participant_id, enemy.participant_id],
        seed=1,
        rule_config=BattleRuleConfig(simulation_safety_limit=simulation_safety_limit),
    )


def m3_participant(
    participant_id: str,
    side: str,
    lane_id: str,
    deck: list[BattleCard],
    hp: int = 30,
    mp: int = 3,
    ds: int = 0,
    push: int = 0,
    ad: int = 0,
    ap: int = 0,
    ar: int = 0,
    mr: int = 0,
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
        mpr=0,
        hpr=0,
        deck=deck,
        lane_id=lane_id,
        push=push,
        ad=ad,
        ap=ap,
        ar=ar,
        mr=mr,
    )


def m3_scenario(
    participants: list[BattleParticipantSetup],
    simulation_safety_limit: int | None = 50,
    seed: int = 1,
    rule_config: BattleRuleConfig | None = None,
) -> BattleScenario:
    resolved_rule_config = rule_config or BattleRuleConfig()
    resolved_rule_config = BattleRuleConfig(
        initial_hand_size=resolved_rule_config.initial_hand_size,
        max_hand_size=resolved_rule_config.max_hand_size,
        draw_gauge_threshold=resolved_rule_config.draw_gauge_threshold,
        respawn_skip_turns=resolved_rule_config.respawn_skip_turns,
        ally_nexus_position=resolved_rule_config.ally_nexus_position,
        enemy_nexus_position=resolved_rule_config.enemy_nexus_position,
        initial_position=resolved_rule_config.initial_position,
        nexus_max_hp=resolved_rule_config.nexus_max_hp,
        nexus_ar=resolved_rule_config.nexus_ar,
        nexus_mr=resolved_rule_config.nexus_mr,
        defense_constant=resolved_rule_config.defense_constant,
        minimum_damage=resolved_rule_config.minimum_damage,
        simulation_safety_limit=(
            simulation_safety_limit
            if simulation_safety_limit is not None
            else resolved_rule_config.simulation_safety_limit
        ),
        simulation_card_play_limit_per_action=(
            resolved_rule_config.simulation_card_play_limit_per_action
        ),
    )
    return BattleScenario(
        battle_id="battle_m3_test_001",
        participants=participants,
        turn_order=[
            "top_ally",
            "top_enemy",
            "mid_ally",
            "mid_enemy",
            "bot_ally",
            "bot_enemy",
        ],
        seed=seed,
        rule_config=resolved_rule_config,
    )


def m3_lane_participants(
    top_ally_deck: list[BattleCard] | None = None,
    top_enemy_deck: list[BattleCard] | None = None,
    mid_ally_deck: list[BattleCard] | None = None,
    mid_enemy_deck: list[BattleCard] | None = None,
    bot_ally_deck: list[BattleCard] | None = None,
    bot_enemy_deck: list[BattleCard] | None = None,
) -> list[BattleParticipantSetup]:
    filler = [m3_damage_card("card_filler", 0)]
    nexus_breaker = [
        m3_damage_card("card_nexus_breaker_1", 1000),
        m3_damage_card("card_nexus_breaker_2", 1000),
        m3_damage_card("card_nexus_breaker_3", 1000),
    ]
    return [
        m3_participant("top_ally", "ally", "top", top_ally_deck or filler, push=1000),
        m3_participant(
            "top_enemy",
            "enemy",
            "top",
            top_enemy_deck or filler,
            hp=1,
            push=0,
        ),
        m3_participant(
            "mid_ally",
            "ally",
            "mid",
            mid_ally_deck or nexus_breaker,
            push=1000,
        ),
        m3_participant(
            "mid_enemy",
            "enemy",
            "mid",
            mid_enemy_deck or filler,
            hp=1,
            push=0,
        ),
        m3_participant(
            "bot_ally",
            "ally",
            "bot",
            bot_ally_deck or filler,
            push=1000,
        ),
        m3_participant(
            "bot_enemy",
            "enemy",
            "bot",
            bot_enemy_deck or filler,
            hp=1,
            push=0,
        ),
    ]


def test_same_input_generates_same_replay() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_slash", 3)]),
        participant("enemy_001", "enemy", [damage_card("card_claw", 2)]),
        simulation_safety_limit=4,
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
        simulation_safety_limit=1,
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
        simulation_safety_limit=1,
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
        simulation_safety_limit=3,
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
            ds=300,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert any(
        event.event_type == "card_draw_blocked" and event.actor_id == "ally_001"
        for event in replay.events
    )
    blocked_event = next(
        event for event in replay.events if event.event_type == "card_draw_blocked"
    )
    assert blocked_event.payload == {
        "blocked_reason": "hand_full",
        "draw_source": "draw_gauge",
        "hand_size": 5,
        "hand_limit": 5,
    }
    gauge_event = next(event for event in replay.events if event.event_type == "gauge_changed")
    assert gauge_event.sequence < blocked_event.sequence
    assert len(replay.snapshots[-1].participants["ally_001"].hand) == 5


def test_card_effect_blocked_draw_reports_source() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [
                draw_card("card_draw", 4),
                damage_card("card_hold_1", 1, mp_cost=99),
                damage_card("card_hold_2", 1, mp_cost=99),
                damage_card("card_hold_3", 1, mp_cost=99),
                damage_card("card_hold_4", 1, mp_cost=99),
                damage_card("card_hold_5", 1, mp_cost=99),
            ],
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    blocked_event = next(
        event for event in replay.events if event.event_type == "card_draw_blocked"
    )
    assert blocked_event.payload == {
        "blocked_reason": "hand_full",
        "draw_source": "card_effect",
        "hand_size": 5,
        "hand_limit": 5,
    }


def test_empty_deck_blocked_draw_reports_source() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [draw_card("card_draw", 2)]),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)]),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    blocked_event = next(
        event for event in replay.events if event.event_type == "card_draw_blocked"
    )
    assert blocked_event.payload == {
        "blocked_reason": "empty_deck",
        "draw_source": "card_effect",
        "hand_size": 1,
    }


def test_action_right_recovery_applies_only_to_actor_and_caps_hp_mp() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [damage_card("card_expensive", 1, mp_cost=99)],
            hp=20,
            mp=5,
            initial_hp=18,
            initial_mp=4,
            ds=0,
            mpr=3,
            hpr=5,
        ),
        participant(
            "enemy_001",
            "enemy",
            [damage_card("card_enemy", 0)],
            hp=20,
            mp=5,
            initial_hp=18,
            initial_mp=4,
            mpr=3,
            hpr=5,
        ),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    ally_snapshot = replay.snapshots[-1].participants["ally_001"]
    enemy_snapshot = replay.snapshots[-1].participants["enemy_001"]
    assert ally_snapshot.mp == 5
    assert ally_snapshot.hp == 20
    assert enemy_snapshot.mp == 4
    assert enemy_snapshot.hp == 18
    assert not hasattr(ally_snapshot, "mana_gauge")
    assert not hasattr(ally_snapshot, "health_gauge")
    mana_recovered_event = next(
        event
        for event in replay.events
        if event.event_type == "mana_recovered" and event.actor_id == "ally_001"
    )
    assert mana_recovered_event.payload == {
        "before": 4,
        "requested": 3,
        "applied": 1,
        "after": 5,
        "reason": "action_right",
    }
    health_recovered_event = next(
        event
        for event in replay.events
        if event.event_type == "health_recovered" and event.actor_id == "ally_001"
    )
    assert health_recovered_event.payload == {
        "before": 18,
        "requested": 5,
        "applied": 2,
        "after": 20,
        "reason": "action_right",
    }
    action_events = [
        event.event_type
        for event in replay.events
        if event.action_index == 1
        and event.event_type in {"health_recovered", "mana_recovered", "gauge_changed"}
    ]
    assert action_events == ["health_recovered", "mana_recovered", "gauge_changed"]


def test_mpr_is_applied_before_card_playability_check() -> None:
    battle_scenario = scenario(
        participant(
            "ally_001",
            "ally",
            [damage_card("card_after_mpr", 4, mp_cost=2)],
            mp=3,
            initial_mp=1,
            mpr=1,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)], hp=10),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert any(
        event.event_type == "card_used"
        and event.payload["card_id"] == "card_after_mpr"
        for event in replay.events
    )
    assert replay.snapshots[-1].participants["enemy_001"].hp == 6


def test_ds_applies_only_to_actor_draw_gauge() -> None:
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
            ds=100,
        ),
        participant("enemy_001", "enemy", [damage_card("card_enemy", 0)], ds=100),
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    ally_snapshot = replay.snapshots[-1].participants["ally_001"]
    enemy_snapshot = replay.snapshots[-1].participants["enemy_001"]
    assert ally_snapshot.draw_gauge == 0
    assert ally_snapshot.hand == ["card_b", "card_c", "card_d"]
    assert enemy_snapshot.draw_gauge == 0
    assert enemy_snapshot.hand == ["card_enemy"]
    gauge_events = [event for event in replay.events if event.event_type == "gauge_changed"]
    assert [event.actor_id for event in gauge_events] == ["ally_001"]
    assert gauge_events[0].payload == {
        "gauge_type": "draw",
        "before": 0,
        "gain": 100,
        "trigger_count": 1,
        "after": 0,
        "blocked_reason": None,
    }
    draw_event = next(event for event in replay.events if event.event_type == "card_drawn")
    assert draw_event.payload == {
        "card_id": "card_d",
        "reason": "draw_gauge",
        "draw_source": "draw_gauge",
        "hand_size_before": 3,
        "hand_size_after": 4,
    }
    assert gauge_events[0].sequence < draw_event.sequence


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
        simulation_safety_limit=1,
    )

    replay = BattleEngine().simulate(battle_scenario)

    effect_events = [
        event.event_type
        for event in replay.events
        if event.event_type in {"mana_gained", "card_drawn", "health_recovered", "damage_applied"}
        and event.action_index == 1
        and event.payload.get("reason") != "action_right"
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
        simulation_safety_limit=5,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert replay.summary.result == "ally_win"
    assert replay.summary.end_reason == "enemy_defeated"
    assert [event.event_type for event in replay.events].count("character_defeated") == 1
    assert replay.snapshots[-1].battle_status == "completed"
    card_used_event = next(event for event in replay.events if event.event_type == "card_used")
    assert card_used_event.target_id == "enemy_001"
    damage_event = next(event for event in replay.events if event.event_type == "damage_applied")
    assert damage_event.payload == {
        "before": 10,
        "requested": 99,
        "applied": 10,
        "after": 0,
    }
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
    action_completed_event = next(
        event
        for event in replay.events
        if event.event_type == "action_completed"
        and event.action_index == replay.summary.action_count
    )
    assert action_completed_event.payload == {
        "acted_actor_id": "ally_001",
        "next_actor_id": None,
        "battle_status": "completed",
    }


def test_max_action_boundary_results_in_draw() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_none", 0)]),
        participant("enemy_001", "enemy", [damage_card("card_none_enemy", 0)]),
        simulation_safety_limit=3,
    )

    replay = BattleEngine().simulate(battle_scenario)

    assert replay.summary.result == "draw"
    assert replay.summary.end_reason == "simulation_safety_limit"
    assert replay.summary.action_count == 3
    assert replay.snapshots[-1].action_index == 3


def test_event_snapshot_summary_are_consistent() -> None:
    battle_scenario = scenario(
        participant("ally_001", "ally", [damage_card("card_hit", 2)]),
        participant("enemy_001", "enemy", [damage_card("card_claw", 1)]),
        simulation_safety_limit=2,
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
    ally_snapshot = replay.snapshots[1].participants["ally_001"]
    assert ally_snapshot.character_master_id == "character_ally_001"
    assert ally_snapshot.ds == 0
    assert ally_snapshot.mpr == 0
    assert ally_snapshot.hpr == 0
    assert replay.display_catalog["participants"]["ally_001"]["name"] == "名称未設定"


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
        seed=1,
        rule_config=BattleRuleConfig(simulation_safety_limit=1),
    )

    with pytest.raises(BattleScenarioError):
        BattleEngine().simulate(battle_scenario)


@pytest.mark.parametrize(
    "ally",
    [
        participant("ally_001", "ally", []),
        participant(
            "ally_001",
            "ally",
            [damage_card("card_hit", 1)],
            hp=10,
            initial_hp=11,
        ),
        participant(
            "ally_001",
            "ally",
            [damage_card("card_hit", 1)],
            mp=3,
            initial_mp=4,
        ),
        participant("ally_001", "ally", [damage_card("card_hit", 1)], ds=-1),
        participant("ally_001", "ally", [damage_card("card_hit", 1)], mpr=-1),
        participant("ally_001", "ally", [damage_card("card_hit", 1)], hpr=-1),
        participant("ally_001", "ally", [damage_card("card_hit", 1, mp_cost=-1)]),
        participant("ally_001", "ally", [BattleCard("card_empty", 0, [])]),
        participant(
            "ally_001",
            "ally",
            [BattleCard("card_negative", 0, [BattleEffect("damage", "enemy", -1)])],
        ),
        participant(
            "ally_001",
            "ally",
            [BattleCard("card_unknown_effect", 0, [BattleEffect("unknown", "enemy", 1)])],
        ),
        participant(
            "ally_001",
            "ally",
            [BattleCard("card_unknown_target", 0, [BattleEffect("damage", "ally", 1)])],
        ),
    ],
)
def test_scenario_validation_rejects_invalid_participant_setup(
    ally: BattleParticipantSetup,
) -> None:
    battle_scenario = scenario(
        ally,
        participant("enemy_001", "enemy", [damage_card("card_claw", 1)]),
        simulation_safety_limit=1,
    )

    with pytest.raises(BattleScenarioError):
        BattleEngine().simulate(battle_scenario)


def test_m3_uses_fixed_lane_turn_order_and_snapshot_contract() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[m3_damage_card("card_top", 1)],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(nexus_max_hp=1),
        )
    )

    action_started = [
        event
        for event in replay.events
        if event.event_type == "action_started"
    ]
    assert [event.actor_id for event in action_started[:4]] == [
        "top_ally",
        "top_enemy",
        "mid_ally",
        "mid_enemy",
    ]
    assert action_started[0].lane_id == "top"
    assert replay.snapshots[0].next_actor_id == "top_ally"
    top_snapshot = replay.snapshots[0].participants["top_ally"]
    assert top_snapshot.lane_id == "top"
    assert top_snapshot.position == 0
    assert replay.snapshots[0].nexus_states["enemy"].hp == 1
    assert replay.snapshots[0].applied_rule_config is not None


def test_m3_deck_runtime_draws_and_discards_oldest_on_overflow() -> None:
    cards = [m3_damage_card(f"card_{index}", 1, mp_cost=99) for index in range(8)]
    participants = m3_lane_participants(
        top_ally_deck=cards,
        mid_ally_deck=[
            m3_damage_card("card_mid_1", 1000),
            m3_damage_card("card_mid_2", 1000),
            m3_damage_card("card_mid_3", 1000),
        ],
    )
    participants[0] = m3_participant(
        "top_ally",
        "ally",
        "top",
        cards,
        ds=100,
        push=1000,
    )
    replay = BattleEngine().simulate(
        m3_scenario(
            participants,
            rule_config=BattleRuleConfig(
                initial_hand_size=7,
                max_hand_size=7,
                nexus_max_hp=1,
            ),
        )
    )

    overflow_event = next(
        event for event in replay.events if event.event_type == "card_overflow_discarded"
    )
    draw_event = next(event for event in replay.events if event.event_type == "card_drawn")

    assert overflow_event.actor_id == "top_ally"
    assert overflow_event.payload["hand_limit"] == 7
    assert draw_event.actor_id == "top_ally"
    assert draw_event.payload["hand_size_after"] == 7


def test_m3_checks_only_oldest_card_before_holding_action() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[
                    m3_damage_card("card_expensive", 1, mp_cost=99),
                    m3_damage_card("card_cheap", 1),
                    m3_damage_card("card_third", 1),
                ],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(initial_hand_size=2, nexus_max_hp=1),
        )
    )

    held = next(
        event
        for event in replay.events
        if event.event_type == "card_held" and event.actor_id == "top_ally"
    )
    top_used_card_ids = [
        event.payload["card_id"]
        for event in replay.events
        if event.event_type == "card_used" and event.actor_id == "top_ally"
    ]
    assert held.payload["card_id"] == "card_expensive"
    assert held.payload["reason"] == "insufficient_mana"
    assert "card_cheap" not in top_used_card_ids


def test_m3_damage_uses_scaling_and_lol_defense_formula() -> None:
    participants = m3_lane_participants(
        top_ally_deck=[
            m3_damage_card(
                "card_scaled_physical",
                0,
                damage_type="physical",
                base_damage=80,
                scaling=[{"stat": "ad", "ratio_bp": 20000}],
            )
        ],
        mid_ally_deck=[
            m3_damage_card("card_mid_1", 1000),
            m3_damage_card("card_mid_2", 1000),
            m3_damage_card("card_mid_3", 1000),
        ],
    )
    participants[0] = m3_participant(
        "top_ally",
        "ally",
        "top",
        [
            m3_damage_card(
                "card_scaled_physical",
                0,
                damage_type="physical",
                base_damage=80,
                scaling=[{"stat": "ad", "ratio_bp": 20000}],
            )
        ],
        push=1000,
        ad=20,
    )
    participants[1] = m3_participant(
        "top_enemy",
        "enemy",
        "top",
        [m3_damage_card("card_filler", 0)],
        hp=100,
        ar=100,
    )
    replay = BattleEngine().simulate(
        m3_scenario(
            participants,
            rule_config=BattleRuleConfig(nexus_max_hp=1),
        )
    )

    damage_event = next(
        event
        for event in replay.events
        if event.event_type == "damage_applied" and event.actor_id == "top_ally"
    )

    assert damage_event.payload["requested"] == 60


def test_m3_grant_card_play_allows_next_oldest_card_in_same_action() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[
                    grant_card_play_card("card_focus", 1),
                    m3_damage_card("card_action_hit", 1),
                ],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(initial_hand_size=2, nexus_max_hp=1),
        )
    )

    top_card_used = [
        event
        for event in replay.events
        if event.event_type == "card_used" and event.actor_id == "top_ally"
    ]

    assert [event.payload["card_id"] for event in top_card_used[:2]] == [
        "card_focus",
        "card_action_hit",
    ]
    assert top_card_used[0].action_index == top_card_used[1].action_index
    assert any(
        event.event_type == "grant_card_play" and event.actor_id == "top_ally"
        for event in replay.events
    )


def test_m3_grant_card_play_plus_two_allows_three_cards_only_in_current_action() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[
                    grant_card_play_card("card_focus_plus_two", 2),
                    m3_damage_card("card_action_hit_1", 1),
                    m3_damage_card("card_action_hit_2", 1),
                    m3_damage_card("card_action_hit_3", 1),
                ],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(initial_hand_size=4, nexus_max_hp=1),
        )
    )

    top_cards_by_action: dict[int, list[str]] = {}
    for event in replay.events:
        if event.event_type == "card_used" and event.actor_id == "top_ally":
            top_cards_by_action.setdefault(event.action_index, []).append(
                str(event.payload["card_id"])
            )

    first_action_cards = next(iter(top_cards_by_action.values()))
    assert len(first_action_cards) == 3
    assert first_action_cards[0] == "card_focus_plus_two"


def test_m3_card_play_safety_limit_raises_error_without_draw_result() -> None:
    with pytest.raises(BattleScenarioError, match="card_play_safety_limit"):
        BattleEngine().simulate(
            m3_scenario(
                m3_lane_participants(
                    top_ally_deck=[
                        grant_card_play_card("card_focus_1", 1),
                        grant_card_play_card("card_focus_2", 1),
                        grant_card_play_card("card_focus_3", 1),
                    ],
                    mid_ally_deck=[
                        m3_damage_card("card_mid_1", 1000),
                        m3_damage_card("card_mid_2", 1000),
                        m3_damage_card("card_mid_3", 1000),
                    ],
                ),
                rule_config=BattleRuleConfig(
                    initial_hand_size=3,
                    nexus_max_hp=1,
                    simulation_card_play_limit_per_action=2,
                ),
            )
        )


def test_m3_adjacent_and_global_scope_target_living_enemy_characters_only() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[
                    BattleCard(
                        "card_adjacent_plus",
                        0,
                        [
                            BattleEffect(
                                "damage",
                                "enemy",
                                2,
                                scope="adjacent",
                            ),
                            BattleEffect("grant_card_play", "self", 1),
                        ],
                    ),
                    m3_damage_card("card_global", 2, scope="global"),
                ],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(initial_hand_size=2, nexus_max_hp=1),
        )
    )

    adjacent_damage = next(
        event
        for event in replay.events
        if event.event_type == "damage_applied"
        and event.actor_id == "top_ally"
        and event.payload["requested"] == 2
    )
    global_targets = [
        event.target_id
        for event in replay.events
        if event.event_type == "damage_applied"
        and event.actor_id == "top_ally"
        and event.action_index == adjacent_damage.action_index
    ]

    assert adjacent_damage.target_id == "mid_enemy"
    assert "enemy_nexus" not in global_targets


def test_m3_respawn_waits_are_counted_on_own_action_opportunities() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[m3_damage_card("card_defeat_top_enemy", 1000)],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            simulation_safety_limit=20,
            rule_config=BattleRuleConfig(nexus_max_hp=1, respawn_skip_turns=2),
        )
    )

    waits = [
        event
        for event in replay.events
        if event.event_type == "respawn_waited" and event.actor_id == "top_enemy"
    ]

    assert [event.payload["before"] for event in waits[:2]] == [2, 1]


def test_m3_nexus_destroyed_completes_after_action_completed() -> None:
    replay = BattleEngine().simulate(
        m3_scenario(
            m3_lane_participants(
                top_ally_deck=[m3_damage_card("card_break_nexus", 1000)],
                mid_ally_deck=[
                    m3_damage_card("card_mid_1", 1000),
                    m3_damage_card("card_mid_2", 1000),
                    m3_damage_card("card_mid_3", 1000),
                ],
            ),
            rule_config=BattleRuleConfig(nexus_max_hp=1),
        )
    )

    event_types = [event.event_type for event in replay.events]
    assert replay.summary.result == "ally_win"
    assert replay.summary.end_reason == "nexus_destroyed"
    assert "nexus_damaged" in event_types
    assert event_types.index("action_completed", event_types.index("nexus_damaged")) < (
        event_types.index("battle_completed")
    )


def test_m3_safety_limit_is_error_not_draw() -> None:
    with pytest.raises(BattleScenarioError, match="simulation_safety_limit"):
        BattleEngine().simulate(
            m3_scenario(
                m3_lane_participants(
                    top_ally_deck=[m3_damage_card("card_hold", 1, mp_cost=99)],
                    mid_ally_deck=[m3_damage_card("card_hold_mid", 1, mp_cost=99)],
                ),
                simulation_safety_limit=2,
            )
        )


@pytest.mark.parametrize(
    "rule_config",
    [
        BattleRuleConfig(max_hand_size=0),
        BattleRuleConfig(initial_hand_size=8, max_hand_size=7),
        BattleRuleConfig(ally_nexus_position=1000, enemy_nexus_position=-1000),
        BattleRuleConfig(initial_position=1000),
        BattleRuleConfig(simulation_safety_limit=0),
        BattleRuleConfig(simulation_card_play_limit_per_action=0),
    ],
)
def test_m3_rejects_invalid_rule_config(rule_config: BattleRuleConfig) -> None:
    with pytest.raises(BattleScenarioError):
        BattleEngine().simulate(
            m3_scenario(
                m3_lane_participants(
                    mid_ally_deck=[
                        m3_damage_card("card_mid_1", 1000),
                        m3_damage_card("card_mid_2", 1000),
                        m3_damage_card("card_mid_3", 1000),
                    ],
                ),
                rule_config=rule_config,
                simulation_safety_limit=None,
            )
        )


def test_participant_adapter_builds_setup_from_character_master_v2() -> None:
    setup = participant_from_character_master(
        participant_id="top_ally",
        side="ally",
        lane_id="top",
        character_master={
            "id": "character_warrior_001",
            "resources": {"max_hp": 120, "max_mp": 20, "initial_mp": 10},
            "action_resources": {"ds": 10, "mpr": 8, "hpr": 2},
            "combat_stats": {"ad": 12, "ap": 0, "ar": 5, "mr": 3, "push": 50},
        },
        deck=[m3_damage_card("card_hit", 1)],
    )

    assert setup.max_hp == 120
    assert setup.initial_mp == 10
    assert setup.mpr == 8
    assert setup.hpr == 2
    assert setup.ad == 12
    assert setup.push == 50
