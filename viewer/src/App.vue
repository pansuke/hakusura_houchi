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
        <section class="replay-layout" aria-label="Battle replay layout">
          <section class="battlefield-panel" aria-label="Battlefield">
            <div class="team-row enemy-team" aria-label="Enemy team">
              <ParticipantCard
                v-for="participant in enemyParticipants"
                :key="participant.participant_id"
                :catalog="replay.display_catalog"
                :is-actor="participant.participant_id === currentSnapshot.acted_actor_id"
                :is-next="participant.participant_id === currentSnapshot.next_actor_id"
                :participant="participant"
                :primary-target="primaryTargetInfo"
              />
            </div>

            <article v-if="enemyNexus" class="nexus-card nexus-card-enemy">
              <p class="combatant-side">敵Nexus</p>
              <strong>{{ enemyNexus.hp }} / {{ enemyNexus.max_hp }}</strong>
              <span>AR {{ enemyNexus.ar }} / MR {{ enemyNexus.mr }}</span>
            </article>

            <section v-if="laneStates.length" class="lane-map arena-lane-map" aria-label="Lane positions">
              <article v-for="lane in laneStates" :key="lane.laneId" class="lane-track">
                <h3>{{ lane.laneId.toUpperCase() }}</h3>
                <div class="lane-bar">
                  <span class="lane-nexus ally">味方</span>
                  <span
                    v-if="lane.ally?.alive"
                    class="lane-marker ally"
                    :style="{ left: `${lane.allyPositionPercent}%` }"
                    title="味方"
                  >●</span>
                  <span
                    v-if="lane.enemy?.alive"
                    class="lane-marker enemy"
                    :style="{ left: `${lane.enemyPositionPercent}%` }"
                    title="敵"
                  >●</span>
                  <span class="lane-nexus enemy">敵</span>
                </div>
                <p class="lane-meta">
                  味方 {{ lane.ally?.position ?? '-' }} / 敵 {{ lane.enemy?.position ?? '-' }}
                </p>
              </article>
            </section>

            <article v-if="allyNexus" class="nexus-card nexus-card-ally">
              <p class="combatant-side">味方Nexus</p>
              <strong>{{ allyNexus.hp }} / {{ allyNexus.max_hp }}</strong>
              <span>AR {{ allyNexus.ar }} / MR {{ allyNexus.mr }}</span>
            </article>

            <div class="team-row ally-team" aria-label="Ally team">
              <ParticipantCard
                v-for="participant in allyParticipants"
                :key="participant.participant_id"
                :catalog="replay.display_catalog"
                :is-actor="participant.participant_id === currentSnapshot.acted_actor_id"
                :is-next="participant.participant_id === currentSnapshot.next_actor_id"
                :participant="participant"
                :primary-target="primaryTargetInfo"
              />
            </div>
          </section>

          <aside class="replay-log-panel" aria-label="Replay text logs">
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

            <DebugEventList
              :catalog="replay.display_catalog"
              :events="currentEvents"
              :snapshot="currentSnapshot"
            />
          </aside>
        </section>
      </template>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchBattleRuleConfig, saveBattleRuleConfig, simulateBattle } from './api/battleApi'
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
const defaultRuleConfig = m3Scenario.rule_config as BattleRuleConfig
const replay = ref<BattleReplay | null>(null)
const errorMessage = ref('')
const editableRuleConfig = ref<BattleRuleConfig>({ ...defaultRuleConfig })

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

const allyParticipants = computed(() =>
  participantList.value.filter((participant) => participant.side === 'ally'),
)

const enemyParticipants = computed(() =>
  participantList.value.filter((participant) => participant.side === 'enemy'),
)

const nexusStates = computed(() =>
  Object.values(currentSnapshot.value?.nexus_states ?? {}).sort(
    (left, right) => (sideOrder[left.side] ?? 99) - (sideOrder[right.side] ?? 99),
  ),
)

const allyNexus = computed(() => nexusStates.value.find((nexus) => nexus.side === 'ally'))
const enemyNexus = computed(() => nexusStates.value.find((nexus) => nexus.side === 'enemy'))

const laneStates = computed(() => {
  const participants = Object.values(currentSnapshot.value?.participants ?? {})
  const config = currentSnapshot.value?.applied_rule_config ?? defaultRuleConfig
  const range = config.enemy_nexus_position - config.ally_nexus_position
  return ['top', 'mid', 'bot'].map((laneId) => {
    const ally = participants.find(
      (participant) => participant.lane_id === laneId && participant.side === 'ally',
    )
    const enemy = participants.find(
      (participant) => participant.lane_id === laneId && participant.side === 'enemy',
    )
    const toPercent = (position: number | null | undefined) =>
      position === null || position === undefined
        ? 50
        : ((position - config.ally_nexus_position) / range) * 100
    return {
      laneId,
      ally,
      enemy,
      allyPositionPercent: toPercent(ally?.position),
      enemyPositionPercent: toPercent(enemy?.position),
    }
  })
})

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
