import { afterEach, describe, expect, test, vi } from 'vitest'

import { fetchBattleRuleConfig, saveBattleRuleConfig } from './battleApi'

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

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('battleApi rule config', () => {
  test('fetches and saves battle rule config', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ruleConfig })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...ruleConfig, nexus_max_hp: 9000 }) })
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchBattleRuleConfig('http://localhost:8000')).resolves.toEqual(ruleConfig)
    await expect(
      saveBattleRuleConfig('http://localhost:8000', { ...ruleConfig, nexus_max_hp: 9000 }),
    ).resolves.toMatchObject({ nexus_max_hp: 9000 })

    expect(fetchMock).toHaveBeenLastCalledWith(
      'http://localhost:8000/api/v1/dev/battle-rule-config',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  test('throws when rule config API fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))

    await expect(fetchBattleRuleConfig('http://localhost:8000')).rejects.toThrow(
      'failed to load rule config',
    )
    await expect(saveBattleRuleConfig('http://localhost:8000', ruleConfig)).rejects.toThrow(
      'failed to save rule config',
    )
  })
})
