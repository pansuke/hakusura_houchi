import { resultLabel, uiLabels } from './ja'
import type { BattleEvent, BattleReplay, BattleSnapshot, DisplayCatalog, ParticipantSnapshot } from '../types/battleReplay'

export type PrimaryTarget = {
  participantId: string
  kind: 'attack' | 'heal' | 'other'
} | null

export function sideName(side: string): string {
  return side === 'ally' ? uiLabels.ally : uiLabels.enemy
}

export function participantName(catalog: DisplayCatalog, participantId: string | null): string {
  if (!participantId) {
    return '-'
  }
  return catalog.participants[participantId]?.name ?? participantId
}

export function cardName(catalog: DisplayCatalog, cardId: unknown): string {
  return typeof cardId === 'string' ? catalog.cards[cardId]?.name ?? cardId : '-'
}

export function cardDescription(catalog: DisplayCatalog, cardId: string): string {
  return catalog.cards[cardId]?.description ?? ''
}

export function cardMpCost(catalog: DisplayCatalog, cardId: string): number {
  return catalog.cards[cardId]?.mp_cost ?? 0
}

export function visibleResultLabel(replay: BattleReplay | null, isAtLast: boolean): string {
  if (!replay) {
    return uiLabels.loading
  }
  if (!isAtLast) {
    return uiLabels.running
  }
  return resultLabel(replay.summary.result, replay.summary.end_reason)
}

export function actorTitle(snapshot: BattleSnapshot, catalog: DisplayCatalog): string {
  const actor = snapshot.acted_actor_id
  if (!actor) {
    return '戦闘開始前'
  }
  const participant = snapshot.participants[actor]
  return `${sideName(participant.side)}・${participantName(catalog, actor)}の行動`
}

export function actionSummaryLines(
  snapshot: BattleSnapshot,
  events: BattleEvent[],
  catalog: DisplayCatalog,
): string[] {
  if (snapshot.action_index === 0) {
    return ['最初の行動前の状態です。']
  }

  const lines: string[] = []
  const usedCard = events.find((event) => event.event_type === 'card_used')
  if (usedCard) {
    lines.push(`「${cardName(catalog, usedCard.payload.card_id)}」を使用`)
  }

  for (const event of events) {
    if (event.event_type === 'mana_spent') {
      lines.push(`MP ${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`)
    }
    if (event.event_type === 'damage_applied') {
      const target = snapshot.participants[event.target_id ?? '']
      lines.push(
        `${sideName(target.side)}・${participantName(catalog, event.target_id)}に${numberPayload(
          event,
          'applied',
        )}ダメージ`,
      )
      lines.push(`HP ${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`)
    }
    if (event.event_type === 'health_recovered' && event.payload.reason === 'card_effect') {
      lines.push(
        `${participantName(catalog, event.target_id)}のHP ${numberPayload(event, 'before')} → ${numberPayload(
          event,
          'after',
        )}`,
      )
    }
    if (event.event_type === 'mana_gained') {
      lines.push(
        `${participantName(catalog, event.actor_id)}のMP ${numberPayload(event, 'before')} → ${numberPayload(
          event,
          'after',
        )}`,
      )
    }
  }

  if (!usedCard) {
    const heldReason = events.find((event) => event.event_type === 'card_held')?.payload.reason
    lines.push('使用できるカードがありませんでした。')
    if (heldReason === 'insufficient_mana') {
      lines.push('理由：MP不足')
    }
    if (heldReason === 'no_valid_target') {
      lines.push('理由：有効な対象なし')
    }
  }

  lines.push(`次の行動：${participantName(catalog, snapshot.next_actor_id)}`)
  return lines
}

export function primaryTarget(events: BattleEvent[]): PrimaryTarget {
  const defeated = events.find((event) => event.event_type === 'character_defeated')
  if (defeated?.actor_id) {
    return { participantId: defeated.actor_id, kind: 'attack' }
  }
  const damaged = events.find((event) => event.event_type === 'damage_applied')
  if (damaged?.target_id) {
    return { participantId: damaged.target_id, kind: 'attack' }
  }
  const healed = events.find(
    (event) => event.event_type === 'health_recovered' && event.payload.reason === 'card_effect',
  )
  if (healed?.target_id) {
    return { participantId: healed.target_id, kind: 'heal' }
  }
  const manaGained = events.find((event) => event.event_type === 'mana_gained')
  if (manaGained?.actor_id) {
    return { participantId: manaGained.actor_id, kind: 'heal' }
  }
  const cardUsed = events.find((event) => event.event_type === 'card_used')
  if (cardUsed?.target_id) {
    return { participantId: cardUsed.target_id, kind: 'other' }
  }
  return null
}

export function recoveryText(value: number): string {
  return value === 0 ? uiLabels.none : `+${value}`
}

export function participantTitle(participant: ParticipantSnapshot, catalog: DisplayCatalog): string {
  return `${sideName(participant.side)}・${participantName(catalog, participant.participant_id)}`
}

export function drawDebugLines(events: BattleEvent[], catalog: DisplayCatalog): string[] {
  return events
    .filter((event) => event.event_type === 'gauge_changed')
    .map(
      (event) =>
        `${participantName(catalog, event.actor_id)}: ドロー進捗 ${numberPayload(
          event,
          'before',
        )} + ${numberPayload(event, 'gain')} → ${numberPayload(event, 'after')} / ${numberPayload(
          event,
          'trigger_count',
        )}回発火`,
    )
}

export function cardAttemptDebugLines(events: BattleEvent[], catalog: DisplayCatalog): string[] {
  return events
    .filter((event) => event.event_type === 'card_attempted' || event.event_type === 'card_held')
    .map((event) => {
      const card = cardName(catalog, event.payload.card_id)
      if (event.event_type === 'card_attempted') {
        return `${card}: 使用確認`
      }
      const reason = event.payload.reason === 'insufficient_mana' ? 'MP不足のため保留' : '有効な対象なし'
      return `${card}: ${reason}`
    })
}

export function numberPayload(event: BattleEvent, key: string): number {
  const value = event.payload[key]
  return typeof value === 'number' ? value : 0
}
