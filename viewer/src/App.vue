<template>
  <main class="app-shell">
    <section class="status-panel replay-panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">Lane Relay Replay</p>
          <h1>{{ uiLabels.appTitle }}</h1>
        </div>
        <div class="result-badge">{{ resultLabel }}</div>
      </div>

      <p class="lead">{{ uiLabels.lead }}</p>

      <div class="toolbar">
        <button type="button" :disabled="isBusy || cursor === 0" @click="goFirst">
          {{ uiLabels.first }}
        </button>
        <button type="button" :disabled="isBusy || cursor === 0" @click="goPrevious">
          {{ uiLabels.previous }}
        </button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goNext">
          {{ uiLabels.next }}
        </button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(10)">
          {{ uiLabels.tenForward }}
        </button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(100)">
          {{ uiLabels.hundredForward }}
        </button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goLast">
          {{ uiLabels.last }}
        </button>
        <button type="button" :disabled="isBusy || !replay" @click="toggleAutoplay">
          {{ autoplay ? uiLabels.pause : uiLabels.autoplay }}
        </button>
      </div>

      <div class="jump-row">
        <label>
          {{ uiLabels.jump }}
          <input
            v-model.number="jumpTarget"
            :max="lastCursor"
            min="0"
            type="number"
            @change="jumpTo"
          />
        </label>
        <label>
          {{ uiLabels.speed }}
          <select v-model.number="speedMs">
            <option :value="1200">{{ uiLabels.slow }}</option>
            <option :value="700">{{ uiLabels.normal }}</option>
            <option :value="250">{{ uiLabels.fast }}</option>
          </select>
        </label>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-else-if="!replay" class="loading-text">{{ uiLabels.loading }}</p>

      <template v-if="currentSnapshot && replay">
        <ActionSummary
          :catalog="replay.display_catalog"
          :events="currentEvents"
          :last-cursor="lastCursor"
          :snapshot="currentSnapshot"
        />

        <section class="combatants">
          <ParticipantCard
            v-for="participant in participantList"
            :key="participant.participant_id"
            :catalog="replay.display_catalog"
            :is-actor="participant.participant_id === currentSnapshot.acted_actor_id"
            :is-next="participant.participant_id === currentSnapshot.next_actor_id"
            :participant="participant"
            :primary-target="primaryTargetInfo"
          />
        </section>

        <DebugEventList
          :catalog="replay.display_catalog"
          :events="currentEvents"
          :snapshot="currentSnapshot"
        />
      </template>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { simulateBattle } from './api/battleApi'
import ActionSummary from './components/ActionSummary.vue'
import DebugEventList from './components/DebugEventList.vue'
import ParticipantCard from './components/ParticipantCard.vue'
import { useReplayController } from './composables/useReplayController'
import { m1Scenario } from './fixtures/m1Scenario'
import { primaryTarget, visibleResultLabel } from './presentation/battlePresenter'
import { uiLabels } from './presentation/ja'
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

const resultLabel = computed(() => visibleResultLabel(replay.value, isAtLast.value))

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

const primaryTargetInfo = computed(() => primaryTarget(currentEvents.value))

async function loadReplay(): Promise<void> {
  errorMessage.value = ''
  try {
    replay.value = await simulateBattle(apiBaseUrl, m1Scenario)
    resetCursor()
  } catch {
    errorMessage.value = uiLabels.loadFailed
  }
}

onMounted(() => {
  void loadReplay()
})
</script>
