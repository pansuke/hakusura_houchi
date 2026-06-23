/*
テスト一覧:
- Action #0は初期状態として要約する
- card_usedはattempted targetを補完して要約する
- 対象や数値がないEventは安全なデフォルトで表示する
- 表示対象EventがないActionはカード未解決として要約する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import ActionSummary from './ActionSummary.vue'
import type { BattleEvent, BattleSnapshot } from '../types/battleReplay'

const baseSnapshot: BattleSnapshot = {
  action_index: 1,
  battle_status: 'running',
  battle_result: 'undecided',
  acted_actor_id: 'ally_001',
  next_actor_id: 'enemy_001',
  participants: {},
}

function event(
  eventType: string,
  payload: Record<string, unknown> = {},
  actorId: string | null = 'ally_001',
  targetId: string | null = 'enemy_001',
): BattleEvent {
  return {
    event_id: Math.floor(Math.random() * 100000),
    action_index: 1,
    sequence: 1,
    event_type: eventType,
    actor_id: actorId,
    target_id: targetId,
    payload,
  }
}

describe('ActionSummary', () => {
  test('renders initial snapshot summary', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: { ...baseSnapshot, action_index: 0, acted_actor_id: null },
        events: [],
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('Battle ready')
    expect(wrapper.text()).toContain('Initial state before the first action.')
  })

  test('summarizes action from events', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: baseSnapshot,
        events: [
          event('card_attempted', { card_id: 'card_fire_ball' }, 'ally_001', 'enemy_001'),
          event('card_used', { card_id: 'card_fire_ball' }, 'ally_001', null),
          event('mana_spent', { amount: 1 }, 'ally_001', null),
          event('damage_applied', { amount: 12 }),
          event('health_recovered', { amount: 3 }),
          event('mana_gained', { amount: 2 }, 'ally_001', null),
          event('card_drawn', { card_id: 'card_focus' }, 'ally_001', null),
          event('character_defeated', {}, 'enemy_001', null),
          event('battle_completed', { result: 'ally_win' }, null, null),
        ],
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('ally_001 used card_fire_ball on enemy_001')
    expect(wrapper.text()).toContain('ally_001 spent 1 MP')
    expect(wrapper.text()).toContain('enemy_001 took 12 damage')
    expect(wrapper.text()).toContain('enemy_001 recovered 3 HP')
    expect(wrapper.text()).toContain('ally_001 gained 2 MP')
    expect(wrapper.text()).toContain('ally_001 drew card_focus')
    expect(wrapper.text()).toContain('enemy_001 was defeated')
    expect(wrapper.text()).toContain('Battle completed: ally_win')
    expect(wrapper.text()).toContain('Next: enemy_001')
  })

  test('uses safe fallback text for missing payloads', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: { ...baseSnapshot, acted_actor_id: null },
        events: [
          event('card_used', {}, null, null),
          event('damage_applied', {}, null, null),
        ],
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('Battle ready')
    expect(wrapper.text()).toContain('system used -')
    expect(wrapper.text()).toContain('target took 0 damage')
  })

  test('renders no card resolved fallback', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: baseSnapshot,
        events: [event('action_started', {}, 'ally_001', null)],
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('No card resolved in this action.')
  })
})
