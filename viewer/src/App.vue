<template>
  <main class="app-shell">
    <section class="status-panel replay-panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">Lane Relay Replay</p>
          <h1>Action Replay Viewer</h1>
        </div>
        <div class="result-badge">{{ resultLabel }}</div>
      </div>

      <p class="lead">
        BattleEngine が生成した Replay を Action 単位で表示します。Viewer は戦闘計算を行いません。
      </p>

      <div class="toolbar">
        <button type="button" :disabled="isBusy || cursor === 0" @click="goFirst">First</button>
        <button type="button" :disabled="isBusy || cursor === 0" @click="goPrevious">Prev</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goNext">Next</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(10)">+10</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="stepBy(100)">+100</button>
        <button type="button" :disabled="isBusy || isAtLast" @click="goLast">Last</button>
        <button type="button" :disabled="isBusy || !replay" @click="toggleAutoplay">
          {{ autoplay ? 'Pause' : 'Auto' }}
        </button>
      </div>

      <div class="jump-row">
        <label>
          Jump
          <input
            v-model.number="jumpTarget"
            :max="lastCursor"
            min="0"
            type="number"
            @change="jumpTo"
          />
        </label>
        <label>
          Speed
          <select v-model.number="speedMs">
            <option :value="1200">Slow</option>
            <option :value="700">Normal</option>
            <option :value="250">Fast</option>
          </select>
        </label>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-else-if="!replay" class="loading-text">loading replay</p>

      <template v-if="currentSnapshot">
        <div class="action-line">
          Action #{{ currentSnapshot.action_index }} / {{ lastCursor }}
        </div>

        <section class="combatants">
          <article
            v-for="participant in participantList"
            :key="participant.participant_id"
            class="combatant"
          >
            <p class="combatant-side">{{ participant.side }}</p>
            <h2>{{ participant.participant_id }}</h2>
            <dl>
              <div><dt>HP</dt><dd>{{ participant.hp }} / {{ participant.max_hp }}</dd></div>
              <div><dt>MP</dt><dd>{{ participant.mp }} / {{ participant.max_mp }}</dd></div>
              <div><dt>Alive</dt><dd>{{ participant.alive ? 'yes' : 'no' }}</dd></div>
              <div><dt>Gauge</dt><dd>D{{ participant.draw_gauge }} M{{ participant.mana_gauge }} H{{ participant.health_gauge }}</dd></div>
              <div><dt>Hand</dt><dd>{{ participant.hand.join(', ') || '-' }}</dd></div>
              <div><dt>Draw</dt><dd>{{ participant.draw_pile.length }}</dd></div>
              <div><dt>Discard</dt><dd>{{ participant.discard_pile.length }}</dd></div>
            </dl>
          </article>
        </section>

        <section class="events">
          <h2>Events</h2>
          <ol>
            <li v-for="event in currentEvents" :key="event.event_id">
              {{ eventText(event) }}
            </li>
          </ol>
        </section>
      </template>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

type BattleEvent = {
  event_id: number
  action_index: number
  sequence: number
  event_type: string
  actor_id: string | null
  target_id: string | null
  payload: Record<string, unknown>
}

type ParticipantSnapshot = {
  participant_id: string
  side: string
  hp: number
  max_hp: number
  mp: number
  max_mp: number
  alive: boolean
  draw_gauge: number
  mana_gauge: number
  health_gauge: number
  hand: string[]
  draw_pile: string[]
  discard_pile: string[]
}

type BattleSnapshot = {
  action_index: number
  battle_status: string
  battle_result: string
  participants: Record<string, ParticipantSnapshot>
}

