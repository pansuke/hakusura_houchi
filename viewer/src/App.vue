<template>
  <main class="app-shell">
    <section class="status-panel replay-panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">Lane Relay Replay</p>
          <h1>Action Replay Viewer</h1>
        </div>
        <div class="result-badge">{{ resultLabel }}</div>
      </div>

      <p class="lead">
        BattleEngine が生成した Replay を Action 単位で表示します。Viewer は戦闘計算を行いません。
      </p>

      <div class="toolbar">
        <button type="button" :disabled="isBusy || cursor === 0" @click="goFirst">First</button>
        <button type="button" :disabled="isBusy || cursor === 0" @click="goPrevious">Prev</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goNext">Next</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(10)">+10</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(100)">+100</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goLast">Last</button>
        <button type="button" :disabled="isBusy || !replay" @click="toggleAutoplay">
          {{ autoplay ? 'Pause' : 'Auto' }}
        </button>
      </div>

      <div class="jump-row">
        <label>
          Jump
          <input
            v-model.number="jumpTarget"
            :max="lastCursor"
            min="0"
            type="number"
            @change="jumpTo"
          />
        </label>
        <label>
          Speed
          <select v-model.number="speedMs">
            <option :value="1200">Slow</option>
            <option :value="700">Normal</option>
            <option :value="250">Fast</option>
          </select>
        </label>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-else-if="!replay" class="loading-text">loading replay</p>

      <template v-if="currentSnapshot">
        <ActionSummary
          :events="currentEvents"
          :last-cursor="lastCursor"
          :snapshot="currentSnapshot"
        />

        <section class="combatants">
          <ParticipantCard
            v-for="participant in participantList"
            :key="participant.participant_id"
            :is-actor="participant.participant_id === currentSnapshot.acted_actor_id"
            :is-next="participant.participant_id === currentSnapshot.next_actor_id"
            :is-target="targetIds.has(participant.participant_id)"
            :participant="participant"
          />
        </section>

        <EventTimeline :events="currentEvents" />
      </template>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { simulateBattle } from './api/battleApi'
import ActionSummary from './components/ActionSummary.vue'
import EventTimeline from './components/EventTimeline.vue'
import ParticipantCard from './components/ParticipantCard.vue'
import { useReplayController } from './composables/useReplayController'
import { m1Scenario } from './fixtures/m1Scenario'
import type { BattleReplay } from './types/battleReplay'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const replay = ref<BattleReplay | null>(null)
const errorMessage = ref('')

const {
  cursor,
  jumpTarget,
  autoplay,
  isBusy,
  speedMs,
  currentSnapshot,
  lastCursor,
  isAtLast,
  resetCursor,
  goFirst,
  goPrevious,
  goNext,
  stepBy,
  goLast,
  jumpTo,
  toggleAutoplay,
} = useReplayController(replay)

const resultLabel = computed(() => {
  if (!replay.value) {
    return 'loading'
  }
  if (!isAtLast.value) {
    return 'running'
  }
  return `${replay.value.summary.result} / ${replay.value.summary.end_reason}`
})

const participantList = computed(() =>
  Object.values(currentSnapshot.value?.participants ?? {}).sort((left, right) =>
    left.participant_id.localeCompare(right.participant_id),
  ),
)

const currentEvents = computed(() =>
  (replay.value?.events ?? []).filter(
    (event) => event.action_index === currentSnapshot.value?.action_index,
  ),
)

const targetIds = computed(
  () =>
    new Set(
      currentEvents.value
        .map((event) => event.target_id)
        .filter((targetId): targetId is string => targetId !== null),
    ),
)

async function loadReplay(): Promise<void> {
  errorMessage.value = ''
  try {
    replay.value = await simulateBattle(apiBaseUrl, m1Scenario)
    resetCursor()
  } catch {
    errorMessage.value = 'failed to load replay'
  }
}

onMounted(() => {
  void loadReplay()
})
</script>
