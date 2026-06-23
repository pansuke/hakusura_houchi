import { computed, onUnmounted, ref, watch, type Ref } from 'vue'

import type { BattleReplay } from '../types/battleReplay'

export function useReplayController(replay: Ref<BattleReplay | null>) {
  const cursor = ref(0)
  const jumpTarget = ref(0)
  const autoplay = ref(false)
  const isBusy = ref(false)
  const speedMs = ref(700)
  let autoplayTimer: number | undefined

  const currentSnapshot = computed(() => replay.value?.snapshots[cursor.value] ?? null)
  const lastCursor = computed(() => Math.max(0, (replay.value?.snapshots.length ?? 1) - 1))
  const isAtLast = computed(() => cursor.value >= lastCursor.value)

  function resetCursor(): void {
    cursor.value = 0
    jumpTarget.value = 0
    autoplay.value = false
  }

  async function withLock(operation: () => void): Promise<void> {
    if (isBusy.value) {
      return
    }
    isBusy.value = true
    operation()
    window.setTimeout(() => {
      isBusy.value = false
    }, Math.min(speedMs.value, 300))
  }

  function setCursor(nextCursor: number): void {
    cursor.value = Math.min(Math.max(nextCursor, 0), lastCursor.value)
    jumpTarget.value = cursor.value
    if (isAtLast.value) {
      autoplay.value = false
    }
  }

  function goFirst(): void {
    void withLock(() => setCursor(0))
  }

  function goPrevious(): void {
    void withLock(() => setCursor(cursor.value - 1))
  }

  function goNext(): void {
    void withLock(() => setCursor(cursor.value + 1))
  }

  function stepBy(amount: number): void {
    void withLock(() => setCursor(cursor.value + amount))
  }

  function goLast(): void {
    void withLock(() => setCursor(lastCursor.value))
  }

  function jumpTo(): void {
    void withLock(() => setCursor(Number(jumpTarget.value) || 0))
  }

  function toggleAutoplay(): void {
    autoplay.value = !autoplay.value
  }

  watch([autoplay, speedMs], () => {
    if (autoplayTimer) {
      window.clearInterval(autoplayTimer)
    }
    if (!autoplay.value) {
      return
    }
    autoplayTimer = window.setInterval(() => {
      if (isAtLast.value) {
        autoplay.value = false
        return
      }
      setCursor(cursor.value + 1)
    }, speedMs.value)
  })

  onUnmounted(() => {
    if (autoplayTimer) {
      window.clearInterval(autoplayTimer)
    }
  })

  return {
    cursor,
    jumpTarget,
    autoplay,
    isBusy,
    speedMs,
    currentSnapshot,
    lastCursor,
    isAtLast,
    resetCursor,
    goFirst,
    goPrevious,
    goNext,
    stepBy,
    goLast,
    jumpTo,
    toggleAutoplay,
  }
}
