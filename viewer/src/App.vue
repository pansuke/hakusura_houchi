<template>
  <main class="app-shell">
    <section class="status-panel replay-panel">
      <header class="replay-topbar">
        <div class="topbar-brand">
          <span class="brand-mark">LR</span>
          <div>
            <p>Lane Relay</p>
            <strong>Action {{ cursor }} / {{ lastCursor }}</strong>
          </div>
        </div>

        <nav class="toolbar" aria-label="Replay controls">
          <button type="button" :disabled="isBusy || autoplay || cursor === 0" @click="goFirst">{{ uiLabels.first }}</button>
          <button type="button" :disabled="isBusy || autoplay || cursor === 0" @click="goPrevious">{{ uiLabels.previous }}</button>
          <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="goNext">{{ uiLabels.next }}</button>
          <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="stepBy(10)">{{ uiLabels.tenForward }}</button>
          <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="stepBy(100)">{{ uiLabels.hundredForward }}</button>
          <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="goLast">{{ uiLabels.last }}</button>
          <button type="button" :disabled="isBusy || !replay || (isAtLast && !autoplay)" @click="toggleAutoplay">
            {{ autoplay ? uiLabels.pause : uiLabels.autoplay }}
          </button>
        </nav>

        <div class="topbar-settings">
          <label>
            {{ uiLabels.jump }}
            <input v-model.number="jumpTarget" :max="lastCursor" :disabled="isBusy || autoplay" min="0" type="number" @change="jumpTo" />
          </label>
          <label>
            {{ uiLabels.speed }}
            <select v-model.number="speedMs">
              <option :value="1200">{{ uiLabels.slow }}</option>
              <option :value="700">{{ uiLabels.normal }}</option>
              <option :value="250">{{ uiLabels.fast }}</option>
            </select>
          </label>
          <span class="result-badge">{{ resultLabel }}</span>
        </div>
      </header>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-else-if="!replay" class="loading-text">{{ uiLabels.loading }}</p>

      <section v-if="currentSnapshot && replay" class="replay-layout" aria-label="Battle replay layout">
        <section class="battlefield-panel" aria-label="Battlefield">
          <NexusStatusBar
            :ally="allyNexus"
            :enemy="enemyNexus"
            :target-side="nexusTargetSide"
          />

          <div class="battlefield-lanes" :class="{ 'has-support': allySupport || enemySupport }">
            <BattleLaneRow
              v-for="lane in laneStates"
              :key="lane.laneId"
              :actor-id="currentSnapshot.acted_actor_id"
              :ally="lane.ally"
              :catalog="replay.display_catalog"
              :enemy="lane.enemy"
              :lane-id="lane.laneId"
              :next-actor-id="currentSnapshot.next_actor_id"
              :primary-target="primaryTargetInfo"
              :rule-config="appliedRuleConfig"
              @select="selectParticipant"
            />
            <SupportBattleRow
              v-if="allySupport || enemySupport"
              :actor-id="currentSnapshot.acted_actor_id"
              :ally="allySupport"
              :catalog="replay.display_catalog"
              :enemy="enemySupport"
              :max-hand-size="appliedRuleConfig.max_hand_size"
              :next-actor-id="currentSnapshot.next_actor_id"
              :requests="supportRequests"
              :selected-lane="selectedSupportLane"
              @select="selectParticipant"
            />
          </div>
        </section>

        <ReplayInspector
          :events="currentEvents"
          :is-busy="isBusy || autoplay"
          :last-cursor="lastCursor"
          :replay="replay"
          :rule-config="editableRuleConfig"
          :selected-participant-id="selectedParticipantId"
          :snapshot="currentSnapshot"
          @save-config="saveRuleConfig"
          @update:rule-config="editableRuleConfig = $event"
        />
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { fetchBattleRuleConfig, saveBattleRuleConfig, simulateBattle } from './api/battleApi'
import BattleLaneRow from './components/BattleLaneRow.vue'
import NexusStatusBar from './components/NexusStatusBar.vue'
import ReplayInspector from './components/ReplayInspector.vue'
import SupportBattleRow from './components/SupportBattleRow.vue'
import { useReplayController } from './composables/useReplayController'
import { m3Scenario } from './fixtures/m3Scenario'
import { primaryTarget, visibleResultLabel } from './presentation/battlePresenter'
import { uiLabels } from './presentation/ja'
import type { BattleReplay, BattleRuleConfig, ParticipantSnapshot } from './types/battleReplay'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const defaultRuleConfig = m3Scenario.rule_config as BattleRuleConfig
const replay = ref<BattleReplay | null>(null)
const errorMessage = ref('')
const editableRuleConfig = ref<BattleRuleConfig>({ ...defaultRuleConfig })
const selectedParticipantId = ref<string | null>(null)

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
const appliedRuleConfig = computed(
  () => currentSnapshot.value?.applied_rule_config ?? editableRuleConfig.value,
)
const currentEvents = computed(() =>
  (replay.value?.events ?? []).filter(
    (event) => event.action_index === currentSnapshot.value?.action_index,
  ),
)
const primaryTargetInfo = computed(() => primaryTarget(currentEvents.value))
const nexusTargetSide = computed(() =>
  primaryTargetInfo.value?.kind === 'nexus' ? primaryTargetInfo.value.side : null,
)
const allySupport = computed(() =>
  Object.values(currentSnapshot.value?.participants ?? {}).find(
    (participant) => participant.slot_type === 'support' && participant.side === 'ally',
  ),
)
const enemySupport = computed(() =>
  Object.values(currentSnapshot.value?.participants ?? {}).find(
    (participant) => participant.slot_type === 'support' && participant.side === 'enemy',
  ),
)
const supportRequests = computed(
  () =>
    currentSnapshot.value?.support_requests ?? {
      ally: { top: 0, mid: 0, bot: 0 },
      enemy: { top: 0, mid: 0, bot: 0 },
    },
)
const selectedSupportLane = computed(() => {
  const event = currentEvents.value.find((candidate) => candidate.event_type === 'support_lane_selected')
  const laneId = event?.payload.selected_lane_id
  return laneId === 'top' || laneId === 'mid' || laneId === 'bot' ? laneId : null
})

