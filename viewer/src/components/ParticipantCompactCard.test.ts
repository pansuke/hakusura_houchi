/*
テスト一覧:
- キャラクター概要には名前・HP・MP・DS・AD・AP・AR・MR・PUSH・位置・手札枚数を表示する
- 行動者・攻撃対象・戦闘不能の状態を視覚識別できる
- カード名やHPR・MPRなどの詳細情報は概要へ表示しない
- クリックするとInspector選択用のparticipant IDを通知する
- SUPPORTは同じカード骨格でHPを持たずMP・DS・MPR・手札を表示する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import ParticipantCompactCard from './ParticipantCompactCard.vue'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const catalog: DisplayCatalog = {
  participants: { ally_001: { name: '戦士' } },
  cards: { card_fire_ball: { name: '火球', mp_cost: 1, description: '敵に12ダメージ' } },
}

const participant: ParticipantSnapshot = {
  participant_id: 'ally_001',
  character_master_id: 'character_warrior_001',
  side: 'ally',
  hp: 24,
  max_hp: 32,
  mp: 3,
  max_mp: 5,
  alive: true,
  ds: 20,
  mpr: 1,
  hpr: 2,
  ad: 18,
  ap: 8,
  ar: 10,
  mr: 6,
  draw_gauge: 60,
  hand: ['card_fire_ball'],
  draw_pile: ['card_fire_ball'],
  discard_pile: [],
  lane_id: 'top',
  position: 200,
  push: 50,
}

describe('ParticipantCompactCard', () => {
  test('renders only battle summary information', () => {
    const wrapper = mount(ParticipantCompactCard, {
      props: { participant, catalog, isActor: true, isNext: false, targetKind: 'attack' },
    })

    expect(wrapper.text()).toContain('戦士')
    expect(wrapper.text()).toContain('24 / 32')
    expect(wrapper.text()).toContain('3 / 5')
    expect(wrapper.text()).toContain('60 / 100')
    expect(wrapper.text()).toContain('PUSH 50')
    expect(wrapper.text()).toContain('POS 200')
    expect(wrapper.text()).toContain('手札 1 / 7')
    expect(wrapper.text()).toContain('AD 18')
    expect(wrapper.text()).toContain('AP 8')
    expect(wrapper.text()).toContain('AR 10')
    expect(wrapper.text()).toContain('MR 6')
    expect(wrapper.text()).toContain('行動中')
    expect(wrapper.text()).toContain('攻撃対象')
    expect(wrapper.text()).not.toContain('火球')
    expect(wrapper.text()).not.toContain('HPR')
    expect(wrapper.text()).not.toContain('MPR')
  })

  test('emits participant id when selected', async () => {
    const wrapper = mount(ParticipantCompactCard, {
      props: { participant, catalog, isActor: false, isNext: true, targetKind: null },
    })

    await wrapper.trigger('click')

    expect(wrapper.emitted('select')).toEqual([['ally_001']])
    expect(wrapper.text()).toContain('次行動')
  })

  test('renders support variant with the shared compact card', () => {
    const wrapper = mount(ParticipantCompactCard, {
      props: {
        participant: {
          ...participant,
          slot_type: 'support',
          hp: null,
          max_hp: null,
          alive: null,
          hpr: null,
          position: null,
          push: null,
        },
        catalog,
        isActor: false,
        isNext: true,
        targetKind: null,
      },
    })

    expect(wrapper.classes()).toContain('participant-compact-support')
    expect(wrapper.text()).toContain('SUPPORT')
    expect(wrapper.text()).toContain('MP3 / 5')
    expect(wrapper.text()).toContain('DS60 / 100')
    expect(wrapper.text()).toContain('MPR +1')
    expect(wrapper.text()).toContain('手札 1 / 7')
    expect(wrapper.text()).not.toContain('HP')
    expect(wrapper.text()).not.toContain('PUSH')
  })
})
