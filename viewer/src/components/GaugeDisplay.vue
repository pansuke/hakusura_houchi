<template>
  <div class="gauge-list">
    <div v-for="gauge in gauges" :key="gauge.label" class="gauge-row">
      <span class="gauge-label">{{ gauge.label }}</span>
      <span class="gauge-bar" aria-hidden="true">
        <span class="gauge-fill" :style="{ width: `${gauge.value}%` }" />
      </span>
      <span class="gauge-value">{{ gauge.value }} / 100</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  drawGauge: number
  manaGauge: number
  healthGauge: number
}>()

const gauges = computed(() => [
  { label: 'Draw', value: props.drawGauge },
  { label: 'Mana', value: props.manaGauge },
  { label: 'Health', value: props.healthGauge },
])
</script>
