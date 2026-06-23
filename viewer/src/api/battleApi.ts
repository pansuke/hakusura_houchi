import type { BattleReplay, BattleScenarioRequest } from '../types/battleReplay'

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
