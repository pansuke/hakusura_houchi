<template>
  <section class="lane-track-compact" :class="{ 'lane-engaged': isEngaged }">
    <header>
      <strong>{{ laneId.toUpperCase() }}</strong>
      <span v-if="isEngaged">対面中</span>
    </header>
    <div class="lane-bar">
      <span class="lane-nexus ally">味方</span>
      <span
        v-if="ally?.alive"
        class="lane-marker ally"
        :class="{ actor: ally.participant_id === actorId, target: ally.participant_id === targetId }"
        :style="{ left: `${positionPercent(ally.position)}%` }"
        title="味方"
      >●</span>
      <span
        v-if="enemy?.alive"
        class="lane-marker enemy"
        :class="{ actor: enemy.participant_id === actorId, target: enemy.participant_id === targetId }"
        :style="{ left: `${positionPercent(enemy.position)}%` }"
        title="敵"
      >●</span>
      <span class="lane-center" />
      <span class="lane-nexus enemy">敵</span>
    </div>
    <footer>
      <span>{{ ally?.alive ? ally.position ?? '-' : `復活まで ${ally?.respawn_turns_remaining ?? '-'}` }}</span>
      <span>{{ enemy?.alive ? enemy.position ?? '-' : `復活まで ${enemy?.respawn_turns_remaining ?? '-'}` }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { BattleRuleConfig, ParticipantSnapshot } from '../types/battleReplay'

const props = defineProps<{
  laneId: string
  ally?: ParticipantSnapshot
  enemy?: ParticipantSnapshot
  ruleConfig: BattleRuleConfig
  actorId: string | null
  targetId: string | null
}>()

const isEngaged = computed(
  () =>
    Boolean(props.ally?.alive && props.enemy?.alive) &&
    (props.ally?.engaged_with_participant_id === props.enemy?.participant_id ||
      props.enemy?.engaged_with_participant_id === props.ally?.participant_id ||
      props.ally?.position === props.enemy?.position),
)

function positionPercent(position: number | null | undefined): number {
  const range = props.ruleConfig.enemy_nexus_position - props.ruleConfig.ally_nexus_position
  if (position === null || position === undefined || range <= 0) {
    return 50
  }
  return Math.max(2, Math.min(98, ((position - props.ruleConfig.ally_nexus_position) / range) * 100))
}
</script>
