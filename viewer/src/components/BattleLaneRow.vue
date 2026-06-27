<template>
  <article class="battle-lane-row" :data-lane="laneId">
    <ParticipantCompactCard
      v-if="ally"
      :catalog="catalog"
      :is-actor="ally.participant_id === actorId"
      :is-next="ally.participant_id === nextActorId"
      :max-hand-size="ruleConfig.max_hand_size"
      :participant="ally"
      :target-kind="targetKind(ally.participant_id)"
      @select="emit('select', $event)"
    />
    <div v-else class="participant-empty">味方未配置</div>

    <LaneTrack
      :actor-id="actorId"
      :ally="ally"
      :enemy="enemy"
      :lane-id="laneId"
      :rule-config="ruleConfig"
      :target-id="targetParticipantId"
    />

    <ParticipantCompactCard
      v-if="enemy"
      :catalog="catalog"
      :is-actor="enemy.participant_id === actorId"
      :is-next="enemy.participant_id === nextActorId"
      :max-hand-size="ruleConfig.max_hand_size"
      :participant="enemy"
      :target-kind="targetKind(enemy.participant_id)"
      @select="emit('select', $event)"
    />
    <div v-else class="participant-empty enemy">敵未配置</div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import LaneTrack from './LaneTrack.vue'
import ParticipantCompactCard from './ParticipantCompactCard.vue'
import type { PrimaryTarget } from '../presentation/battlePresenter'
import type { BattleRuleConfig, DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

const props = defineProps<{
  laneId: string
  ally?: ParticipantSnapshot
  enemy?: ParticipantSnapshot
  catalog: DisplayCatalog
  ruleConfig: BattleRuleConfig
  actorId: string | null
  nextActorId: string | null
  primaryTarget: PrimaryTarget
}>()

const emit = defineEmits<{
  select: [participantId: string]
}>()

const targetParticipantId = computed(() =>
  props.primaryTarget?.kind === 'participant' ? props.primaryTarget.participantId : null,
)

function targetKind(participantId: string): 'attack' | 'heal' | null {
  return props.primaryTarget?.kind === 'participant' && props.primaryTarget.participantId === participantId
    ? props.primaryTarget.effectKind === 'attack'
      ? 'attack'
      : props.primaryTarget.effectKind === 'heal'
        ? 'heal'
        : null
    : null
}
</script>
