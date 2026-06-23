<template>
  <section class="action-summary">
    <div>
      <p class="summary-kicker">行動 {{ snapshot.action_index }} / {{ lastCursor }}</p>
      <h2>{{ title }}</h2>
    </div>

    <ol class="phase-list">
      <li
        v-for="phase in phases"
        :key="phase.id"
        class="action-phase"
        :class="`phase-${phase.status}`"
      >
        <header class="phase-header">
          <span class="phase-status">{{ statusMark(phase.status) }}</span>
          <h3>{{ phase.title }}</h3>
        </header>
        <ul class="phase-items">
          <li
            v-for="item in phase.items"
            :key="`${phase.id}-${item.label}-${item.detail ?? ''}`"
            :class="`phase-item-${item.importance}`"
          >
            <span>{{ item.label }}</span>
            <small v-if="item.detail">{{ item.detail }}</small>
          </li>
        </ul>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { actorTitle, buildActionPhases, type ActionPhaseStatus } from '../presentation/battlePresenter'
import type { BattleEvent, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const props = defineProps<{
  snapshot: BattleSnapshot
  events: BattleEvent[]
  catalog: DisplayCatalog
  lastCursor: number
}>()

const title = computed(() => actorTitle(props.snapshot, props.catalog))
const phases = computed(() => buildActionPhases(props.snapshot, props.events, props.catalog))

function statusMark(status: ActionPhaseStatus): string {
  if (status === 'completed') {
    return '✓'
  }
  if (status === 'warning') {
    return '!'
  }
  if (status === 'failed') {
    return '×'
  }
  return '－'
}
</script>
