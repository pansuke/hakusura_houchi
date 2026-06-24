import { resultLabel, uiLabels } from './ja'
import type {
  BattleEvent,
  BattleReplay,
  BattleSnapshot,
  DisplayCatalog,
  ParticipantSnapshot,
} from '../types/battleReplay'

export type PrimaryTarget =
  | {
      kind: 'participant'
      participantId: string
      effectKind: 'attack' | 'heal' | 'other'
    }
  | {
      kind: 'nexus'
      side: 'ally' | 'enemy'
      effectKind: 'attack'
    }
  | null

export type ActionPhaseId =
  | 'standby'
  | 'movement'
  | 'draw'
  | 'card_action'
  | 'effect_result'
  | 'action_end'
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
  standby: '① 復活・行動準備',
  movement: '② 移動・対面・PUSH',
  draw: '③ ドロー',
  card_action: '④ カードアクション',
  effect_result: '⑤ 効果解決',
  action_end: '⑥ 行動終了',
}

export function sideName(side: string): string {
  return side === 'ally' ? uiLabels.ally : uiLabels.enemy
}

export function participantName(catalog: DisplayCatalog, participantId: string | null): string {
  if (!participantId) {
    return '-'
  }
  return catalog.participants[participantId]?.name ?? '名称未設定'
}

export function cardName(catalog: DisplayCatalog, cardId: unknown): string {
  return typeof cardId === 'string' ? catalog.cards[cardId]?.name ?? '名称未設定' : '-'
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
  if (snapshot.action_index === 0) {
    return []
  }
  return [
    buildStandbyPhase(events),
    buildMovementPhase(events),
    buildDrawPhase(events, catalog),
    buildCardActionPhase(snapshot, events, catalog),
    buildEffectResultPhase(snapshot, events, catalog),
    buildActionEndPhase(snapshot, events, catalog),
  ]
}

function buildStandbyPhase(events: BattleEvent[]): ActionPhaseView {
  const items: ActionPhaseItem[] = []
  const respawnWaited = events.find((event) => event.event_type === 'respawn_waited')
  const respawned = events.find((event) => event.event_type === 'character_respawned')
  const deckShuffled = events.find((event) => event.event_type === 'deck_shuffled')
  const health = events.find(
    (event) => event.event_type === 'health_recovered' && event.payload.reason === 'action_right',
  )
  const mana = events.find((event) => event.event_type === 'mana_recovered')
  const drawGauge = events.find((event) => event.event_type === 'gauge_changed')

  if (respawnWaited) {
    items.push({
      label: `復活まで残り：${numberPayload(respawnWaited, 'after')}回`,
      importance: 'primary',
    })
    items.push({
      label: 'このActionでは移動・カード使用を行いません',
      importance: 'secondary',
    })
    return phase('standby', 'warning', items)
  }

  if (respawned) {
    items.push({
      label: `復活：HP ${numberPayload(respawned, 'hp')} / MP ${numberPayload(respawned, 'mp')}`,
      importance: 'primary',
    })
  }
  if (deckShuffled) {
    items.push({ label: 'Deckを再シャッフル', importance: 'secondary' })
  }

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
    if (triggerCount > 0) {
      items.push({
        label: `ドロー権を${triggerCount}回獲得`,
        importance: 'primary',
      })
    }
  }

  return phase('standby', 'completed', items)
}

function buildMovementPhase(events: BattleEvent[]): ActionPhaseView {
  const items: ActionPhaseItem[] = []
  for (const event of events) {
    if (event.event_type === 'lane_moved') {
      const mode = event.payload.mode === 'push' ? 'PUSH' : '前進'
      const lane = event.lane_id ? event.lane_id.toUpperCase() : '-'
      items.push({
        label: `${lane}レーン ${mode}：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`,
        detail:
          event.payload.advance !== undefined
            ? `差分 +${numberPayload(event, 'advance')}`
            : undefined,
        importance: 'primary',
      })
    }
    if (event.event_type === 'engagement_started') {
      items.push({
        label: `対面開始：位置 ${numberPayload(event, 'position')}`,
        importance: 'primary',
      })
    }
    if (event.event_type === 'engagement_ended') {
      items.push({ label: '対面解除', importance: 'secondary' })
    }
    if (event.event_type === 'target_selection_failed') {
      items.push({
        label: `対象なし：${String(event.payload.reason ?? '-')}`,
        importance: 'secondary',
      })
    }
  }
  if (!items.length) {
    items.push({ label: '移動・対面変化なし', importance: 'secondary' })
    return phase('movement', 'skipped', items)
  }
  return phase('movement', 'completed', items)
}

