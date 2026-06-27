/*
テスト一覧:
- マウント時にsimulate APIからReplayを読み込んで行動0を表示する
- 操作ボタンは日本語で表示され、cursorを移動できる
- +100操作は終端へ丸められる
- 演出ロック中は多重操作できない
- 再生速度の変更はReplay結果を変えない
- 最終Action以外では最終結果を表示しない
- 通常表示にはAlive yes / Mana Gauge / Health Gaugeを表示しない
- 通常表示では日本語キャラクター名・カード名・カードチップを表示する
- 今回の行動者、攻撃対象、次の行動者が分かる
- Debug領域を開くと内部IDとRaw Eventを確認できる
- Autoplayは表示位置を進め、終端で停止する
- 戦場はTOP・MID・BOTを1行ずつ表示しInspectorへ詳細を集約する
*/

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, test, vi } from 'vitest'

import App from './App.vue'
import type { BattleReplay, ParticipantSnapshot } from './types/battleReplay'

const replay: BattleReplay = {
  events: [
    {
      event_id: 1,
      action_index: 0,
      sequence: 1,
      event_type: 'battle_started',
      actor_id: null,
      target_id: null,
      payload: {},
    },
    {
      event_id: 2,
      action_index: 1,
      sequence: 1,
      event_type: 'action_started',
      actor_id: 'ally_001',
      target_id: null,
      payload: {},
    },
    {
      event_id: 3,
      action_index: 1,
      sequence: 2,
      event_type: 'mana_recovered',
      actor_id: 'ally_001',
      target_id: 'ally_001',
      payload: { before: 3, requested: 1, applied: 0, after: 3, reason: 'action_right' },
    },
    {
      event_id: 4,
      action_index: 1,
      sequence: 3,
      event_type: 'gauge_changed',
      actor_id: 'ally_001',
      target_id: null,
      payload: { gauge_type: 'draw', before: 80, gain: 20, trigger_count: 1, after: 0 },
    },
    {
      event_id: 5,
      action_index: 1,
      sequence: 4,
      event_type: 'card_drawn',
      actor_id: 'ally_001',
      target_id: null,
      payload: {
        card_id: 'card_fire_ball',
        reason: 'draw_gauge',
        draw_source: 'draw_gauge',
        hand_size_before: 3,
        hand_size_after: 4,
      },
    },
    {
      event_id: 6,
      action_index: 1,
      sequence: 5,
      event_type: 'card_attempted',
      actor_id: 'ally_001',
      target_id: 'enemy_001',
      payload: { card_id: 'card_fire_ball', required_mp: 1, current_mp: 3, playable: true },
    },
    {
      event_id: 7,
      action_index: 1,
      sequence: 6,
      event_type: 'mana_spent',
      actor_id: 'ally_001',
      target_id: null,
      payload: { card_id: 'card_fire_ball', before: 3, amount: 1, after: 2 },
    },
    {
      event_id: 8,
      action_index: 1,
      sequence: 7,
      event_type: 'card_used',
      actor_id: 'ally_001',
      target_id: 'enemy_001',
      payload: { card_id: 'card_fire_ball' },
    },
    {
      event_id: 9,
      action_index: 1,
      sequence: 8,
      event_type: 'damage_applied',
      actor_id: 'ally_001',
      target_id: 'enemy_001',
      payload: { before: 28, requested: 12, applied: 12, after: 16 },
    },
    {
      event_id: 10,
      action_index: 2,
      sequence: 1,
      event_type: 'character_defeated',
      actor_id: 'enemy_001',
      target_id: null,
      payload: { side: 'enemy' },
    },
    {
      event_id: 11,
      action_index: 2,
      sequence: 2,
      event_type: 'action_completed',
      actor_id: 'enemy_001',
      target_id: null,
      payload: { battle_status: 'completed' },
    },
    {
      event_id: 12,
      action_index: 2,
      sequence: 3,
      event_type: 'battle_completed',
      actor_id: null,
      target_id: null,
      payload: { result: 'ally_win', end_reason: 'enemy_defeated' },
    },
  ],
  snapshots: [
    {
      action_index: 0,
      battle_status: 'running',
      battle_result: 'undecided',
      acted_actor_id: null,
      next_actor_id: 'ally_001',
      participants: {
        ally_001: participant('ally_001', 'ally', 32, 32, 3, 5, true, ['card_fire_ball']),
        enemy_001: participant('enemy_001', 'enemy', 28, 28, 2, 3, true, ['card_claw']),
      },
    },
    {
      action_index: 1,
      battle_status: 'running',
      battle_result: 'undecided',
      acted_actor_id: 'ally_001',
      next_actor_id: 'enemy_001',
      participants: {
        ally_001: participant('ally_001', 'ally', 32, 32, 2, 5, true, ['card_focus', 'card_recover']),
        enemy_001: participant('enemy_001', 'enemy', 16, 28, 2, 3, true, ['card_claw']),
      },
    },
    {
      action_index: 2,
      battle_status: 'completed',
      battle_result: 'ally_win',
      acted_actor_id: 'enemy_001',
      next_actor_id: null,
      participants: {
        ally_001: participant('ally_001', 'ally', 32, 32, 2, 5, true, ['card_focus']),
        enemy_001: participant('enemy_001', 'enemy', 0, 28, 2, 3, false, []),
      },
    },
  ],
  summary: {
    result: 'ally_win',
    end_reason: 'enemy_defeated',
    action_count: 2,
  },
  display_catalog: {
    participants: {
      ally_001: { name: '戦士' },
      enemy_001: { name: 'ゴブリン' },
    },
    cards: {
      card_fire_ball: { name: '火球', mp_cost: 1, description: '敵に12ダメージ' },
      card_focus: { name: '精神集中', mp_cost: 0, description: '自身のMPを1回復' },
      card_recover: { name: '治癒', mp_cost: 1, description: '自身のHPを3回復' },
      card_claw: { name: 'ひっかき', mp_cost: 0, description: '敵に5ダメージ' },
    },
  },
}