type BattleReplay = {
  events: BattleEvent[]
  snapshots: BattleSnapshot[]
  summary: {
    result: string
    end_reason: string
    action_count: number
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const replay = ref<BattleReplay | null>(null)
const cursor = ref(0)
const jumpTarget = ref(0)
const autoplay = ref(false)
const isBusy = ref(false)
const speedMs = ref(700)
const errorMessage = ref('')
let autoplayTimer: number | undefined

const currentSnapshot = computed(() => replay.value?.snapshots[cursor.value] ?? null)
const lastCursor = computed(() => Math.max(0, (replay.value?.snapshots.length ?? 1) - 1))
const isAtLast = computed(() => cursor.value >= lastCursor.value)
const resultLabel = computed(() => {
  if (!replay.value) {
    return 'loading'
  }
  return `${replay.value.summary.result} / ${replay.value.summary.end_reason}`
})
const participantList = computed(() =>
  Object.values(currentSnapshot.value?.participants ?? {}).sort((left, right) =>
    left.participant_id.localeCompare(right.participant_id),
  ),
)
const currentEvents = computed(() =>
  (replay.value?.events ?? []).filter(
    (event) => event.action_index === currentSnapshot.value?.action_index,
  ),
)

function defaultScenario(): Record<string, unknown> {
  return {
    battle_id: 'battle_viewer_001',
    participants: [
      {
        participant_id: 'ally_001',
        side: 'ally',
        character_master_id: 'character_warrior_001',
        max_hp: 32,
        max_mp: 5,
        initial_hp: 32,
        initial_mp: 3,
        ds: 100,
        mrg: 50,
        hrg: 0,
        deck: [
          {
            card_id: 'card_fire_ball',
            mp_cost: 1,
            effects: [{ effect_type: 'damage', target: 'enemy', value: 12 }],
          },
          {
            card_id: 'card_focus',
            mp_cost: 0,
            effects: [{ effect_type: 'gain_mana', target: 'self', value: 1 }],
          },
          {
            card_id: 'card_recover',
            mp_cost: 1,
            effects: [{ effect_type: 'heal', target: 'self', value: 3 }],
          },
        ],
      },
      {
        participant_id: 'enemy_001',
        side: 'enemy',
        character_master_id: 'character_enemy_001',
        max_hp: 28,
        max_mp: 3,
        initial_hp: 28,
        initial_mp: 2,
        ds: 0,
        mrg: 50,
        hrg: 0,
        deck: [
          {
            card_id: 'card_claw',
            mp_cost: 0,
            effects: [{ effect_type: 'damage', target: 'enemy', value: 5 }],
          },
        ],
      },
    ],
    turn_order: ['ally_001', 'enemy_001'],
    max_actions: 12,
    seed: 1,
  }
}

async function loadReplay(): Promise<void> {
  errorMessage.value = ''
  const response = await fetch(`${apiBaseUrl}/api/v1/battles/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(defaultScenario()),
  })
  if (!response.ok) {
    errorMessage.value = 'failed to load replay'
    return
  }
  replay.value = (await response.json()) as BattleReplay
  cursor.value = 0
  jumpTarget.value = 0
}

async function withLock(operation: () => void): Promise<void> {
  if (isBusy.value) {
    return
  }
  isBusy.value = true
  operation()
  window.setTimeout(() => {
    isBusy.value = false
  }, Math.min(speedMs.value, 300))
}

function setCursor(nextCursor: number): void {
  cursor.value = Math.min(Math.max(nextCursor, 0), lastCursor.value)
  jumpTarget.value = cursor.value
  if (isAtLast.value) {
    autoplay.value = false
  }
}

function goFirst(): void {
  void withLock(() => setCursor(0))
}

function goPrevious(): void {
  void withLock(() => setCursor(cursor.value - 1))
}

function goNext(): void {
  void withLock(() => setCursor(cursor.value + 1))
}

function stepBy(amount: number): void {
  void withLock(() => setCursor(cursor.value + amount))
}

function goLast(): void {
  void withLock(() => setCursor(lastCursor.value))
}

function jumpTo(): void {
  void withLock(() => setCursor(Number(jumpTarget.value) || 0))
}

function toggleAutoplay(): void {
  autoplay.value = !autoplay.value
}

function eventText(event: BattleEvent): string {
  const actor = event.actor_id ?? 'system'
  const target = event.target_id ? ` -> ${event.target_id}` : ''
  const card = event.payload.card_id ? ` ${event.payload.card_id}` : ''
  return `${event.sequence}. ${event.event_type}: ${actor}${target}${card}`
}

watch([autoplay, speedMs], () => {
  if (autoplayTimer) {
    window.clearInterval(autoplayTimer)
  }
  if (!autoplay.value) {
    return
  }
  autoplayTimer = window.setInterval(() => {
    if (isAtLast.value) {
      autoplay.value = false
      return
    }
    setCursor(cursor.value + 1)
  }, speedMs.value)
})

onMounted(() => {
  void loadReplay()
})

onUnmounted(() => {
  if (autoplayTimer) {
    window.clearInterval(autoplayTimer)
  }
})
</script>
