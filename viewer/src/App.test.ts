/*
テスト一覧:
- マウント時にsimulate APIからReplayを読み込んでAction #0を表示する
- Next / Prev / +10 / Last / Firstでcursorを移動できる
- Jumpで任意Actionへ移動できる
- Autoplayは表示位置を進め、終端で停止する
- 操作ロック中は多重操作できない
*/

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, test, vi } from 'vitest'

import App from './App.vue'

const replay = {
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
      event_type: 'damage_applied',
      actor_id: 'ally_001',
      target_id: 'enemy_001',
      payload: { card_id: 'card_fire_ball' },
    },
    {
      event_id: 3,
      action_index: 2,
      sequence: 1,
      event_type: 'battle_completed',
      actor_id: null,
      target_id: null,
      payload: {},
    },
  ],
  snapshots: [
    {
      action_index: 0,
      battle_status: 'running',
      battle_result: 'undecided',
      participants: {
        ally_001: participant('ally_001', 'ally', 20),
        enemy_001: participant('enemy_001', 'enemy', 10),
      },
    },
    {
      action_index: 1,
      battle_status: 'running',
      battle_result: 'undecided',
      participants: {
        ally_001: participant('ally_001', 'ally', 20),
        enemy_001: participant('enemy_001', 'enemy', 4),
      },
    },
    {
      action_index: 2,
      battle_status: 'completed',
      battle_result: 'ally_win',
      participants: {
        ally_001: participant('ally_001', 'ally', 20),
        enemy_001: participant('enemy_001', 'enemy', 0, false),
      },
    },
  ],
  summary: {
    result: 'ally_win',
    end_reason: 'enemy_defeated',
    action_count: 2,
  },
}

function participant(participantId: string, side: string, hp: number, alive = true) {
  return {
    participant_id: participantId,
    side,
    hp,
    max_hp: 20,
    mp: 3,
    max_mp: 5,
    alive,
    draw_gauge: 0,
    mana_gauge: 0,
    health_gauge: 0,
    hand: ['card_fire_ball'],
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
    vi.fn(async () => ({
      ok: true,
      json: async () => replay,
    })),
  )
  const wrapper = mount(App)
  await vi.waitFor(() => {
    expect(wrapper.text()).toContain('Action #0 / 2')
  })
  return wrapper
}

describe('App', () => {
  test('loads replay from simulate API and renders action zero', async () => {
    const wrapper = await mountLoadedApp()

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/battles/simulate',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(wrapper.text()).toContain('ally_001')
    expect(wrapper.text()).toContain('battle_started')

    wrapper.unmount()
  })

  test('moves cursor with replay controls', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper.findAll('button').find((button) => button.text() === 'Next')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('Action #1 / 2')

    await wrapper.findAll('button').find((button) => button.text() === 'Prev')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('Action #0 / 2')

    await wrapper.findAll('button').find((button) => button.text() === '+10')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('Action #2 / 2')

    await wrapper.findAll('button').find((button) => button.text() === 'First')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('Action #0 / 2')

    await wrapper.findAll('button').find((button) => button.text() === 'Last')?.trigger('click')
    await vi.runOnlyPendingTimersAsync()
    expect(wrapper.text()).toContain('Action #2 / 2')

    wrapper.unmount()
  })

  test('jumps to selected action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()
    const input = wrapper.get('input')

    await input.setValue(2)
    await input.trigger('change')
    await vi.runOnlyPendingTimersAsync()

    expect(wrapper.text()).toContain('Action #2 / 2')
    wrapper.unmount()
  })

  test('autoplay advances and stops at the last action', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()

    await wrapper.findAll('button').find((button) => button.text() === 'Auto')?.trigger('click')
    await vi.advanceTimersByTimeAsync(1600)

    expect(wrapper.text()).toContain('Action #2 / 2')
    expect(wrapper.text()).toContain('Auto')
    wrapper.unmount()
  })

  test('ignores repeated operations while animation lock is active', async () => {
    vi.useFakeTimers()
    const wrapper = await mountLoadedApp()
    const nextButton = wrapper.findAll('button').find((button) => button.text() === 'Next')

    await nextButton?.trigger('click')
    await nextButton?.trigger('click')

    expect(wrapper.text()).toContain('Action #1 / 2')
    await vi.runOnlyPendingTimersAsync()
    wrapper.unmount()
  })
})
