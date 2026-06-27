<template>
  <section class="nexus-status-bar" aria-label="Nexus status">
    <article :class="{ targeted: targetSide === 'ally', destroyed: ally?.hp === 0 }">
      <header><strong>味方Nexus</strong><span>{{ ally?.hp ?? '-' }} / {{ ally?.max_hp ?? '-' }}</span></header>
      <span class="nexus-health"><i :style="{ width: `${healthPercent(ally)}%` }" /></span>
    </article>
    <div class="nexus-divider">LANE RELAY</div>
    <article :class="{ targeted: targetSide === 'enemy', destroyed: enemy?.hp === 0 }">
      <header><strong>敵Nexus</strong><span>{{ enemy?.hp ?? '-' }} / {{ enemy?.max_hp ?? '-' }}</span></header>
      <span class="nexus-health enemy"><i :style="{ width: `${healthPercent(enemy)}%` }" /></span>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { NexusSnapshot } from '../types/battleReplay'

defineProps<{
  ally?: NexusSnapshot
  enemy?: NexusSnapshot
  targetSide: 'ally' | 'enemy' | null
}>()

function healthPercent(nexus: NexusSnapshot | undefined): number {
  return nexus && nexus.max_hp > 0 ? Math.max(0, Math.min(100, (nexus.hp / nexus.max_hp) * 100)) : 0
}
</script>
