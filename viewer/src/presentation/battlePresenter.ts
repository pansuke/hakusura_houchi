import { resultLabel, uiLabels } from './ja'
import type {
  BattleEvent,
  BattleReplay,
  BattleSnapshot,
  DisplayCatalog,
  ParticipantSnapshot,
} from '../types/battleReplay'

export type PrimaryTarget = {
  participantId: string
  kind: 'attack' | 'heal' | 'other'
} | null

export type ActionPhaseId = 'standby' | 'draw' | 'card_action' | 'effect_result' | 'action_end'
export type ActionPhaseStatus = 'completed' | 'skipped' | 'warning' | 'failed'
export type ActionPhaseItem = {
  label: string
  detail?: string
  importance: 'primary' | 'secondary' | 'debug'
}
export type ActionPhaseView = {
  id: ActionPhaseId
  title: string
  status: ActionPhaseStatus
  items: ActionPhaseItem[]
}

const phaseTitles: Record<ActionPhaseId, string> = {
  standby: '① 行動準備',
  draw: '② ドロー',
  card_action: '③ カードアクション',
  effect_result: '④ 効果解決',
  action_end: '⑤ 行動終了',
}

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

export function buildActionPhases(
  snapshot: BattleSnapshot,
  events: BattleEvent[],
  catalog: DisplayCatalog,
): ActionPhaseView[] {
  return [
    buildStandbyPhase(events),
    buildDrawPhase(events, catalog),
    buildCardActionPhase(snapshot, events, catalog),
    buildEffectResultPhase(snapshot, events, catalog),
    buildActionEndPhase(snapshot, events, catalog),
  ]
}

function buildStandbyPhase(events: BattleEvent[]): ActionPhaseView {
  const items: ActionPhaseItem[] = []
  const health = events.find(
    (event) => event.event_type === 'health_recovered' && event.payload.reason === 'action_right',
  )
  const mana = events.find((event) => event.event_type === 'mana_recovered')
  const drawGauge = events.find((event) => event.event_type === 'gauge_changed')

  if (health) {
    items.push({ label: recoveryLine('HP回復', 'HPR', health), importance: 'secondary' })
  } else {
    items.push({ label: 'HP回復：なし', importance: 'secondary' })
  }

  if (mana) {
    items.push({ label: recoveryLine('MP回復', 'MPR', mana), importance: 'secondary' })
  } else {
    items.push({ label: 'MP回復：なし', importance: 'secondary' })
  }

  if (drawGauge) {
    const triggerCount = numberPayload(drawGauge, 'trigger_count')
    items.push({
      label: `ドロー進捗：${numberPayload(drawGauge, 'before')} + ${numberPayload(
        drawGauge,
        'gain',
      )} → ${numberPayload(drawGauge, 'after')}`,
      importance: triggerCount > 0 ? 'primary' : 'secondary',
    })
    items.push({
      label: triggerCount > 0 ? `ドロー権を${triggerCount}回獲得` : 'ドロー権は発生しませんでした',
      importance: triggerCount > 0 ? 'primary' : 'secondary',
    })
  }

  return phase('standby', 'completed', items)
}

function buildDrawPhase(events: BattleEvent[], catalog: DisplayCatalog): ActionPhaseView {
  const drawGauge = events.find((event) => event.event_type === 'gauge_changed')
  const triggerCount = drawGauge ? numberPayload(drawGauge, 'trigger_count') : 0
  const drawnCards = events.filter(
    (event) => event.event_type === 'card_drawn' && event.payload.reason === 'draw_gauge',
  )
  const blockedDraws = events.filter((event) => event.event_type === 'card_draw_blocked')
  const items: ActionPhaseItem[] = []

  if (triggerCount === 0) {
    items.push({ label: 'ドロー権は発生しませんでした', importance: 'secondary' })
    if (drawGauge) {
      items.push({
        label: `現在の進捗：${numberPayload(drawGauge, 'after')} / 100`,
        importance: 'secondary',
      })
    }
    return phase('draw', 'skipped', items)
  }

  items.push({ label: `ドロー権を${triggerCount}回使用`, importance: 'primary' })
  for (const [index, event] of drawnCards.entries()) {
    const prefix = drawnCards.length > 1 ? `${index + 1}枚目：` : ''
    items.push({
      label: `${prefix}「${cardName(catalog, event.payload.card_id)}」を引いた`,
      importance: 'primary',
    })
    items.push({
      label: `手札：${numberPayload(event, 'hand_size_before')}枚 → ${numberPayload(
        event,
        'hand_size_after',
      )}枚`,
      importance: 'secondary',
    })
  }
  for (const event of blockedDraws) {
    const reason = event.payload.reason === 'hand_full' ? '手札上限のためカードを引けませんでした' : '引けるカードがありませんでした'
    items.push({ label: reason, importance: 'secondary' })
  }

  return phase('draw', blockedDraws.length > 0 ? 'warning' : 'completed', items)
}

