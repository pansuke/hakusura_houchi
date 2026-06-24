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
        <button type="button" :disabled="isBusy || autoplay || cursor === 0" @click="goFirst">
          {{ uiLabels.first }}
        </button>
        <button type="button" :disabled="isBusy || autoplay || cursor === 0" @click="goPrevious">
          {{ uiLabels.previous }}
        </button>
        <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="goNext">
          {{ uiLabels.next }}
        </button>
        <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="stepBy(10)">
          {{ uiLabels.tenForward }}
        </button>
        <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="stepBy(100)">
          {{ uiLabels.hundredForward }}
        </button>
        <button type="button" :disabled="isBusy || autoplay || isAtLast" @click="goLast">
          {{ uiLabels.last }}
        </button>
        <button type="button" :disabled="isBusy || !replay || (isAtLast && !autoplay)" @click="toggleAutoplay">
          {{ autoplay ? uiLabels.pause : uiLabels.autoplay }}
        </button>
      </div>

      <div class="jump-row">
        <label>
          {{ uiLabels.jump }}
          <input
            v-model.number="jumpTarget"
            :max="lastCursor"
            :disabled="isBusy || autoplay"
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

      <details class="rule-config-panel">
        <summary>BattleRuleConfig</summary>
        <div class="rule-config-grid">
          <label>
            初期手札
            <input v-model.number="editableRuleConfig.initial_hand_size" min="0" type="number" />
          </label>
          <label>
            最大手札
            <input v-model.number="editableRuleConfig.max_hand_size" min="0" type="number" />
          </label>
          <label>
            DSしきい値
            <input v-model.number="editableRuleConfig.draw_gauge_threshold" min="1" type="number" />
          </label>
          <label>
            復活待ち
            <input v-model.number="editableRuleConfig.respawn_skip_turns" min="0" type="number" />
          </label>
          <label>
            Nexus HP
            <input v-model.number="editableRuleConfig.nexus_max_hp" min="1" type="number" />
          </label>
          <label>
            防御定数
            <input v-model.number="editableRuleConfig.defense_constant" min="1" type="number" />
          </label>
        </div>
        <button type="button" :disabled="isBusy || autoplay" @click="saveRuleConfig">
          設定を保存して再読込
        </button>
      </details>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-else-if="!replay" class="loading-text">{{ uiLabels.loading }}</p>

      <template v-if="currentSnapshot && replay">
        <ActionSummary
          v-if="currentSnapshot.action_index > 0"
          :catalog="replay.display_catalog"
          :events="currentEvents"
          :last-cursor="lastCursor"
          :snapshot="currentSnapshot"
        />
        <InitialBattleState
          v-else
          :catalog="replay.display_catalog"
          :last-cursor="lastCursor"
          :snapshot="currentSnapshot"
        />

        <section v-if="nexusStates.length" class="nexus-row" aria-label="Nexus states">
          <article v-for="nexus in nexusStates" :key="nexus.side" class="nexus-card">
            <p class="combatant-side">{{ nexus.side === 'ally' ? '味方Nexus' : '敵Nexus' }}</p>
            <strong>{{ nexus.hp }} / {{ nexus.max_hp }}</strong>
            <span>AR {{ nexus.ar }} / MR {{ nexus.mr }}</span>
          </article>
        </section>

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
import InitialBattleState from './components/InitialBattleState.vue'
import ParticipantCard from './components/ParticipantCard.vue'
import { useReplayController } from './composables/useReplayController'
import { m3Scenario } from './fixtures/m3Scenario'
import { primaryTarget, visibleResultLabel } from './presentation/battlePresenter'
import { uiLabels } from './presentation/ja'
import type { BattleReplay, BattleRuleConfig } from './types/battleReplay'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const ruleConfigStorageKey = 'lane-relay-m3-rule-config'
const defaultRuleConfig = m3Scenario.rule_config as BattleRuleConfig
const replay = ref<BattleReplay | null>(null)
const errorMessage = ref('')
const editableRuleConfig = ref<BattleRuleConfig>(loadRuleConfig())

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

const sideOrder: Record<string, number> = {
  ally: 0,
  enemy: 1,
}

const laneOrder: Record<string, number> = {
  top: 0,
  mid: 1,
  bot: 2,
}

const participantList = computed(() =>
  Object.values(currentSnapshot.value?.participants ?? {}).sort(
    (left, right) =>
      (laneOrder[left.lane_id ?? ''] ?? 99) - (laneOrder[right.lane_id ?? ''] ?? 99) ||
      (sideOrder[left.side] ?? 99) - (sideOrder[right.side] ?? 99) ||
      left.participant_id.localeCompare(right.participant_id),
  ),
)

const nexusStates = computed(() =>
  Object.values(currentSnapshot.value?.nexus_states ?? {}).sort(
    (left, right) => (sideOrder[left.side] ?? 99) - (sideOrder[right.side] ?? 99),
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
    replay.value = await simulateBattle(apiBaseUrl, {
      ...m3Scenario,
      rule_config: editableRuleConfig.value,
    })
    resetCursor()
  } catch {
    errorMessage.value = uiLabels.loadFailed
  }
}

function loadRuleConfig(): BattleRuleConfig {
  if (typeof window === 'undefined') {
    return { ...defaultRuleConfig }
  }
  const stored = window.localStorage.getItem(ruleConfigStorageKey)
  if (!stored) {
    return { ...defaultRuleConfig }
  }
  try {
    return { ...defaultRuleConfig, ...JSON.parse(stored) } as BattleRuleConfig
  } catch {
    return { ...defaultRuleConfig }
  }
}

function saveRuleConfig(): void {
  window.localStorage.setItem(ruleConfigStorageKey, JSON.stringify(editableRuleConfig.value))
  void loadReplay()
}

onMounted(() => {
  void loadReplay()
})
</script>
