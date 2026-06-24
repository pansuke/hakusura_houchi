/*
テスト一覧:
- Action #0は戦闘開始前として要約する
- card_usedはCatalogの日本語カード名で要約する
- HP・MP変化と次の行動者を表示する
- 使用可能カードがない場合は理由を日本語で表示する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import ActionSummary from './ActionSummary.vue'
import type { BattleEvent, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const catalog: DisplayCatalog = {
  participants: {
    ally_001: { name: '戦士' },
    enemy_001: { name: 'ゴブリン' },
  },
  cards: {
    card_fire_ball: { name: '火球', mp_cost: 1, description: '敵に12ダメージ' },
  },
}

const baseSnapshot: BattleSnapshot = {
  action_index: 1,
  battle_status: 'running',
  battle_result: 'undecided',
  acted_actor_id: 'ally_001',
  next_actor_id: 'enemy_001',
  participants: {
    ally_001: {
      participant_id: 'ally_001',
      character_master_id: 'character_ally_001',
      side: 'ally',
      hp: 32,
      max_hp: 32,
      mp: 2,
      max_mp: 5,
      alive: true,
      ds: 100,
      mpr: 1,
      hpr: 0,
      draw_gauge: 0,
      hand: [],
      draw_pile: [],
      discard_pile: [],
    },
    enemy_001: {
      participant_id: 'enemy_001',
      character_master_id: 'character_enemy_001',
      side: 'enemy',
      hp: 16,
      max_hp: 28,
      mp: 2,
      max_mp: 3,
      alive: true,
      ds: 0,
      mpr: 1,
      hpr: 0,
      draw_gauge: 0,
      hand: [],
      draw_pile: [],
      discard_pile: [],
    },
  },
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
        catalog,
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('戦闘開始前')
    expect(wrapper.text()).not.toContain('① 復活・行動準備')
    expect(wrapper.text()).not.toContain('カード判定前です')
  })

  test('summarizes card action in Japanese', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: baseSnapshot,
        events: [
          event('mana_recovered', { before: 2, requested: 1, applied: 1, after: 3, reason: 'action_right' }, 'ally_001', 'ally_001'),
          event('gauge_changed', { before: 80, gain: 20, trigger_count: 1, after: 0 }, 'ally_001', null),
          event(
            'card_drawn',
            {
              card_id: 'card_fire_ball',
              reason: 'draw_gauge',
              draw_source: 'draw_gauge',
              hand_size_before: 3,
              hand_size_after: 4,
            },
            'ally_001',
            null,
          ),
          event('card_used', { card_id: 'card_fire_ball' }, 'ally_001', 'enemy_001'),
          event('mana_spent', { before: 3, amount: 1, after: 2 }, 'ally_001', null),
          event('damage_applied', { before: 28, requested: 12, applied: 12, after: 16 }),
        ],
        catalog,
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('味方・戦士の行動')
    expect(wrapper.text()).toContain('① 復活・行動準備')
    expect(wrapper.text()).toContain('③ ドロー')
    expect(wrapper.text()).toContain('④ カードアクション')
    expect(wrapper.text()).toContain('⑤ 効果解決')
    expect(wrapper.text()).toContain('⑥ 行動終了')
    expect(wrapper.text()).toContain('MP回復：2 → 3（MPR +1）')
    expect(wrapper.text()).toContain('ドロー権を1回獲得')
    expect(wrapper.text()).toContain('「火球」を引いた')
    expect(wrapper.text()).toContain('「火球」を選択')
    expect(wrapper.text()).toContain('MP：3 → 2')
    expect(wrapper.text()).toContain('敵・ゴブリンに12ダメージ')
    expect(wrapper.text()).toContain('HP：28 → 16')
    expect(wrapper.text()).toContain('次の行動：ゴブリン')
  })

  test('renders unavailable card reason', () => {
    const wrapper = mount(ActionSummary, {
      props: {
        snapshot: baseSnapshot,
        events: [
          event('card_held', {
            card_id: 'card_fire_ball',
            reason: 'insufficient_mana',
            required_mp: 3,
            current_mp: 2,
          }),
        ],
        catalog,
        lastCursor: 2,
      },
    })

    expect(wrapper.text()).toContain('使用できるカードがありませんでした')
    expect(wrapper.text()).toContain('火球：使用不可：MP不足')
    expect(wrapper.text()).toContain('必要MP：3 / 現在MP：2')
  })
})
