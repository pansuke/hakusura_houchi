/*
テスト一覧:
- 味方・敵SUPPORTのMP・DS・手札を同じ行に表示する
- SUPPORTカードにはHP・HPR・位置・PUSHを表示しない
- 両SideのTOP・MID・BOT支援要請と選択中レーンを表示する
- SUPPORTカードを選択するとUnit Inspector用IDを通知する
- SUPPORT未配置時は空Slotを表示する
- レーナーと同じParticipantCompactCardをSUPPORT派生表示として利用する
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import SupportBattleRow from './SupportBattleRow.vue'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const catalog: DisplayCatalog = {
  participants: {
    support_ally: { name: '司祭' },
    support_enemy: { name: '呪術師' },
  },
  cards: {},
}

function support(participantId: string, side: 'ally' | 'enemy'): ParticipantSnapshot {
  return {
    participant_id: participantId,
    character_master_id: `character_${participantId}`,
    side,
    slot_type: 'support',
    hp: null,
    max_hp: null,
    mp: 4,
    max_mp: 5,
    alive: null,
    ds: 20,
    mpr: 1,
    hpr: null,
    ad: 8,
    ap: 18,
    ar: 4,
    mr: 10,
    draw_gauge: 60,
    hand: ['card_support'],
    draw_pile: [],
    discard_pile: [],
  }
}

describe('SupportBattleRow', () => {
  test('renders support resources and lane requests without lane vitals', () => {
    const wrapper = mount(SupportBattleRow, {
      props: {
        ally: support('support_ally', 'ally'),
        enemy: support('support_enemy', 'enemy'),
        catalog,
        requests: {
          ally: { top: 5, mid: 2, bot: 0 },
          enemy: { top: 1, mid: 4, bot: 3 },
        },
        selectedLane: 'top',
        actorId: 'support_ally',
        nextActorId: 'support_enemy',
        maxHandSize: 7,
      },
    })

    expect(wrapper.text()).toContain('司祭')
    expect(wrapper.text()).toContain('呪術師')
    expect(wrapper.text()).toContain('MP4 / 5')
    expect(wrapper.text()).toContain('DS60 / 100')
    expect(wrapper.text()).toContain('TOP')
    expect(wrapper.text()).toContain('5')
    expect(wrapper.find('[data-lane="top"]').classes()).toContain('selected')
    expect(wrapper.text()).not.toContain('HP')
    expect(wrapper.text()).not.toContain('HPR')
    expect(wrapper.text()).not.toContain('PUSH')
    expect(wrapper.findAll('.participant-compact')).toHaveLength(2)
    expect(wrapper.findAll('.participant-compact-support')).toHaveLength(2)
  })

  test('emits selected support participant', async () => {
    const wrapper = mount(SupportBattleRow, {
      props: {
        ally: support('support_ally', 'ally'),
        enemy: support('support_enemy', 'enemy'),
        catalog,
        requests: {
          ally: { top: 0, mid: 0, bot: 0 },
          enemy: { top: 0, mid: 0, bot: 0 },
        },
        selectedLane: null,
        actorId: null,
        nextActorId: null,
        maxHandSize: 7,
      },
    })

    const cards = wrapper.findAll('.participant-compact')
    await cards[0].trigger('click')
    await cards[1].trigger('click')

    expect(wrapper.emitted('select')).toEqual([['support_ally'], ['support_enemy']])
  })

  test('renders empty slots without support participants', () => {
    const wrapper = mount(SupportBattleRow, {
      props: {
        catalog,
        requests: {
          ally: { top: 0, mid: 0, bot: 0 },
          enemy: { top: 0, mid: 0, bot: 0 },
        },
        selectedLane: null,
        actorId: null,
        nextActorId: null,
        maxHandSize: 7,
      },
    })

    expect(wrapper.text()).toContain('味方SUPPORT未配置')
    expect(wrapper.text()).toContain('敵SUPPORT未配置')
  })
})
