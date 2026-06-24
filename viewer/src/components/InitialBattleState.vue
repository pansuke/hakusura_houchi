<template>
  <section class="action-summary initial-battle-state">
    <div class="summary-header">
      <p class="summary-kicker">行動 0 / {{ lastCursor }}</p>
      <h2>戦闘開始前</h2>
      <p>最初の行動者：{{ firstActorName }}</p>
    </div>

    <div class="initial-hands">
      <section v-for="participant in participantList" :key="participant.participant_id">
        <h3>{{ participantTitle(participant, catalog) }} 初期手札</h3>
        <ul v-if="participant.hand.length">
          <li v-for="(cardId, index) in participant.hand" :key="`${cardId}-${index}`">
            {{ cardName(catalog, cardId) }}
          </li>
        </ul>
        <p v-else class="muted-text">手札なし</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { cardName, participantName, participantTitle } from '../presentation/battlePresenter'
import type { BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const props = defineProps<{
  snapshot: BattleSnapshot
  catalog: DisplayCatalog
  lastCursor: number
}>()

const sideOrder: Record<string, number> = {
  ally: 0,
  enemy: 1,
}

const participantList = computed(() =>
  Object.values(props.snapshot.participants).sort(
    (left, right) =>
      (sideOrder[left.side] ?? 99) - (sideOrder[right.side] ?? 99) ||
      left.participant_id.localeCompare(right.participant_id),
  ),
)

const firstActorName = computed(() => participantName(props.catalog, props.snapshot.next_actor_id))
</script>
