<template>
  <article
    class="combatant"
    :class="{
      'combatant-actor': isActor,
      'combatant-next': isNext,
      'combatant-target': isTarget,
    }"
  >
    <div class="combatant-heading">
      <div>
        <p class="combatant-side">{{ participant.side }}</p>
        <h2>{{ participant.participant_id }}</h2>
      </div>
      <div class="combatant-tags">
        <span v-if="isActor">ACTED</span>
        <span v-if="isNext">NEXT</span>
        <span v-if="isTarget">TARGET</span>
      </div>
    </div>
    <dl>
      <div><dt>HP</dt><dd>{{ participant.hp }} / {{ participant.max_hp }}</dd></div>
      <div><dt>MP</dt><dd>{{ participant.mp }} / {{ participant.max_mp }}</dd></div>
      <div><dt>Alive</dt><dd>{{ participant.alive ? 'yes' : 'no' }}</dd></div>
      <div>
        <dt>Gauge</dt>
        <dd>
          <GaugeDisplay
            :draw-gauge="participant.draw_gauge"
            :mana-gauge="participant.mana_gauge"
            :health-gauge="participant.health_gauge"
          />
        </dd>
      </div>
      <div><dt>Hand</dt><dd>{{ participant.hand.join(', ') || '-' }}</dd></div>
      <div><dt>Draw</dt><dd>{{ participant.draw_pile.length }}</dd></div>
      <div><dt>Discard</dt><dd>{{ participant.discard_pile.length }}</dd></div>
    </dl>
  </article>
</template>

<script setup lang="ts">
import GaugeDisplay from './GaugeDisplay.vue'
import type { ParticipantSnapshot } from '../types/battleReplay'

defineProps<{
  participant: ParticipantSnapshot
  isActor: boolean
  isNext: boolean
  isTarget: boolean
}>()
</script>
