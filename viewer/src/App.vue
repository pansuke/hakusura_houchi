<template>
  <main class="app-shell">
    <section class="status-panel">
      <p class="eyebrow">Lane Relay Prototype</p>
      <h1>Action Index Viewer</h1>
      <p class="lead">
        BattleEngine と Viewer を分離する前提で、まずは開発環境と API 疎通だけを確認します。
      </p>

      <dl class="status-grid">
        <div>
          <dt>Backend</dt>
          <dd :class="backendClass">
            {{ backendLabel }}
            <button type="button" class="retry-button" @click="retryBackendCheck">Retry</button>
          </dd>
        </div>
        <div>
          <dt>API Base</dt>
          <dd>{{ apiBaseUrl }}</dd>
        </div>
        <div>
          <dt>BattleEngine</dt>
          <dd>not implemented</dd>
        </div>
      </dl>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type HealthResponse = {
  status: string
  service: string
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const backendStatus = ref<'checking' | 'ok' | 'error'>('checking')
const maxHealthAttempts = 5
const healthRetryDelayMs = 800

const backendLabel = computed(() => {
  if (backendStatus.value === 'ok') {
    return 'backend: ok'
  }
  if (backendStatus.value === 'error') {
    return 'backend: error'
  }
  return 'checking'
})

const backendClass = computed(() => `status-value status-value-${backendStatus.value}`)

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function checkBackend(attempts = maxHealthAttempts): Promise<void> {
  backendStatus.value = 'checking'

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const isHealthy = await requestHealth()
    if (isHealthy) {
      backendStatus.value = 'ok'
      return
    }
    if (attempt < attempts) {
      await wait(healthRetryDelayMs)
    }
  }

  backendStatus.value = 'error'
}

async function requestHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${apiBaseUrl}/health`)
    const payload = (await response.json()) as HealthResponse
    return response.ok && payload.status === 'ok'
  } catch {
    return false
  }
}

function retryBackendCheck(): void {
  void checkBackend()
}

onMounted(() => {
  void checkBackend()
})
</script>
