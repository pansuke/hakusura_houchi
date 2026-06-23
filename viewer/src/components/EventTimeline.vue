<template>
  <section class="events">
    <h2>Action Result</h2>
    <ul class="readable-events">
      <li v-for="event in readableEvents" :key="event.event_id">
        {{ eventText(event) }}
      </li>
    </ul>
    <p v-if="!readableEvents.length" class="muted-text">No readable events for this action.</p>

    <details>
      <summary>Resource Updates ({{ resourceEvents.length }})</summary>
      <ul>
        <li v-for="event in resourceEvents" :key="event.event_id">
          {{ eventText(event) }}
        </li>
      </ul>
    </details>

    <details>
      <summary>Raw Events ({{ events.length }})</summary>
      <ul class="raw-events">
        <li v-for="event in events" :key="event.event_id">
          {{ eventText(event) }}
          <code>{{ event.payload }}</code>
        </li>
      </ul>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { BattleEvent } from '../types/battleReplay'

const props = defineProps<{
  events: BattleEvent[]
}>()

const readableTypes = new Set([
  'card_used',
  'mana_spent',
  'damage_applied',
  'health_recovered',
  'mana_gained',
  'card_drawn',
  'character_defeated',
  'battle_completed',
])

const resourceTypes = new Set(['action_started', 'gauge_changed', 'card_attempted', 'card_held', 'action_completed'])

const readableEvents = computed(() => props.events.filter((event) => readableTypes.has(event.event_type)))
const resourceEvents = computed(() => props.events.filter((event) => resourceTypes.has(event.event_type)))

function eventText(event: BattleEvent): string {
  switch (event.event_type) {
    case 'card_used':
      return `${event.actor_id ?? 'system'} used ${payloadText(event, 'card_id')}`
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
    case 'gauge_changed':
      return `${event.actor_id ?? 'system'} ${payloadText(event, 'gauge_type')} gauge: ${payloadNumber(
        event,
        'before',
      )} + ${payloadNumber(event, 'gain')} -> ${payloadNumber(event, 'after')} (${payloadNumber(
        event,
        'trigger_count',
      )} trigger)`
    case 'card_held':
      return `${event.actor_id ?? 'system'} held ${payloadText(event, 'card_id')}: ${payloadText(
        event,
        'reason',
      )}`
    default:
      return `${event.event_type}: ${event.actor_id ?? 'system'}`
  }
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
