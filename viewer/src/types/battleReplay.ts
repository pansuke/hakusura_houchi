export type BattleEvent = {
  event_id: number
  action_index: number
  sequence: number
  event_type: string
  actor_id: string | null
  target_id: string | null
  payload: Record<string, unknown>
}

export type ParticipantSnapshot = {
  participant_id: string
  character_master_id: string
  side: string
  hp: number
  max_hp: number
  mp: number
  max_mp: number
  alive: boolean
  ds: number
  mpr: number
  hpr: number
  draw_gauge: number
  hand: string[]
  draw_pile: string[]
  discard_pile: string[]
}

export type BattleSnapshot = {
  action_index: number
  battle_status: string
  battle_result: string
  acted_actor_id: string | null
  next_actor_id: string | null
  participants: Record<string, ParticipantSnapshot>
}

export type BattleReplay = {
  events: BattleEvent[]
  snapshots: BattleSnapshot[]
  summary: {
    result: string
    end_reason: string
    action_count: number
  }
  display_catalog: DisplayCatalog
}

export type DisplayCatalog = {
  participants: Record<string, { name: string }>
  cards: Record<string, { name: string; mp_cost: number; description: string }>
}

export type BattleEffectRequest = {
  effect_type: 'damage' | 'heal' | 'gain_mana' | 'draw_card'
  target: 'self' | 'enemy'
  value: number
}

export type BattleCardRequest = {
  card_id: string
  mp_cost: number
  effects: BattleEffectRequest[]
}

export type BattleParticipantRequest = {
  participant_id: string
  side: 'ally' | 'enemy'
  character_master_id: string
  max_hp: number
  max_mp: number
  initial_hp: number
  initial_mp: number
  ds: number
  mpr: number
  hpr: number
  deck: BattleCardRequest[]
}

export type BattleScenarioRequest = {
  battle_id: string
  participants: BattleParticipantRequest[]
  turn_order: string[]
  max_actions: number
  seed: number
}
