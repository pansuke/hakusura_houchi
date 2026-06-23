<template>
  <section class="action-summary">
    <div>
      <p class="summary-kicker">行動 {{ snapshot.action_index }} / {{ lastCursor }}</p>
      <h2>{{ title }}</h2>
    </div>
    <ul class="summary-list">
      <li v-for="line in lines" :key="line">{{ line }}</li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { actionSummaryLines, actorTitle } from '../presentation/battlePresenter'
import type { BattleEvent, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const props = defineProps<{
  snapshot: BattleSnapshot
  events: BattleEvent[]
  catalog: DisplayCatalog
  lastCursor: number
}>()

const title = computed(() => actorTitle(props.snapshot, props.catalog))
const lines = computed(() => actionSummaryLines(props.snapshot, props.events, props.catalog))
</script>
