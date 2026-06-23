/*
テスト一覧:
- resultLabel / visibleResultLabelは日本語の戦闘状態を返す
- primaryTargetは撃破、ダメージ、回復、MP獲得、card_usedの優先順で対象を返す
- actionSummaryLinesは回復・MP獲得・カードなし理由を表示する
- Catalog未定義IDはIDをfallback表示する
*/

import { describe, expect, test } from 'vitest'

import {
  actionSummaryLines,
  cardDescription,
  cardMpCost,
  cardName,
  participantName,
  primaryTarget,
  recoveryText,
  visibleResultLabel,
} from './battlePresenter'
import type { BattleEvent, BattleReplay, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const catalog: DisplayCatalog = {
  participants: {
    ally_001: { name: '戦士' },
    enemy_001: { name: 'ゴブリン' },
  },
  cards: {
    card_heal: { name: '治癒', mp_cost: 1, description: '自身のHPを3回復' },
  },
}

const snapshot: BattleSnapshot = {
  action_index: 1,
  battle_status: 'running',
  battle_result: 'undecided',
  acted_actor_id: 'ally_001',
  next_actor_id: null,
  participants: {
    ally_001: participant('ally_001', 'ally'),
    enemy_001: participant('enemy_001', 'enemy'),
  },
}

function participant(participantId: string, side: string) {
  return {
    participant_id: participantId,
    character_master_id: `character_${participantId}`,
    side,
    hp: 10,
    max_hp: 20,
    mp: 1,
    max_mp: 3,
    alive: true,
    ds: 0,
    mpr: 0,
    hpr: 0,
    draw_gauge: 0,
    hand: [],
    draw_pile: [],
    discard_pile: [],
  }
}

function event(
  eventType: string,
  payload: Record<string, unknown> = {},
  actorId: string | null = 'ally_001',
  targetId: string | null = 'enemy_001',
): BattleEvent {
  return {
    event_id: 1,
    action_index: 1,
    sequence: 1,
    event_type: eventType,
    actor_id: actorId,
    target_id: targetId,
    payload,
  }
}

describe('battlePresenter', () => {
  test('renders Japanese result labels', () => {
    const replay = {
      summary: { result: 'draw', end_reason: 'max_actions', action_count: 2 },
    } as BattleReplay

    expect(visibleResultLabel(null, false)).toBe('読み込み中')
    expect(visibleResultLabel(replay, false)).toBe('戦闘中')
    expect(visibleResultLabel(replay, true)).toBe('引き分け / 最大行動数')
  })

  test('resolves catalog names and fallbacks', () => {
    expect(participantName(catalog, 'ally_001')).toBe('戦士')
    expect(participantName(catalog, null)).toBe('-')
    expect(participantName(catalog, 'unknown')).toBe('unknown')
    expect(cardName(catalog, 'card_heal')).toBe('治癒')
    expect(cardName(catalog, 'unknown_card')).toBe('unknown_card')
    expect(cardName(catalog, 1)).toBe('-')
    expect(cardDescription(catalog, 'card_heal')).toBe('自身のHPを3回復')
    expect(cardDescription(catalog, 'unknown_card')).toBe('')
    expect(cardMpCost(catalog, 'card_heal')).toBe(1)
    expect(cardMpCost(catalog, 'unknown_card')).toBe(0)
    expect(recoveryText(0)).toBe('なし')
    expect(recoveryText(2)).toBe('+2')
  })

  test('chooses primary targets by priority', () => {
    expect(primaryTarget([event('character_defeated', {}, 'enemy_001', null)])).toEqual({
      participantId: 'enemy_001',
      kind: 'attack',
    })
    expect(primaryTarget([event('damage_applied')])).toEqual({
      participantId: 'enemy_001',
      kind: 'attack',
    })
    expect(
      primaryTarget([event('health_recovered', { reason: 'card_effect' }, 'ally_001', 'ally_001')]),
    ).toEqual({ participantId: 'ally_001', kind: 'heal' })
    expect(primaryTarget([event('mana_gained', {}, 'ally_001', null)])).toEqual({
      participantId: 'ally_001',
      kind: 'heal',
    })
    expect(primaryTarget([event('card_used', { card_id: 'card_heal' })])).toEqual({
      participantId: 'enemy_001',
      kind: 'other',
    })
    expect(primaryTarget([event('mana_recovered', {}, 'ally_001', 'ally_001')])).toBeNull()
  })

  test('summarizes heal and mana gain actions', () => {
    const lines = actionSummaryLines(
      snapshot,
      [
        event('card_used', { card_id: 'card_heal' }, 'ally_001', 'ally_001'),
        event('health_recovered', { before: 10, requested: 3, applied: 3, after: 13, reason: 'card_effect' }, 'ally_001', 'ally_001'),
        event('mana_gained', { before: 1, requested: 1, applied: 1, after: 2 }, 'ally_001', null),
      ],
      catalog,
    )

    expect(lines).toContain('「治癒」を使用')
    expect(lines).toContain('戦士のHP 10 → 13')
    expect(lines).toContain('戦士のMP 1 → 2')
    expect(lines).toContain('次の行動：-')
  })

  test('summarizes no target reason', () => {
    const lines = actionSummaryLines(
      snapshot,
      [event('card_held', { card_id: 'card_heal', reason: 'no_valid_target' })],
      catalog,
    )

    expect(lines).toContain('使用できるカードがありませんでした。')
    expect(lines).toContain('理由：有効な対象なし')
  })
})
