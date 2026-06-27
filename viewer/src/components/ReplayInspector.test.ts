/*
テスト一覧:
- Action・Unit・Events・State・Configをタブで切り替える
- ActionとRaw Eventを同時表示せずInspector本文だけを切り替える
- Unitタブでは選択キャラクターの詳細情報を表示する
- Configタブで設定値の変更と保存要求を通知する
- Stateタブで現在SnapshotをJSON表示する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import ReplayInspector from './ReplayInspector.vue'
import type { BattleReplay, BattleRuleConfig } from '../types/battleReplay'

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

const replay: BattleReplay = {
  events: [{ event_id: 1, action_index: 0, sequence: 1, event_type: 'battle_started', actor_id: null, target_id: null, payload: {} }],
  snapshots: [{
    action_index: 0,
    battle_status: 'running',
    battle_result: 'undecided',
    acted_actor_id: null,
    next_actor_id: 'ally_001',
    participants: {
      ally_001: {
        participant_id: 'ally_001', character_master_id: 'character_ally_001', side: 'ally',
        hp: 32, max_hp: 32, mp: 5, max_mp: 5, alive: true, ds: 20, mpr: 1, hpr: 2,
        ad: 18, ap: 8, ar: 10, mr: 6,
        draw_gauge: 40, hand: ['card_fire_ball'], draw_pile: [], discard_pile: [], lane_id: 'top', position: 0, push: 50,
      },
    },
    applied_rule_config: config,
  }],
  summary: { result: 'undecided', end_reason: '', action_count: 0 },
  display_catalog: {
    participants: { ally_001: { name: '戦士' } },
    cards: { card_fire_ball: { name: '火球', mp_cost: 1, description: '敵に12ダメージ' } },
  },
}

describe('ReplayInspector', () => {
  test('switches one inspector body by tabs', async () => {
    const wrapper = mount(ReplayInspector, {
      props: {
        replay,
        snapshot: replay.snapshots[0],
        events: replay.events,
        lastCursor: 0,
        selectedParticipantId: 'ally_001',
        ruleConfig: config,
        isBusy: false,
      },
    })

    expect(wrapper.find('.initial-battle-state').exists()).toBe(true)
    expect(wrapper.find('.debug-panel').exists()).toBe(false)

    await wrapper.get('[data-tab="events"]').trigger('click')
    expect(wrapper.find('.initial-battle-state').exists()).toBe(false)
    expect(wrapper.find('.debug-panel').exists()).toBe(true)

    await wrapper.get('[data-tab="unit"]').trigger('click')
    expect(wrapper.text()).toContain('HPR')
    expect(wrapper.text()).toContain('火球')
  })

  test('emits config changes and save request', async () => {
    const wrapper = mount(ReplayInspector, {
      props: {
        replay,
        snapshot: replay.snapshots[0],
        events: replay.events,
        lastCursor: 0,
        selectedParticipantId: 'ally_001',
        ruleConfig: config,
        isBusy: false,
      },
    })

    await wrapper.get('[data-tab="config"]').trigger('click')
    const inputs = wrapper.findAll('input')
    for (const [index, input] of inputs.entries()) {
      await input.setValue(String(index + 4))
    }
    await wrapper.get('.config-inspector button').trigger('click')

    expect(wrapper.emitted('update:rule-config')).toHaveLength(inputs.length)
    expect(wrapper.emitted('update:rule-config')?.[0]?.[0]).toEqual({ ...config, initial_hand_size: 4 })
    expect(wrapper.emitted('save-config')).toHaveLength(1)
  })

  test('renders current snapshot as state JSON', async () => {
    const wrapper = mount(ReplayInspector, {
      props: {
        replay,
        snapshot: replay.snapshots[0],
        events: replay.events,
        lastCursor: 0,
        selectedParticipantId: null,
        ruleConfig: config,
        isBusy: false,
      },
    })

    await wrapper.get('[data-tab="state"]').trigger('click')

    expect(wrapper.get('.state-inspector').text()).toContain('"action_index": 0')
    expect(wrapper.get('.state-inspector').text()).toContain('"participant_id": "ally_001"')
  })
})