function buildCardActionPhase(
  snapshot: BattleSnapshot,
  events: BattleEvent[],
  catalog: DisplayCatalog,
): ActionPhaseView {
  const actor = snapshot.acted_actor_id ? snapshot.participants[snapshot.acted_actor_id] : null
  const attempts = events.filter((event) => event.event_type === 'card_attempted')
  const heldCards = events.filter((event) => event.event_type === 'card_held')
  const usedCard = events.find((event) => event.event_type === 'card_used')
  const manaSpent = events.find((event) => event.event_type === 'mana_spent')
  const items: ActionPhaseItem[] = []

  if (!actor) {
    items.push({ label: 'カード判定前です', importance: 'secondary' })
    return phase('card_action', 'skipped', items)
  }

  if (actor.hand.length === 0 && attempts.length === 0 && heldCards.length === 0 && !usedCard) {
    items.push({ label: '手札にカードがありませんでした', importance: 'secondary' })
    return phase('card_action', 'skipped', items)
  }

  for (const held of heldCards) {
    items.push({
      label: `${cardName(catalog, held.payload.card_id)}：${heldReasonText(held.payload.reason)}`,
      detail:
        held.payload.reason === 'insufficient_mana'
          ? `必要MP：${numberPayload(held, 'required_mp')} / 現在MP：${numberPayload(
              held,
              'current_mp',
            )}`
          : undefined,
      importance: 'secondary',
    })
  }

  if (!usedCard) {
    items.push({ label: '使用できるカードがありませんでした', importance: 'primary' })
    return phase('card_action', heldCards.length > 0 ? 'warning' : 'skipped', items)
  }

  items.push({ label: `「${cardName(catalog, usedCard.payload.card_id)}」を選択`, importance: 'primary' })
  items.push({ label: `対象：${targetLabel(snapshot, usedCard.target_id, catalog)}`, importance: 'secondary' })
  if (manaSpent) {
    items.push({ label: `消費MP：${numberPayload(manaSpent, 'amount')}`, importance: 'secondary' })
    items.push({
      label: `MP：${numberPayload(manaSpent, 'before')} → ${numberPayload(manaSpent, 'after')}`,
      importance: 'secondary',
    })
  } else {
    items.push({ label: '消費MP：0', importance: 'secondary' })
  }
  return phase('card_action', heldCards.length > 0 ? 'warning' : 'completed', items)
}

