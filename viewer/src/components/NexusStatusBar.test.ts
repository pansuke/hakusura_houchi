/*
テスト一覧:
- 味方・敵NexusのHPを同時表示する
- 攻撃対象Nexusを強調する
- HP0のNexusを破壊状態で表示する
- Nexus未設定時も欠損表示で描画できる
*/

import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'

import NexusStatusBar from './NexusStatusBar.vue'

describe('NexusStatusBar', () => {
  test('renders target and destroyed nexus states', () => {
    const wrapper = mount(NexusStatusBar, {
      props: {
        ally: { side: 'ally', hp: 8000, max_hp: 8000, ar: 0, mr: 0 },
        enemy: { side: 'enemy', hp: 0, max_hp: 8000, ar: 0, mr: 0 },
        targetSide: 'enemy',
      },
    })

    expect(wrapper.text()).toContain('8000 / 8000')
    expect(wrapper.text()).toContain('0 / 8000')
    expect(wrapper.find('article.targeted').exists()).toBe(true)
    expect(wrapper.find('article.destroyed').exists()).toBe(true)
  })

  test('renders missing nexus values safely', () => {
    const wrapper = mount(NexusStatusBar, {
      props: { targetSide: null },
    })

    expect(wrapper.text()).toContain('- / -')
    expect(wrapper.find('.targeted').exists()).toBe(false)
    expect(wrapper.find('.destroyed').exists()).toBe(false)
  })
})
