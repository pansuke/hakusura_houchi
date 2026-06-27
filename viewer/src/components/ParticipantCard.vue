<template>
  <article
    class="combatant"
    :class="{
      'combatant-actor': isActor,
      'combatant-defeated': participant.alive === false,
      'combatant-attack-target': targetKind === 'attack',
      'combatant-heal-target': targetKind === 'heal',
    }"
  >
    <div class="combatant-heading">
      <div>
        <p class="combatant-side">{{ title }}</p>
        <h2 v-if="isActor">{{ uiLabels.acted }}</h2>
        <h2 v-else-if="participant.alive === false">{{ uiLabels.defeated }}</h2>
        <h2 v-else-if="isNext">{{ uiLabels.nextActor }}</h2>
      </div>
      <span v-if="targetKind === 'attack'" class="target-note">{{ uiLabels.attackTarget }}</span>
      <span v-else-if="targetKind === 'heal'" class="target-note heal">{{ uiLabels.healTarget }}</span>
    </div>

    <p v-if="participant.alive === false" class="defeated-text">{{ uiLabels.defeated }}</p>

    <dl>
      <div><dt>Slot</dt><dd>{{ participant.slot_type === 'support' ? 'SUPPORT' : 'LANE' }}</dd></div>
      <div v-if="participant.lane_id"><dt>Lane</dt><dd>{{ participant.lane_id.toUpperCase() }}</dd></div>
      <div v-if="participant.position !== null && participant.position !== undefined">
        <dt>Position</dt><dd>{{ participant.position }}</dd>
      </div>
      <div v-if="participant.push !== null && participant.push !== undefined">
        <dt>PUSH</dt><dd>{{ participant.push }}</dd>
      </div>
      <div v-if="participant.respawn_turns_remaining !== null && participant.respawn_turns_remaining !== undefined">
        <dt>復活待ち</dt><dd>{{ participant.respawn_turns_remaining }}</dd>
      </div>
      <div v-if="participant.slot_type !== 'support'"><dt>{{ uiLabels.hp }}</dt><dd>{{ participant.hp }} / {{ participant.max_hp }}</dd></div>
      <div><dt>{{ uiLabels.mp }}</dt><dd>{{ participant.mp }} / {{ participant.max_mp }}</dd></div>
    </dl>

    <section class="stat-section">
      <h3>戦闘能力</h3>
      <dl class="combat-stats-detail">
        <div><dt>AD</dt><dd>{{ participant.ad }}</dd></div>
        <div><dt>AP</dt><dd>{{ participant.ap }}</dd></div>
        <div><dt>AR</dt><dd>{{ participant.ar }}</dd></div>
        <div><dt>MR</dt><dd>{{ participant.mr }}</dd></div>
      </dl>
    </section>

    <section class="stat-section">
      <h3>{{ uiLabels.actionRecovery }}</h3>
      <dl>
        <div v-if="participant.slot_type !== 'support'"><dt>{{ uiLabels.hpr }}</dt><dd>{{ recoveryText(participant.hpr ?? 0) }}</dd></div>
        <div><dt>{{ uiLabels.mpr }}</dt><dd>{{ recoveryText(participant.mpr) }}</dd></div>
      </dl>
    </section>

    <section class="stat-section">
      <h3>{{ uiLabels.draw }}</h3>
      <dl>
        <div><dt>{{ uiLabels.ds }}</dt><dd>{{ recoveryText(participant.ds) }}</dd></div>
        <div>
          <dt>{{ uiLabels.drawProgress }}</dt>
          <dd><DrawProgress :draw-gauge="participant.draw_gauge" :ds="participant.ds" /></dd>
        </div>
      </dl>
    </section>

    <section class="hand-section">
      <h3>{{ uiLabels.hand }}</h3>
      <div class="card-list">
        <CardChip
          v-for="(cardId, index) in participant.hand"
          :key="`${cardId}-${index}`"
          :description="cardDescription(catalog, cardId)"
          :mp-cost="cardMpCost(catalog, cardId)"
          :name="cardName(catalog, cardId)"
        />
        <p v-if="!participant.hand.length" class="muted-text">手札なし</p>
      </div>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import CardChip from './CardChip.vue'
import DrawProgress from './DrawProgress.vue'
import {
  cardDescription,
  cardMpCost,
  cardName,
  participantTitle,
  recoveryText,
  type PrimaryTarget,
} from '../presentation/battlePresenter'
import { uiLabels } from '../presentation/ja'
import type { DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const props = defineProps<{
  participant: ParticipantSnapshot
  catalog: DisplayCatalog
  isActor: boolean
  isNext: boolean
  primaryTarget: PrimaryTarget
}>()

const title = computed(() => participantTitle(props.participant, props.catalog))
const targetKind = computed(() =>
  props.primaryTarget?.kind === 'participant' &&
  props.primaryTarget.participantId === props.participant.participant_id
    ? props.primaryTarget.effectKind
    : null,
)
</script>
