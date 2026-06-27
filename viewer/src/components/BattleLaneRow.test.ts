/*
テスト一覧:
- 1行の中に味方キャラクター・レーン・敵キャラクターを対応付けて表示する
- 生存キャラクターの現在位置をレーンマーカーへ反映する
- 死亡キャラクターはレーンマーカーを表示せず復活待ちを表示する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import BattleLaneRow from './BattleLaneRow.vue'
import type { BattleRuleConfig, DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const config: BattleRuleConfig = {
  initial_hand_size: 3,
  max_hand_size: 7,
  draw_gauge_threshold: 100,
  respawn_skip_turns: 3,
  ally_nexus_position: -1000,
  enemy_nexus_position: 1000,
  initial_position: 0,
  nexus_max_hp: 8000,
  nexus_ar: 0,
  nexus_mr: 0,
  defense_constant: 100,
  minimum_damage: 1,
  simulation_safety_limit: 1000,
  simulation_card_play_limit_per_action: 100,
}

const catalog: DisplayCatalog = {
  participants: { ally_top: { name: '戦士' }, enemy_top: { name: 'ゴブリン' } },
  cards: {},
}

function participant(participantId: string, side: 'ally' | 'enemy', position: number): ParticipantSnapshot {
  return {
    participant_id: participantId,
    character_master_id: `character_${participantId}`,
    side,
    hp: 20,
    max_hp: 20,
    mp: 2,
    max_mp: 3,
    alive: true,
    ds: 20,
    mpr: 1,
    hpr: 1,
    ad: side === 'ally' ? 18 : 12,
    ap: side === 'ally' ? 8 : 4,
    ar: side === 'ally' ? 10 : 6,
    mr: side === 'ally' ? 6 : 4,
    draw_gauge: 40,
    hand: [],
    draw_pile: [],
    discard_pile: [],
    lane_id: 'top',
    position,
    push: 50,
  }
}

describe('BattleLaneRow', () => {
  test('renders both participants and their lane in one row', () => {
    const wrapper = mount(BattleLaneRow, {
      props: {
        laneId: 'top',
        ally: participant('ally_top', 'ally', -300),
        enemy: participant('enemy_top', 'enemy', 300),
        catalog,
        ruleConfig: config,
        actorId: 'ally_top',
        nextActorId: 'enemy_top',
        primaryTarget: null,
      },
    })

    expect(wrapper.text()).toContain('戦士')
    expect(wrapper.text()).toContain('TOP')
    expect(wrapper.text()).toContain('ゴブリン')
    expect(wrapper.findAll('.lane-marker')).toHaveLength(2)
  })

  test('hides defeated marker and shows respawn wait', () => {
    const enemy = { ...participant('enemy_top', 'enemy', 300), alive: false, respawn_turns_remaining: 2 }
    const wrapper = mount(BattleLaneRow, {
      props: {
        laneId: 'top',
        ally: participant('ally_top', 'ally', -300),
        enemy,
        catalog,
        ruleConfig: config,
        actorId: null,
        nextActorId: null,
        primaryTarget: null,
      },
    })

    expect(wrapper.findAll('.lane-marker')).toHaveLength(1)
    expect(wrapper.text()).toContain('復活まで 2')
  })
})
