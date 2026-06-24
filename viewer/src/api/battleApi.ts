import type { BattleReplay, BattleRuleConfig, BattleScenarioRequest } from '../types/battleReplay'

export async function simulateBattle(
  apiBaseUrl: string,
  scenario: BattleScenarioRequest,
): Promise<BattleReplay> {
  const response = await fetch(`${apiBaseUrl}/api/v1/battles/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(scenario),
  })
  if (!response.ok) {
    throw new Error('failed to load replay')
  }
  return (await response.json()) as BattleReplay
}

export async function fetchBattleRuleConfig(apiBaseUrl: string): Promise<BattleRuleConfig> {
  const response = await fetch(`${apiBaseUrl}/api/v1/dev/battle-rule-config`)
  if (!response.ok) {
    throw new Error('failed to load rule config')
  }
  return (await response.json()) as BattleRuleConfig
}

export async function saveBattleRuleConfig(
  apiBaseUrl: string,
  config: BattleRuleConfig,
): Promise<BattleRuleConfig> {
  const response = await fetch(`${apiBaseUrl}/api/v1/dev/battle-rule-config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!response.ok) {
    throw new Error('failed to save rule config')
  }
  return (await response.json()) as BattleRuleConfig
}
