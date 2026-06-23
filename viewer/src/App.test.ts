/*
テスト一覧:
- 初期表示でプロトタイプ名と BattleEngine 未実装状態を表示する
- health API が ok を返した場合 backend: ok を表示する
*/

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, test, vi } from 'vitest'

import App from './App.vue'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  test('renders prototype status labels', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('backend unavailable')),
    )

    const wrapper = mount(App)

    expect(wrapper.text()).toContain('Lane Relay Prototype')
    expect(wrapper.text()).toContain('not implemented')
    wrapper.unmount()
  })

  test('renders backend ok when health API responds ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ status: 'ok', service: 'lane-relay-backend' }),
      })),
    )

    const wrapper = mount(App)
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('backend: ok')
    })
    wrapper.unmount()
  })
})
