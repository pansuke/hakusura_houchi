<template>
  <section class="action-summary">
    <div class="action-summary-heading">
      <p class="summary-kicker">行動 {{ snapshot.action_index }} / {{ lastCursor }}</p>
      <h2>{{ title }}</h2>
      <ul class="action-highlights">
        <li v-for="line in highlights" :key="line">{{ line }}</li>
      </ul>
    </div>

    <ol class="phase-list" aria-label="Action phases">
      <li
        v-for="phase in phases"
        :key="phase.id"
        class="action-phase"
        :class="`phase-${phase.status}`"
      >
        <details :open="phase.items.some((item) => item.importance === 'primary')">
          <summary class="phase-header">
            <span class="phase-status">{{ statusMark(phase.status) }}</span>
            <h3>{{ phase.title }}</h3>
            <span class="phase-compact-line">{{ compactLine(phase) }}</span>
          </summary>
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
        </details>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import {
  actorTitle,
  buildActionPhases,
  type ActionPhaseStatus,
  type ActionPhaseView,
} from '../presentation/battlePresenter'
import type { BattleEvent, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const props = defineProps<{
  snapshot: BattleSnapshot
  events: BattleEvent[]
  catalog: DisplayCatalog
  lastCursor: number
}>()

const title = computed(() => actorTitle(props.snapshot, props.catalog))
const phases = computed(() => buildActionPhases(props.snapshot, props.events, props.catalog))
const highlights = computed(() =>
  phases.value
    .flatMap((phase) => phase.items.filter((item) => item.importance === 'primary').map((item) => item.label))
    .slice(0, 4),
)

function compactLine(phase: ActionPhaseView): string {
  return phase.items.map((item) => item.label).slice(0, 2).join(' / ')
}

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
