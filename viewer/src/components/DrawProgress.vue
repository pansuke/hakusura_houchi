<template>
  <div class="draw-progress">
    <div v-if="ds > 0" class="draw-bar-row">
      <span class="draw-bar" aria-hidden="true">
        <span class="draw-fill" :style="{ width: `${drawGauge}%` }" />
      </span>
      <span>{{ drawGauge }} / 100</span>
    </div>
    <p v-else class="muted-text">ドロー進行なし</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  ds: number
  drawGauge: number
}>()
</script>
