<template>
  <details class="card-chip">
    <summary>{{ name }} <span>MP {{ mpCost }}</span></summary>
    <p>{{ description }}</p>
  </details>
</template>

<script setup lang="ts">
defineProps<{
  name: string
  mpCost: number
  description: string
}>()
</script>
