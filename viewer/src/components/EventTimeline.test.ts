/*
テスト一覧:
- Readable Eventは意味のある文章で表示する
- Resource Updatesは折りたたみ内に表示する
- Raw Eventsはpayload付きで確認できる
- Readable Eventがない場合は空表示メッセージを出す
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import EventTimeline from './EventTimeline.vue'
import type { BattleEvent } from '../types/battleReplay'

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

describe('EventTimeline', () => {
  test('renders readable events with event-specific text', () => {
    const wrapper = mount(EventTimeline, {
      props: {
        events: [
          event('card_used', { card_id: 'card_fire_ball' }, 'ally_001', null),
          event('mana_spent', { amount: 1 }, 'ally_001', null),
          event('damage_applied', { amount: 12 }),
          event('health_recovered', { amount: 3 }),
          event('mana_gained', { amount: 2 }, 'ally_001', null),
          event('card_drawn', { card_id: 'card_focus' }, 'ally_001', null),
          event('character_defeated', {}, 'enemy_001', null),
          event('battle_completed', { result: 'ally_win' }, null, null),
        ],
      },
    })

    expect(wrapper.text()).toContain('ally_001 used card_fire_ball')
    expect(wrapper.text()).toContain('ally_001 spent 1 MP')
    expect(wrapper.text()).toContain('enemy_001 took 12 damage')
    expect(wrapper.text()).toContain('enemy_001 recovered 3 HP')
    expect(wrapper.text()).toContain('ally_001 gained 2 MP')
    expect(wrapper.text()).toContain('ally_001 drew card_focus')
    expect(wrapper.text()).toContain('enemy_001 was defeated')
    expect(wrapper.text()).toContain('Battle completed: ally_win')
  })

  test('renders resource and raw events', () => {
    const wrapper = mount(EventTimeline, {
      props: {
        events: [
          event('action_started', {}, 'ally_001', null),
          event('gauge_changed', {
            gauge_type: 'mana',
            before: 0,
            gain: 50,
            trigger_count: 0,
            after: 50,
          }),
          event('card_attempted', { card_id: 'card_fire_ball' }),
          event('card_held', { card_id: 'card_fire_ball', reason: 'insufficient_mana' }),
          event('action_completed', { battle_status: 'running' }, 'ally_001', null),
          event('unknown_debug', {}, null, null),
        ],
      },
    })

    expect(wrapper.text()).toContain('Resource Updates (5)')
    expect(wrapper.text()).toContain('ally_001 mana gauge: 0 + 50 -> 50 (0 trigger)')
    expect(wrapper.text()).toContain('ally_001 held card_fire_ball: insufficient_mana')
    expect(wrapper.text()).toContain('Raw Events (6)')
    expect(wrapper.text()).toContain('unknown_debug: system')
  })

  test('renders empty readable event message', () => {
    const wrapper = mount(EventTimeline, {
      props: { events: [event('action_started', {}, 'ally_001', null)] },
    })

    expect(wrapper.text()).toContain('No readable events for this action.')
  })
})
