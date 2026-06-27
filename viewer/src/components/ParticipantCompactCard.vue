<template>
  <button
    class="participant-compact"
    :class="{
      'participant-compact-actor': isActor,
      'participant-compact-next': isNext,
      'participant-compact-support': isSupport,
      'participant-compact-defeated': participant.alive === false,
      'participant-compact-attack-target': targetKind === 'attack',
      'participant-compact-heal-target': targetKind === 'heal',
    }"
    type="button"
    @click="emit('select', participant.participant_id)"
  >
    <span class="compact-heading">
      <strong>{{ participantName(catalog, participant.participant_id) }}</strong>
      <span v-if="participant.alive === false" class="compact-state defeated">戦闘不能</span>
      <span v-else-if="isActor" class="compact-state actor">行動中</span>
      <span v-else-if="isNext" class="compact-state next">次行動</span>
      <span v-if="targetKind === 'attack'" class="compact-state target">攻撃対象</span>
      <span v-else-if="targetKind === 'heal'" class="compact-state heal">回復対象</span>
    </span>

    <span v-if="isSupport" class="compact-role-row">
      <span>ROLE</span>
      <strong class="compact-role-value">SUPPORT</strong>
      <b>支援専任</b>
    </span>
    <span v-else class="compact-gauge-row">
      <span>HP</span>
      <span class="compact-gauge"><i class="hp-fill" :style="{ width: `${hpPercent}%` }" /></span>
      <b>{{ participant.hp ?? '-' }} / {{ participant.max_hp ?? '-' }}</b>
    </span>
    <span class="compact-gauge-row">
      <span>MP</span>
      <span class="compact-gauge"><i class="mp-fill" :style="{ width: `${mpPercent}%` }" /></span>
      <b>{{ participant.mp }} / {{ participant.max_mp }}</b>
    </span>
    <span class="compact-gauge-row">
      <span>DS</span>
      <span class="compact-gauge"><i class="ds-fill" :style="{ width: `${drawPercent}%` }" /></span>
      <b>{{ participant.draw_gauge }} / 100</b>
    </span>

    <span class="compact-meta">
      <span v-if="isSupport">MPR +{{ participant.mpr }}</span>
      <span v-else>PUSH {{ participant.push ?? '-' }}</span>
      <span v-if="!isSupport">POS {{ participant.position ?? '-' }}</span>
      <span>手札 {{ participant.hand.length }} / {{ maxHandSize }}</span>
    </span>
    <span class="compact-combat-stats">
      <span><small>AD</small> {{ participant.ad }}</span>
      <span><small>AP</small> {{ participant.ap }}</span>
      <span><small>AR</small> {{ participant.ar }}</span>
      <span><small>MR</small> {{ participant.mr }}</span>
    </span>
    <span v-if="participant.alive === false" class="respawn-note">
      復活まで {{ participant.respawn_turns_remaining ?? '-' }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { participantName } from '../presentation/battlePresenter'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const props = withDefaults(
  defineProps<{
    participant: ParticipantSnapshot
    catalog: DisplayCatalog
    isActor: boolean
    isNext: boolean
    targetKind: 'attack' | 'heal' | null
    maxHandSize?: number
  }>(),
  { maxHandSize: 7 },
)

const emit = defineEmits<{
  select: [participantId: string]
}>()

const isSupport = computed(() => props.participant.slot_type === 'support')
const hpPercent = computed(() => percent(props.participant.hp ?? 0, props.participant.max_hp ?? 0))
const mpPercent = computed(() => percent(props.participant.mp, props.participant.max_mp))
const drawPercent = computed(() => Math.max(0, Math.min(100, props.participant.draw_gauge)))

function percent(value: number, maximum: number): number {
  return maximum > 0 ? Math.max(0, Math.min(100, (value / maximum) * 100)) : 0
}
</script>
