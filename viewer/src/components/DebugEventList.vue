<template>
  <section class="debug-panel">
    <details>
      <summary>{{ uiLabels.drawDebug }}</summary>
      <ul>
        <li v-for="line in drawLines" :key="line">{{ line }}</li>
      </ul>
      <p v-if="!drawLines.length" class="muted-text">この行動ではドロー進行はありません。</p>
    </details>

    <details>
      <summary>{{ uiLabels.cardDebug }}</summary>
      <ul>
        <li v-for="line in cardLines" :key="line">{{ line }}</li>
      </ul>
      <p v-if="!cardLines.length" class="muted-text">カード試行はありません。</p>
    </details>

    <details>
      <summary>{{ uiLabels.rawDebug }}</summary>
      <div class="debug-participants">
        <p v-for="participant in participantList" :key="participant.participant_id">
          participant_id: {{ participant.participant_id }} / character_master_id:
          {{ participant.character_master_id }} / 山札:
          {{ participant.draw_pile.join(', ') || '-' }} / 捨て札:
          {{ participant.discard_pile.join(', ') || '-' }}
        </p>
      </div>
      <ul class="raw-events">
        <li v-for="event in events" :key="event.event_id">
          <code>
            event_id={{ event.event_id }} sequence={{ event.sequence }}
            type={{ event.event_type }} actor={{ event.actor_id ?? '-' }}
            target={{ event.target_id ?? '-' }} payload={{ event.payload }}
          </code>
        </li>
      </ul>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { cardAttemptDebugLines, drawDebugLines } from '../presentation/battlePresenter'
import { uiLabels } from '../presentation/ja'
import type { BattleEvent, BattleSnapshot, DisplayCatalog } from '../types/battleReplay'

const props = defineProps<{
  events: BattleEvent[]
  catalog: DisplayCatalog
  snapshot: BattleSnapshot
}>()

const drawLines = computed(() => drawDebugLines(props.events, props.catalog))
const cardLines = computed(() => cardAttemptDebugLines(props.events, props.catalog))
const participantList = computed(() => Object.values(props.snapshot.participants))
</script>
