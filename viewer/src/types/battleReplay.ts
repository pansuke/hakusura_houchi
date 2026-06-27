export type BattleEvent = {
  event_id: number
  action_index: number
  sequence: number
  event_type: string
  actor_id: string | null
  target_id: string | null
  payload: Record<string, unknown>
  lane_id?: 'top' | 'mid' | 'bot' | null
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
  ad: number
  ap: number
  ar: number
  mr: number
  draw_gauge: number
  hand: string[]
  draw_pile: string[]
  discard_pile: string[]
  lane_id?: 'top' | 'mid' | 'bot' | null
  position?: number | null
  push?: number | null
  engaged_with_participant_id?: string | null
  respawn_turns_remaining?: number | null
}

export type NexusSnapshot = {
  side: 'ally' | 'enemy'
  hp: number
  max_hp: number
  ar: number
  mr: number
}

export type BattleRuleConfig = {
  initial_hand_size: number
  max_hand_size: number
  draw_gauge_threshold: number
  respawn_skip_turns: number
  ally_nexus_position: number
  enemy_nexus_position: number
  initial_position: number
  nexus_max_hp: number
  nexus_ar: number
  nexus_mr: number
  defense_constant: number
  minimum_damage: number
  simulation_safety_limit: number
  simulation_card_play_limit_per_action: number
}

export type BattleSnapshot = {
  action_index: number
  battle_status: string
  battle_result: string
  acted_actor_id: string | null
  next_actor_id: string | null
  participants: Record<string, ParticipantSnapshot>
  nexus_states?: Record<string, NexusSnapshot>
  applied_rule_config?: BattleRuleConfig | null
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
  effect_type: 'damage' | 'heal' | 'gain_mana' | 'draw_card' | 'grant_card_play'
  target: 'self' | 'enemy'
  value: number
  scope?: 'local' | 'adjacent' | 'global'
  damage_type?: 'physical' | 'magic' | 'true'
  base_damage?: number | null
  scaling?: Record<string, number>[]
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
  lane_id?: 'top' | 'mid' | 'bot' | null
  ad?: number
  ap?: number
  ar?: number
  mr?: number
  push?: number
}

export type BattleScenarioRequest = {
  battle_id: string
  participants: BattleParticipantRequest[]
  turn_order: string[]
  seed: number
  rule_config?: BattleRuleConfig
}
