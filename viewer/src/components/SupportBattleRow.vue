<template>
  <article class="support-battle-row">
    <ParticipantCompactCard
      v-if="ally"
      :catalog="catalog"
      :is-actor="ally.participant_id === actorId"
      :is-next="ally.participant_id === nextActorId"
      :max-hand-size="maxHandSize"
      :participant="ally"
      :target-kind="null"
      @select="emit('select', $event)"
    />
    <div v-else class="participant-empty">味方SUPPORT未配置</div>

    <section class="support-request-board">
      <header><strong>SUPPORT REQUEST</strong><span>味方 / 敵</span></header>
      <div
        v-for="laneId in laneIds"
        :key="laneId"
        class="support-request-lane"
        :class="{ selected: selectedLane === laneId }"
        :data-lane="laneId"
      >
        <strong>{{ laneId.toUpperCase() }}</strong>
        <span class="request-value ally">{{ requests.ally[laneId] }}</span>
        <span class="request-meter"><i :style="{ width: `${requestPercent(requests.ally[laneId])}%` }" /></span>
        <span class="request-meter enemy"><i :style="{ width: `${requestPercent(requests.enemy[laneId])}%` }" /></span>
        <span class="request-value enemy">{{ requests.enemy[laneId] }}</span>
      </div>
    </section>

    <ParticipantCompactCard
      v-if="enemy"
      :catalog="catalog"
      :is-actor="enemy.participant_id === actorId"
      :is-next="enemy.participant_id === nextActorId"
      :max-hand-size="maxHandSize"
      :participant="enemy"
      :target-kind="null"
      @select="emit('select', $event)"
    />
    <div v-else class="participant-empty enemy">敵SUPPORT未配置</div>
  </article>
</template>

<script setup lang="ts">
import ParticipantCompactCard from './ParticipantCompactCard.vue'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

defineProps<{
  ally?: ParticipantSnapshot
  enemy?: ParticipantSnapshot
  catalog: DisplayCatalog
  requests: Record<'ally' | 'enemy', Record<'top' | 'mid' | 'bot', number>>
  selectedLane: 'top' | 'mid' | 'bot' | null
  actorId: string | null
  nextActorId: string | null
  maxHandSize: number
}>()

const emit = defineEmits<{
  select: [participantId: string]
}>()

const laneIds = ['top', 'mid', 'bot'] as const

function requestPercent(value: number): number {
  return Math.max(0, Math.min(100, (value / 9) * 100))
}
</script>