function buildDrawPhase(events: BattleEvent[], catalog: DisplayCatalog): ActionPhaseView {
  const drawGauge = events.find((event) => event.event_type === 'gauge_changed')
  const triggerCount = drawGauge ? numberPayload(drawGauge, 'trigger_count') : 0
  const drawnCards = events.filter(
    (event) =>
      event.event_type === 'card_drawn' &&
      (event.payload.draw_source ?? event.payload.reason) === 'draw_gauge',
  )
  const blockedDraws = events.filter(
    (event) =>
      event.event_type === 'card_draw_blocked' && event.payload.draw_source === 'draw_gauge',
  )
  const recycled = events.filter((event) => event.event_type === 'discard_recycled')
  const overflow = events.filter((event) => event.event_type === 'card_overflow_discarded')
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
  for (const event of recycled) {
    items.push({
      label: '捨て札をシャッフルして山札を再構築',
      detail: `shuffle_count: ${numberPayload(event, 'shuffle_count')}`,
      importance: 'secondary',
    })
  }
  for (const event of overflow) {
    items.push({
      label: `手札上限${numberPayload(event, 'hand_limit')}枚：最古の「${cardName(
        catalog,
        event.payload.card_id,
      )}」を捨てた`,
      importance: 'primary',
    })
  }
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
    items.push(...blockedDrawItems(event))
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
  const usedCards = events.filter((event) => event.event_type === 'card_used')
  const manaSpentEvents = events.filter((event) => event.event_type === 'mana_spent')
  const grants = events.filter((event) => event.event_type === 'grant_card_play')
  const items: ActionPhaseItem[] = []

  if (!actor) {
    items.push({ label: 'カード判定前です', importance: 'secondary' })
    return phase('card_action', 'skipped', items)
  }

  if (actor.hand.length === 0 && attempts.length === 0 && heldCards.length === 0 && !usedCards.length) {
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

  if (!usedCards.length) {
    items.push({ label: '使用できるカードがありませんでした', importance: 'primary' })
    return phase('card_action', heldCards.length > 0 ? 'warning' : 'skipped', items)
  }

  for (const [index, usedCard] of usedCards.entries()) {
    const cardPlayIndex = numberPayload(usedCard, 'card_play_index', index + 1)
    const manaSpent =
      manaSpentEvents.find(
        (event) => numberPayload(event, 'card_play_index', -1) === cardPlayIndex,
      ) ?? manaSpentEvents[index]
    items.push({
      label: `${cardPlayIndex}枚目：「${cardName(catalog, usedCard.payload.card_id)}」を選択`,
      importance: 'primary',
    })
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
    for (const grant of grants.filter(
      (event) => numberPayload(event, 'card_play_index', -1) === cardPlayIndex,
    )) {
      items.push({
        label: `追加カード使用権：+${numberPayload(grant, 'amount')}`,
        detail: `残り使用権：${numberPayload(grant, 'remaining_card_plays')}`,
        importance: 'primary',
      })
    }
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
    [
      'damage_applied',
      'health_recovered',
      'mana_gained',
      'card_drawn',
      'card_draw_blocked',
      'character_defeated',
      'nexus_damaged',
      'nexus_destroyed',
      'grant_card_play',
    ].includes(event.event_type),
  )

  for (const event of effectEvents) {
    if (event.event_type === 'health_recovered' && event.payload.reason !== 'card_effect') {
      continue
    }
    if (
      event.event_type === 'card_drawn' &&
      (event.payload.draw_source ?? event.payload.reason) !== 'card_effect'
    ) {
      continue
    }
    if (event.event_type === 'card_draw_blocked' && event.payload.draw_source !== 'card_effect') {
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
    if (event.event_type === 'nexus_damaged') {
      const target = targetLabel(snapshot, event.target_id, catalog)
      items.push({
        label: `${target}に${numberPayload(event, 'applied')}ダメージ`,
        importance: 'primary',
      })
      items.push({
        label: `Nexus HP：${numberPayload(event, 'before')} → ${numberPayload(event, 'after')}`,
        importance: 'secondary',
      })
    }
    if (event.event_type === 'nexus_destroyed') {
      items.push({
        label: `${targetLabel(snapshot, event.target_id, catalog)}を破壊しました`,
        importance: 'primary',
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
    if (event.event_type === 'card_draw_blocked') {
      items.push({ label: 'カードを1枚引く効果を処理', importance: 'secondary' })
      items.push(...blockedDrawItems(event))
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
  if (participantId === 'enemy_nexus') {
    return '敵Nexus'
  }
  if (participantId === 'ally_nexus') {
    return '味方Nexus'
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
  if (reason === 'simulation_safety_limit') {
    return '最大行動回数に到達しました'
  }
  return '戦闘が終了しました'
}

export function primaryTarget(events: BattleEvent[]): PrimaryTarget {
  const defeated = events.find((event) => event.event_type === 'character_defeated')
  if (defeated?.actor_id) {
    return { kind: 'participant', participantId: defeated.actor_id, effectKind: 'attack' }
  }
  const damaged = events.find((event) => event.event_type === 'damage_applied')
  if (damaged?.target_id) {
    return { kind: 'participant', participantId: damaged.target_id, effectKind: 'attack' }
  }
  const nexusDamaged = events.find((event) => event.event_type === 'nexus_damaged')
  if (nexusDamaged?.target_id === 'enemy_nexus' || nexusDamaged?.target_id === 'ally_nexus') {
    return {
      kind: 'nexus',
      side: nexusDamaged.target_id === 'enemy_nexus' ? 'enemy' : 'ally',
      effectKind: 'attack',
    }
  }
  const healed = events.find(
    (event) => event.event_type === 'health_recovered' && event.payload.reason === 'card_effect',
  )
  if (healed?.target_id) {
    return { kind: 'participant', participantId: healed.target_id, effectKind: 'heal' }
  }
  const manaGained = events.find((event) => event.event_type === 'mana_gained')
  if (manaGained?.actor_id) {
    return { kind: 'participant', participantId: manaGained.actor_id, effectKind: 'heal' }
  }
  const cardUsed = events.find((event) => event.event_type === 'card_used')
  if (cardUsed?.target_id && !cardUsed.target_id.endsWith('_nexus')) {
    return { kind: 'participant', participantId: cardUsed.target_id, effectKind: 'other' }
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

export function numberPayload(event: BattleEvent, key: string, fallback?: number): number {
  const value = event.payload[key]
  if (typeof value !== 'number') {
    if (fallback !== undefined) {
      return fallback
    }
    throw new Error(`Invalid event payload: ${event.event_type}.${key}`)
  }
  return value
}

function blockedDrawItems(event: BattleEvent): ActionPhaseItem[] {
  const reason =
    event.payload.blocked_reason === 'hand_full'
      ? '手札上限のためカードを引けませんでした'
      : '引けるカードがありませんでした'
  const items: ActionPhaseItem[] = [{ label: reason, importance: 'secondary' }]
  if (event.payload.blocked_reason === 'hand_full') {
    items.push({
      label: `手札：${numberPayload(event, 'hand_size')} / ${numberPayload(event, 'hand_limit')}`,
      importance: 'secondary',
    })
  } else {
    items.push({
      label: `手札：${numberPayload(event, 'hand_size')}枚`,
      importance: 'secondary',
    })
  }
  return items
}
