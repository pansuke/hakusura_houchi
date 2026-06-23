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
          <dd :class="backendClass">{{ backendLabel }}</dd>
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

async function checkBackend(): Promise<void> {
  try {
    const response = await fetch(`${apiBaseUrl}/health`)
    const payload = (await response.json()) as HealthResponse
    backendStatus.value = response.ok && payload.status === 'ok' ? 'ok' : 'error'
  } catch {
    backendStatus.value = 'error'
  }
}

onMounted(() => {
  void checkBackend()
})
</script>