function buildEffectResultPhase(
  snapshot: BattleSnapshot,
  events: BattleEvent[],
  catalog: DisplayCatalog,
): ActionPhaseView {
  const items: ActionPhaseItem[] = []
  const effectEvents = events.filter((event) =>
    ['damage_applied', 'health_recovered', 'mana_gained', 'card_drawn', 'character_defeated'].includes(
      event.event_type,
    ),
  )

  for (const event of effectEvents) {
    if (event.event_type === 'health_recovered' && event.payload.reason !== 'card_effect') {
      continue
    }
    if (event.event_type === 'card_drawn' && event.payload.reason !== 'card_effect') {
      continue
    }
    if (event.event_type === 'damage_applied') {
      const target = targetLabel(snapshot, event.target_id, catalog)
      const requested = numberPayload(event, 'requested')
      const applied = numberPayload(event, 'applied')
      items.push({
        label:
          requested === applied
            ? `${target}に${applied}ダメージ`
            : `${target}に${requested}ダメージを試行 / 実ダメージ：${applied}`,
        importance: 'primary',
      })
      items.push({
        label: `HP：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`,
        importance: 'secondary',
      })
    }
    if (event.event_type === 'health_recovered') {
      items.push({
        label: `${targetLabel(snapshot, event.target_id, catalog)}のHPを${numberPayload(
          event,
          'requested',
        )}回復 / 実回復：${numberPayload(event, 'applied')}`,
        importance: 'primary',
      })
      items.push({
        label: `HP：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`,
        importance: 'secondary',
      })
    }
    if (event.event_type === 'mana_gained') {
      items.push({
        label: `${participantName(catalog, event.actor_id)}のMPを${numberPayload(event, 'applied')}回復`,
        importance: 'primary',
      })
      items.push({
        label: `MP：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`,
        importance: 'secondary',
      })
    }
    if (event.event_type === 'card_drawn') {
      items.push({
        label: `カード効果で「${cardName(catalog, event.payload.card_id)}」を引いた`,
        importance: 'primary',
      })
    }
    if (event.event_type === 'character_defeated') {
      items.push({
        label: `${participantName(catalog, event.actor_id)}は戦闘不能になりました`,
        importance: 'primary',
      })
    }
  }

  if (!items.length) {
    items.push({ label: '効果は発生しませんでした', importance: 'secondary' })
    return phase('effect_result', 'skipped', items)
  }
  return phase('effect_result', 'completed', items)
}

function buildActionEndPhase(
  snapshot: BattleSnapshot,
  events: BattleEvent[],
  catalog: DisplayCatalog,
): ActionPhaseView {
  const battleCompleted = events.find((event) => event.event_type === 'battle_completed')
  if (battleCompleted) {
    return phase('action_end', 'completed', [
      { label: endReasonText(battleCompleted.payload.end_reason), importance: 'primary' },
      { label: `結果：${resultLabelText(battleCompleted.payload.result)}`, importance: 'primary' },
    ])
  }
  return phase('action_end', 'completed', [
    { label: '戦闘継続', importance: 'secondary' },
    {
      label: `次の行動：${participantName(catalog, snapshot.next_actor_id)}`,
      importance: 'primary',
    },
  ])
}

function phase(
  id: ActionPhaseId,
  status: ActionPhaseStatus,
  items: ActionPhaseItem[],
): ActionPhaseView {
  return { id, title: phaseTitles[id], status, items }
}

function recoveryLine(label: string, statName: string, event: BattleEvent): string {
  const requested = numberPayload(event, 'requested')
  const applied = numberPayload(event, 'applied')
  if (requested === 0) {
    return `${label}：なし`
  }
  if (applied === 0) {
    return `${label}：なし（${statName === 'HPR' ? 'HP' : 'MP'}最大）`
  }
  const base = `${label}：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}（${statName} +${requested}`
  return requested === applied ? `${base}）` : `${base}、実回復${applied}）`
}

function targetLabel(
  snapshot: BattleSnapshot,
  participantId: string | null,
  catalog: DisplayCatalog,
): string {
  if (!participantId) {
    return '-'
  }
  const participant = snapshot.participants[participantId]
  return participant ? `${sideName(participant.side)}・${participantName(catalog, participantId)}` : participantName(catalog, participantId)
}

function heldReasonText(reason: unknown): string {
  if (reason === 'insufficient_mana') {
    return '使用不可：MP不足'
  }
  if (reason === 'no_valid_target') {
    return '使用不可：有効な対象なし'
  }
  return '使用不可'
}

function resultLabelText(result: unknown): string {
  if (result === 'ally_win') {
    return '味方チームの勝利'
  }
  if (result === 'ally_loss') {
    return '敵チームの勝利'
  }
  if (result === 'draw') {
    return '引き分け'
  }
  return String(result ?? '-')
}

function endReasonText(reason: unknown): string {
  if (reason === 'enemy_defeated') {
    return '敵チームが全滅しました'
  }
  if (reason === 'ally_defeated') {
    return '味方チームが全滅しました'
  }
  if (reason === 'max_actions') {
    return '最大行動回数に到達しました'
  }
  return '戦闘が終了しました'
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