const nexusStates = computed(() => Object.values(currentSnapshot.value?.nexus_states ?? {}))
const allyNexus = computed(() => nexusStates.value.find((nexus) => nexus.side === 'ally'))
const enemyNexus = computed(() => nexusStates.value.find((nexus) => nexus.side === 'enemy'))

const laneStates = computed(() => {
  const participants = Object.values(currentSnapshot.value?.participants ?? {})
  const unassigned: Record<'ally' | 'enemy', ParticipantSnapshot[]> = {
    ally: participants.filter(
      (participant) => participant.slot_type !== 'support' && participant.side === 'ally' && !participant.lane_id,
    ),
    enemy: participants.filter(
      (participant) => participant.slot_type !== 'support' && participant.side === 'enemy' && !participant.lane_id,
    ),
  }
  return (['top', 'mid', 'bot'] as const).map((laneId, index) => ({
    laneId,
    ally:
      participants.find((participant) => participant.lane_id === laneId && participant.side === 'ally') ??
      unassigned.ally[index],
    enemy:
      participants.find((participant) => participant.lane_id === laneId && participant.side === 'enemy') ??
      unassigned.enemy[index],
  }))
})

watch(
  currentSnapshot,
  (snapshot) => {
    if (!snapshot) {
      selectedParticipantId.value = null
      return
    }
    if (selectedParticipantId.value && snapshot.participants[selectedParticipantId.value]) {
      return
    }
    selectedParticipantId.value = snapshot.acted_actor_id ?? snapshot.next_actor_id ?? Object.keys(snapshot.participants)[0] ?? null
  },
  { immediate: true },
)

function selectParticipant(participantId: string): void {
  selectedParticipantId.value = participantId
}

async function loadReplay(): Promise<void> {
  errorMessage.value = ''
  try {
    replay.value = await simulateBattle(apiBaseUrl, {
      ...m3Scenario,
      rule_config: editableRuleConfig.value,
    })
    resetCursor()
  } catch {
    errorMessage.value = uiLabels.loadFailed
  }
}

async function loadRuleConfig(): Promise<void> {
  try {
    editableRuleConfig.value = await fetchBattleRuleConfig(apiBaseUrl)
  } catch {
    editableRuleConfig.value = { ...defaultRuleConfig }
  }
}

async function saveRuleConfig(): Promise<void> {
  errorMessage.value = ''
  try {
    editableRuleConfig.value = await saveBattleRuleConfig(apiBaseUrl, editableRuleConfig.value)
    await loadReplay()
  } catch {
    errorMessage.value = uiLabels.loadFailed
  }
}

onMounted(() => {
  void (async () => {
    await loadRuleConfig()
    await loadReplay()
  })()
})
</script>
