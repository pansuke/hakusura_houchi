<template>
  <section class="action-summary">
    <div>
      <p class="summary-kicker">Action {{ snapshot.action_index }} / {{ lastCursor }}</p>
      <h2>{{ actorLine }}</h2>
    </div>
    <ul class="summary-list">
      <li v-for="line in summaryLines" :key="line">{{ line }}</li>
    </ul>
    <p class="next-line">Next: {{ snapshot.next_actor_id ?? '-' }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { BattleEvent, BattleSnapshot } from '../types/battleReplay'

const props = defineProps<{
  snapshot: BattleSnapshot
  events: BattleEvent[]
  lastCursor: number
}>()

const actorLine = computed(() => {
  const actorId = props.snapshot.acted_actor_id ?? firstActorId.value
  return actorId ? `${actorId} acted` : 'Battle ready'
})

const firstActorId = computed(() => props.events.find((event) => event.actor_id)?.actor_id ?? null)

const summaryLines = computed(() => {
  if (props.snapshot.action_index === 0) {
    return ['Initial state before the first action.']
  }
  const lines: string[] = []
  for (const event of props.events) {
    const line = summaryLine(event)
    if (line) {
      lines.push(line)
    }
  }
  return lines.length ? lines : ['No card resolved in this action.']
})

function summaryLine(event: BattleEvent): string | null {
  switch (event.event_type) {
    case 'card_used': {
      const targetId = event.target_id ?? attemptedTarget(event)
      return `${event.actor_id ?? 'system'} used ${payloadText(event, 'card_id')}${
        targetId ? ` on ${targetId}` : ''
      }`
    }
    case 'mana_spent':
      return `${event.actor_id ?? 'system'} spent ${payloadNumber(event, 'amount')} MP`
    case 'damage_applied':
      return `${event.target_id ?? 'target'} took ${payloadNumber(event, 'amount')} damage`
    case 'health_recovered':
      return `${event.target_id ?? 'target'} recovered ${payloadNumber(event, 'amount')} HP`
    case 'mana_gained':
      return `${event.actor_id ?? 'system'} gained ${payloadNumber(event, 'amount')} MP`
    case 'card_drawn':
      return `${event.actor_id ?? 'system'} drew ${payloadText(event, 'card_id')}`
    case 'character_defeated':
      return `${event.actor_id ?? 'target'} was defeated`
    case 'battle_completed':
      return `Battle completed: ${payloadText(event, 'result')}`
    default:
      return null
  }
}

function attemptedTarget(cardUsedEvent: BattleEvent): string | null {
  const cardId = cardUsedEvent.payload.card_id
  return (
    props.events.find(
      (event) =>
        event.event_type === 'card_attempted' &&
        event.actor_id === cardUsedEvent.actor_id &&
        event.payload.card_id === cardId,
    )?.target_id ?? null
  )
}

function payloadText(event: BattleEvent, key: string): string {
  const value = event.payload[key]
  return typeof value === 'string' ? value : '-'
}

function payloadNumber(event: BattleEvent, key: string): number {
  const value = event.payload[key]
  return typeof value === 'number' ? value : 0
}
</script>
