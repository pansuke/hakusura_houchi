/*
テスト一覧:
- 5フェーズが固定順で生成される
- HPR・MPR・DSが行動準備へ分類される
- Draw Gaugeによるcard_drawnがドローへ分類される
- Card Effectによるcard_drawnが効果解決へ分類される
- Draw失敗はdraw_sourceに応じてドローまたは効果解決へ分類される
- 必須Payload欠損は0表示ではなく検出される
- card_heldのMP不足が日本語表示される
- 手札0枚と全カード使用不能を区別する
- Damageのbefore / afterが表示される
- Battle終了時に次の行動者を表示しない
*/

import { describe, expect, test } from 'vitest'

import {
  buildActionPhases,
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
    card_focus: { name: '精神集中', mp_cost: 0, description: '自身のMPを1回復' },
  },
}

const snapshot: BattleSnapshot = {
  action_index: 1,
  battle_status: 'running',
  battle_result: 'undecided',
  acted_actor_id: 'ally_001',
  next_actor_id: 'enemy_001',
  participants: {
    ally_001: participant('ally_001', 'ally', ['card_heal']),
    enemy_001: participant('enemy_001', 'enemy'),
  },
}

function participant(participantId: string, side: string, hand: string[] = []) {
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
    hand,
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
    expect(participantName(catalog, 'unknown')).toBe('名称未設定')
    expect(cardName(catalog, 'card_heal')).toBe('治癒')
    expect(cardName(catalog, 'unknown_card')).toBe('名称未設定')
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

  test('builds fixed ordered phases for a normal action', () => {
    const phases = buildActionPhases(
      snapshot,
      [
        event('health_recovered', { before: 10, requested: 3, applied: 3, after: 13, reason: 'action_right' }, 'ally_001', 'ally_001'),
        event('mana_recovered', { before: 1, requested: 1, applied: 1, after: 2, reason: 'action_right' }, 'ally_001', 'ally_001'),
        event('gauge_changed', { before: 80, gain: 20, trigger_count: 1, after: 0 }, 'ally_001', null),
        event(
          'card_drawn',
          {
            card_id: 'card_focus',
            reason: 'draw_gauge',
            draw_source: 'draw_gauge',
            hand_size_before: 3,
            hand_size_after: 4,
          },
          'ally_001',
          null,
        ),
        event('card_used', { card_id: 'card_heal' }, 'ally_001', 'ally_001'),
        event('mana_spent', { before: 2, amount: 1, after: 1 }, 'ally_001', null),
        event('health_recovered', { before: 10, requested: 3, applied: 3, after: 13, reason: 'card_effect' }, 'ally_001', 'ally_001'),
        event('mana_gained', { before: 1, requested: 1, applied: 1, after: 2 }, 'ally_001', null),
        event('card_drawn', { card_id: 'card_focus', reason: 'card_effect', draw_source: 'card_effect' }, 'ally_001', null),
      ],
      catalog,
    )

    expect(phases.map((phase) => phase.id)).toEqual([
      'standby',
      'draw',
      'card_action',
      'effect_result',
      'action_end',
    ])
    expect(phases[0].items.map((item) => item.label)).toEqual([
      'HP回復：10 → 13（HPR +3）',
      'MP回復：1 → 2（MPR +1）',
      'ドロー進捗：80 + 20 → 0',
      'ドロー権を1回獲得',
    ])
    expect(phases[1].items.map((item) => item.label)).toContain('「精神集中」を引いた')
    expect(phases[1].items.map((item) => item.label)).toContain('手札：3枚 → 4枚')
    expect(phases[2].items.map((item) => item.label)).toContain('「治癒」を選択')
    expect(phases[3].items.map((item) => item.label)).toContain('カード効果で「精神集中」を引いた')
    expect(phases[4].items.map((item) => item.label)).toContain('次の行動：ゴブリン')
  })

  test('separates blocked draw by draw source', () => {
    const gaugeBlocked = buildActionPhases(
      snapshot,
      [
        event('gauge_changed', { before: 80, gain: 20, trigger_count: 1, after: 0 }, 'ally_001', null),
        event(
          'card_draw_blocked',
          { blocked_reason: 'hand_full', draw_source: 'draw_gauge', hand_size: 5, hand_limit: 5 },
          'ally_001',
          null,
        ),
      ],
      catalog,
    )
    expect(gaugeBlocked[1].items.map((item) => item.label)).toContain(
      '手札上限のためカードを引けませんでした',
    )
    expect(gaugeBlocked[1].items.map((item) => item.label)).toContain('手札：5 / 5')
    expect(gaugeBlocked[3].items.map((item) => item.label)).not.toContain(
      '手札上限のためカードを引けませんでした',
    )

    const gaugeEmpty = buildActionPhases(
      snapshot,
      [
        event('gauge_changed', { before: 80, gain: 20, trigger_count: 1, after: 0 }, 'ally_001', null),
        event(
          'card_draw_blocked',
          { blocked_reason: 'empty_deck', draw_source: 'draw_gauge', hand_size: 0 },
          'ally_001',
          null,
        ),
      ],
      catalog,
    )
    expect(gaugeEmpty[1].items.map((item) => item.label)).toContain(
      '引けるカードがありませんでした',
    )

    const effectEmpty = buildActionPhases(
      snapshot,
      [
        event(
          'card_draw_blocked',
          { blocked_reason: 'empty_deck', draw_source: 'card_effect', hand_size: 1 },
          'ally_001',
          null,
        ),
      ],
      catalog,
    )
    expect(effectEmpty[1].items.map((item) => item.label)).not.toContain(
      '引けるカードがありませんでした',
    )
    expect(effectEmpty[3].items.map((item) => item.label)).toContain(
      'カードを1枚引く効果を処理',
    )
    expect(effectEmpty[3].items.map((item) => item.label)).toContain(
      '引けるカードがありませんでした',
    )
    expect(effectEmpty[3].items.map((item) => item.label)).toContain('手札：1枚')

    const effectHandFull = buildActionPhases(
      snapshot,
      [
        event(
          'card_draw_blocked',
          { blocked_reason: 'hand_full', draw_source: 'card_effect', hand_size: 5, hand_limit: 5 },
          'ally_001',
          null,
        ),
      ],
      catalog,
    )
    expect(effectHandFull[3].items.map((item) => item.label)).toContain(
      '手札上限のためカードを引けませんでした',
    )
    expect(effectHandFull[3].items.map((item) => item.label)).toContain('手札：5 / 5')
  })

  test('does not silently render missing required payload as zero', () => {
    expect(() =>
      buildActionPhases(snapshot, [event('damage_applied', { requested: 12, applied: 12 })], catalog),
    ).toThrow('Invalid event payload: damage_applied.before')
  })

  test('separates no draw, no hand, and unusable hand states', () => {
    const noDraw = buildActionPhases(
      snapshot,
      [event('gauge_changed', { before: 20, gain: 20, trigger_count: 0, after: 40 })],
      catalog,
    )
    expect(noDraw[1].status).toBe('skipped')
    expect(noDraw[1].items.map((item) => item.label)).toContain('ドロー権は発生しませんでした')
    expect(noDraw[0].items.map((item) => item.label)).not.toContain('ドロー権は発生しませんでした')

    const emptyHand = buildActionPhases({ ...snapshot, participants: { ally_001: participant('ally_001', 'ally') } }, [], catalog)
    expect(emptyHand[2].items.map((item) => item.label)).toContain('手札にカードがありませんでした')

    const unusable = buildActionPhases(
      snapshot,
      [event('card_held', { card_id: 'card_heal', reason: 'insufficient_mana', required_mp: 3, current_mp: 2 })],
      catalog,
    )
    expect(unusable[2].status).toBe('warning')
    expect(unusable[2].items.map((item) => item.label)).toContain('治癒：使用不可：MP不足')
    expect(unusable[2].items.map((item) => item.detail)).toContain('必要MP：3 / 現在MP：2')
  })

  test('renders damage and battle completion without next actor', () => {
    const phases = buildActionPhases(
      snapshot,
      [
        event('damage_applied', { before: 4, requested: 20, applied: 4, after: 0 }),
        event('character_defeated', {}, 'enemy_001', null),
        event('battle_completed', { result: 'ally_win', end_reason: 'enemy_defeated' }, null, null),
      ],
      catalog,
    )

    expect(phases[3].items.map((item) => item.label)).toContain(
      '敵・ゴブリンに20ダメージを試行 / 実ダメージ：4',
    )
    expect(phases[3].items.map((item) => item.label)).toContain('ゴブリンは戦闘不能になりました')
    expect(phases[4].items.map((item) => item.label)).toEqual([
      '敵チームが全滅しました',
      '結果：味方チームの勝利',
    ])
  })
})
