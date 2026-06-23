/*
テスト一覧:
- 初期表示でプロトタイプ名と BattleEngine 未実装状態を表示する
- health API が ok を返した場合 backend: ok を表示する
- health API が失敗し続ける場合 backend: error を表示する
- Retryボタンでhealth API確認を再実行する
*/

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, test, vi } from 'vitest'

import App from './App.vue'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
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

  test('renders backend error when health API never recovers', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn().mockRejectedValue(new Error('backend unavailable'))
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(App)
    await vi.runAllTimersAsync()
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('backend: error')
    })

    expect(fetchMock).toHaveBeenCalledTimes(5)
    wrapper.unmount()
  })

  test('retry button runs backend check again', async () => {
    vi.useFakeTimers()
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error('backend unavailable'))
      .mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok', service: 'lane-relay-backend' }),
      })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(App)
    await vi.runAllTimersAsync()
    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('backend: ok')
    })

    await wrapper.get('button').trigger('click')
    await vi.runAllTimersAsync()
    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })

    wrapper.unmount()
  })
})