const ruleConfig = {
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

function participant(
  participantId: string,
  side: string,
  hp: number,
  maxHp: number,
  mp: number,
  maxMp: number,
  alive: boolean,
  hand: string[],
): ParticipantSnapshot {
  return {
    participant_id: participantId,
    character_master_id: `character_${participantId}`,
    side,
    hp,
    max_hp: maxHp,
    mp,
    max_mp: maxMp,
    alive,
    ds: participantId === 'ally_001' ? 100 : 0,
    mpr: 1,
    hpr: 0,
    ad: participantId === 'ally_001' ? 18 : 12,
    ap: participantId === 'ally_001' ? 8 : 4,
    ar: participantId === 'ally_001' ? 10 : 6,
    mr: participantId === 'ally_001' ? 6 : 4,
    draw_gauge: 0,
    hand,
    draw_pile: [],
    discard_pile: [],
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

async function mountLoadedApp() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      return {
        ok: true,
        json: async () => (url.includes('/api/v1/dev/') ? ruleConfig : replay),
      }
    }),
  )
  const wrapper = mount(App)
  await vi.waitFor(() => {
    expect(wrapper.text()).toContain('行動 0 / 2')
  })
  return wrapper
}

describe('App', () => {
  test('loads replay from simulate API and renders initial action', async () => {
    const wrapper = await mountLoadedApp()

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/battles/simulate',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(wrapper.text()).toContain('戦闘開始前')
    expect(wrapper.text()).toContain('最初の行動者：戦士')
    expect(wrapper.text()).toContain('味方・戦士 初期手札')
    expect(wrapper.text()).toContain('火球')
    expect(wrapper.text()).not.toContain('① 復活・行動準備')
    expect(wrapper.text()).toContain('味方・戦士')
    expect(wrapper.text()).toContain('敵・ゴブリン')

    wrapper.unmount()
  })

  test('uses Japanese controls and moves cursor', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    expect(wrapper.text()).toContain('最初')
    expect(wrapper.text()).toContain('前へ')
    expect(wrapper.text()).toContain('次へ')
    expect(wrapper.text()).toContain('自動再生')
    expect(wrapper.text()).toContain('行動番号')
    expect(wrapper.text()).toContain('再生速度')

    await wrapper.findAll('button').find((button) => button.text() === '次へ')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('行動 1 / 2')

    await wrapper.findAll('button').find((button) => button.text() === '最後')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('行動 2 / 2')

    await wrapper.findAll('button').find((button) => button.text() === '前へ')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('行動 1 / 2')

    await wrapper.findAll('button').find((button) => button.text() === '+10')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('行動 2 / 2')

    await wrapper.findAll('button').find((button) => button.text() === '最初')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('行動 0 / 2')

    wrapper.unmount()
  })

  test('hundred forward clamps cursor to last action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper.findAll('button').find((button) => button.text() === '+100')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.text()).toContain('行動 2 / 2')
    wrapper.unmount()
  })

  test('animation lock prevents repeated operation while busy', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()
    const nextButton = wrapper.findAll('button').find((button) => button.text() === '次へ')

    await nextButton?.trigger('click')
    await nextButton?.trigger('click')

    expect(wrapper.text()).toContain('行動 1 / 2')
    expect(wrapper.text()).not.toContain('行動 2 / 2')

    await vi.runOnlyPendingTimersAsync()
    await nextButton?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.text()).toContain('行動 2 / 2')
    wrapper.unmount()
  })

  test('autoplay disables manual movement and jump while pause remains available', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper
      .findAll('button')
      .find((button) => button.text() === '自動再生')
      ?.trigger('click')

    expect(wrapper.findAll('button').find((button) => button.text() === '次へ')?.attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('button').find((button) => button.text() === '前へ')?.attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('button').find((button) => button.text() === '+10')?.attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('button').find((button) => button.text() === '+100')?.attributes('disabled')).toBeDefined()
    expect(wrapper.get('input').attributes('disabled')).toBeDefined()

    await wrapper.findAll('button').find((button) => button.text() === '一時停止')?.trigger('click')
    expect(wrapper.text()).toContain('自動再生')

    wrapper.unmount()
  })

  test('speed changes do not change replay result', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()
    const speedSelect = wrapper.get('select')
    const goLastButton = wrapper.findAll('button').find((button) => button.text() === '最後')
    const goFirstButton = wrapper.findAll('button').find((button) => button.text() === '最初')

    await speedSelect.setValue('250')
    await goLastButton?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.find('.result-badge').text()).toBe('勝利 / 敵を撃破')

    await goFirstButton?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    await speedSelect.setValue('1200')
    await goLastButton?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.find('.result-badge').text()).toBe('勝利 / 敵を撃破')
    expect(fetch).toHaveBeenCalledTimes(2)
    wrapper.unmount()
  })

  test('jumps to selected action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()
    const input = wrapper.get('input')

    await input.setValue(2)
    await input.trigger('change')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.text()).toContain('行動 2 / 2')
    wrapper.unmount()
  })

  test('hides final result until the last action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    expect(wrapper.find('.result-badge').text()).toBe('戦闘中')
    await wrapper.findAll('button').find((button) => button.text() === '最後')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.find('.result-badge').text()).toBe('勝利 / 敵を撃破')
    wrapper.unmount()
  })

  test('normal display hides alive and removed gauges', async () => {
    const wrapper = await mountLoadedApp()
    const normalText = wrapper.find('.battlefield-panel').text()

    expect(normalText).not.toContain('Alive')
    expect(normalText).not.toContain('yes')
    expect(normalText).not.toContain('Mana Gauge')
    expect(normalText).not.toContain('Health Gauge')
    expect(normalText).not.toContain('HPR')
    expect(normalText).not.toContain('MPR')
    wrapper.unmount()
  })

  test('renders Japanese names and card chips in normal display', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper.findAll('button').find((button) => button.text() === '次へ')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    const normalText = wrapper.find('.battlefield-panel').text()
    expect(normalText).toContain('戦士')
    expect(normalText).toContain('ゴブリン')
    expect(normalText).toContain('手札 2 / 7')
    expect(normalText).not.toContain('精神集中')
    expect(normalText).not.toContain('治癒')
    expect(normalText).not.toContain('card_focus')
    expect(normalText).not.toContain('ally_001')
    wrapper.unmount()
  })

  test('shows actor target and next actor without duplicate action result', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper.findAll('button').find((button) => button.text() === '次へ')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.find('.action-summary').text()).toContain('味方・戦士の行動')
    expect(wrapper.find('.action-summary').text()).toContain('① 復活・行動準備')
    expect(wrapper.find('.action-summary').text()).toContain('③ ドロー')
    expect(wrapper.find('.action-summary').text()).toContain('④ カードアクション')
    expect(wrapper.find('.action-summary').text()).toContain('ドロー権を1回獲得')
    expect(wrapper.find('.action-summary').text()).toContain('「火球」を引いた')
    expect(wrapper.find('.action-summary').text()).toContain('「火球」を選択')
    expect(wrapper.find('.action-summary').text()).toContain('敵・ゴブリンに12ダメージ')
    expect(wrapper.find('.action-summary').text()).toContain('次の行動：ゴブリン')
    expect(wrapper.find('.participant-compact-actor').text()).toContain('行動中')
    expect(wrapper.find('.participant-compact-attack-target').text()).toContain('攻撃対象')
    expect(wrapper.findAll('h2').map((heading) => heading.text())).not.toContain('Action Result')
    wrapper.unmount()
  })

  test('shows defeated state only when participant is defeated', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    expect(wrapper.find('.battlefield-panel').text()).not.toContain('戦闘不能')
    await wrapper.findAll('button').find((button) => button.text() === '最後')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.find('.participant-compact-defeated').text()).toContain('戦闘不能')
    wrapper.unmount()
  })

  test('debug area exposes internal ids and raw events', async () => {
    const wrapper = await mountLoadedApp()
    await wrapper.get('[data-tab="events"]').trigger('click')
    const debugText = wrapper.find('.debug-panel').text()

    expect(debugText).toContain('生イベント')
    expect(debugText).toContain('event_id=1')
    expect(debugText).toContain('participant_id: ally_001')
    expect(debugText).toContain('character_master_id: character_ally_001')
    wrapper.unmount()
  })

  test('renders one row per lane and keeps details in inspector', async () => {
    const wrapper = await mountLoadedApp()

    expect(wrapper.findAll('.battle-lane-row')).toHaveLength(3)
    expect(wrapper.findAll('.participant-compact')).toHaveLength(2)
    expect(wrapper.find('.replay-inspector').exists()).toBe(true)
    expect(wrapper.find('.rule-config-panel').exists()).toBe(false)
    expect(wrapper.find('.panel-header').exists()).toBe(false)

    wrapper.unmount()
  })

  test('autoplay advances and stops at the last action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper
      .findAll('button')
      .find((button) => button.text() === '自動再生')
      ?.trigger('click')
    await vi.advanceTimersByTimeAsync(1600)

    expect(wrapper.text()).toContain('行動 2 / 2')
    expect(wrapper.text()).toContain('自動再生')
    expect(wrapper.findAll('button').find((button) => button.text() === '自動再生')?.attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })

  test('shows load failure message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))
    const wrapper = mount(App)

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('リプレイの読み込みに失敗しました')
    })

    wrapper.unmount()
  })
})
