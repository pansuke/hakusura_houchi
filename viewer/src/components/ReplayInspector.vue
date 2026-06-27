<template>
  <aside class="replay-inspector" aria-label="Replay inspector">
    <nav class="inspector-tabs" aria-label="Inspector tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        :data-tab="tab.id"
        type="button"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>

    <div class="inspector-body">
      <template v-if="activeTab === 'action'">
        <ActionSummary
          v-if="snapshot.action_index > 0"
          :catalog="replay.display_catalog"
          :events="events"
          :last-cursor="lastCursor"
          :snapshot="snapshot"
        />
        <InitialBattleState
          v-else
          :catalog="replay.display_catalog"
          :last-cursor="lastCursor"
          :snapshot="snapshot"
        />
      </template>

      <ParticipantCard
        v-else-if="activeTab === 'unit' && selectedParticipant"
        :catalog="replay.display_catalog"
        :is-actor="selectedParticipant.participant_id === snapshot.acted_actor_id"
        :is-next="selectedParticipant.participant_id === snapshot.next_actor_id"
        :participant="selectedParticipant"
        :primary-target="primaryTargetInfo"
      />
      <p v-else-if="activeTab === 'unit'" class="inspector-empty">戦場からキャラクターを選択してください。</p>

      <DebugEventList
        v-else-if="activeTab === 'events'"
        :catalog="replay.display_catalog"
        :events="events"
        :snapshot="snapshot"
      />

      <section v-else-if="activeTab === 'state'" class="state-inspector">
        <h2>Battle Snapshot</h2>
        <pre>{{ JSON.stringify(snapshot, null, 2) }}</pre>
      </section>

      <section v-else class="config-inspector">
        <h2>BattleRuleConfig</h2>
        <div class="rule-config-grid">
          <label>初期手札<input :value="ruleConfig.initial_hand_size" min="0" type="number" @input="updateNumber('initial_hand_size', $event)" /></label>
          <label>最大手札<input :value="ruleConfig.max_hand_size" min="0" type="number" @input="updateNumber('max_hand_size', $event)" /></label>
          <label>DSしきい値<input :value="ruleConfig.draw_gauge_threshold" min="1" type="number" @input="updateNumber('draw_gauge_threshold', $event)" /></label>
          <label>復活待ち<input :value="ruleConfig.respawn_skip_turns" min="0" type="number" @input="updateNumber('respawn_skip_turns', $event)" /></label>
          <label>Nexus HP<input :value="ruleConfig.nexus_max_hp" min="1" type="number" @input="updateNumber('nexus_max_hp', $event)" /></label>
          <label>防御定数<input :value="ruleConfig.defense_constant" min="1" type="number" @input="updateNumber('defense_constant', $event)" /></label>
        </div>
        <button type="button" :disabled="isBusy" @click="emit('save-config')">設定を保存して再読込</button>
      </section>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import ActionSummary from './ActionSummary.vue'
import DebugEventList from './DebugEventList.vue'
import InitialBattleState from './InitialBattleState.vue'
import ParticipantCard from './ParticipantCard.vue'
import { primaryTarget } from '../presentation/battlePresenter'
import type { BattleEvent, BattleReplay, BattleRuleConfig, BattleSnapshot } from '../types/battleReplay'

type InspectorTab = 'action' | 'unit' | 'events' | 'state' | 'config'
type EditableRuleKey =
  | 'initial_hand_size'
  | 'max_hand_size'
  | 'draw_gauge_threshold'
  | 'respawn_skip_turns'
  | 'nexus_max_hp'
  | 'defense_constant'

const props = defineProps<{
  replay: BattleReplay
  snapshot: BattleSnapshot
  events: BattleEvent[]
  lastCursor: number
  selectedParticipantId: string | null
  ruleConfig: BattleRuleConfig
  isBusy: boolean
}>()

const emit = defineEmits<{
  'update:rule-config': [ruleConfig: BattleRuleConfig]
  'save-config': []
}>()

const tabs: { id: InspectorTab; label: string }[] = [
  { id: 'action', label: 'Action' },
  { id: 'unit', label: 'Unit' },
  { id: 'events', label: 'Events' },
  { id: 'state', label: 'State' },
  { id: 'config', label: 'Config' },
]
const activeTab = ref<InspectorTab>('action')
const selectedParticipant = computed(() =>
  props.selectedParticipantId ? props.snapshot.participants[props.selectedParticipantId] : undefined,
)
const primaryTargetInfo = computed(() => primaryTarget(props.events))

function updateNumber(key: EditableRuleKey, event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  emit('update:rule-config', { ...props.ruleConfig, [key]: value })
}
</script>
