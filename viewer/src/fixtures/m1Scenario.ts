import type { BattleScenarioRequest } from '../types/battleReplay'

export const m1Scenario: BattleScenarioRequest = {
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
