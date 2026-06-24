/*
テスト一覧:
- 同一Card IDが複数枚ある手札を表示できる
- 重複Card IDでVue duplicate key warningを発生させない
*/

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, test, vi } from 'vitest'

import ParticipantCard from './ParticipantCard.vue'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const catalog: DisplayCatalog = {
  participants: {
    ally_001: { name: '戦士' },
  },
  cards: {
    card_fire_ball: { name: '火球', mp_cost: 1, description: '敵に12ダメージ' },
  },
}

const participant: ParticipantSnapshot = {
  participant_id: 'ally_001',
  character_master_id: 'character_warrior_001',
  side: 'ally',
  hp: 10,
  max_hp: 10,
  mp: 3,
  max_mp: 5,
  alive: true,
  ds: 20,
  mpr: 1,
  hpr: 0,
  draw_gauge: 40,
  hand: ['card_fire_ball', 'card_fire_ball'],
  draw_pile: [],
  discard_pile: [],
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ParticipantCard', () => {
  test('renders duplicate card ids without duplicate key warning', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined)

    const wrapper = mount(ParticipantCard, {
      props: {
        participant,
        catalog,
        isActor: true,
        isNext: false,
        primaryTarget: null,
      },
    })

    expect(wrapper.findAll('.card-chip')).toHaveLength(2)
    expect(wrapper.text().match(/火球/g)).toHaveLength(2)
    expect(warn).not.toHaveBeenCalledWith(expect.stringContaining('Duplicate keys'))

    wrapper.unmount()
  })
})
