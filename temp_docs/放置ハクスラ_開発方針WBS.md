# 放置系 × ハクスラ × デッキ構築 RPG
# 開発方針・WBS v1.3

更新日: 2026-06-24
対象: プロトタイプ開始からSteam向け製品化判断まで

---

# 0. 文書の目的

本書は以下を管理する。

- 開発順序
- マイルストーン
- Definition of Ready
- Definition of Done
- 大項目・中項目・小項目
- 暫定制約の解除時期
- Product Owner Decision Gate

仕様の中身はゲーム仕様書および総合設計書を正とする。

---

# 1. 開発原則

1. Readyでないマイルストーンへ実装着手しない
2. 未確定事項を実装者判断で確定しない
3. M1暫定仕様には解除先を必ず割り当てる
4. BattleEngineとViewerを分離する
5. Masterデータ基盤をBattleEngineより先に完成させる
6. 同一入力から同一出力を生成する
7. 構造化Eventを正とする
8. バランス値をコードへ埋め込まない
9. M1とM2を混在させない
10. Product Owner Decision Gateを通過してから大きなUX仕様を固定する

---

# 2. マイルストーン

## M0-A: 開発環境基盤

Status: Done候補

対象:

- Docker
- FastAPI
- Vue / Vite
- health
- lint
- test
- Makefile
- 基本ディレクトリ

---

## M0-B: Masterデータ基盤

Status: Ready

対象:

- CharacterMaster
- TraitMaster
- CardMaster
- Effect
- RollRule
- JSON Schema
- build_data.py
- data-validate
- data-build
- 再現可能生成
- CI差分検出

対象外:

- BattleEngine
- Viewer機能
- DB
- API追加
- Instance
- 正式Deck保存

---

## M1: 1対1BattleEngine

Status: Done

対象:

- 味方1体・敵1体
- BattleScenario
- 固定turn_order
- Deck Runtime
- DS / MPR / HPR
- 4種類のEffect
- 死亡
- 勝敗
- 最大Action
- Event
- Snapshot
- Summary
- 再現性

対象外:

- Viewer
- 3レーン
- 復活
- 本番Damage式
- Trait実行
- Instance

---

## M2: Replay API・開発Viewer

Status: Done

対象:

- POST `/api/v1/battles/simulate`
- Replayレスポンス
- Action cursor
- Snapshot表示
- Event表示
- 次・前・複数Action
- 自動再生
- 表示速度
- 多重操作防止

---

## M3-A: 3レーン・本番戦闘基盤

Status: Done

通過済みDecision Gate:

- DG-001 本番Action Scheduler
- DG-002 本番Deck循環
- DG-003 復活テンポ
- DG-005 位置・PUSH・対象Scope

対象:

- TOP / MID / BOT
- Battle全体Action Index
- 固定レーン巡回Scheduler
- BattleRuleConfigと開発Viewer設定画面
- Seed付きDeck shuffle / recycle
- 初期手札3 / 最大手札7
- 最古カード優先・手札上限時最古破棄
- Effect `grant_card_play`
- CharacterMaster Schema v2
- AD / AP / AR / MR / PUSH
- 本番Damage式
- 個別位置・移動・対面
- 復活・レーン復帰
- Local / Adjacent / Global
- 3レーンEvent / Snapshot / Viewer

## M3-B: Nexus・本番勝敗

Status: Done

対象:

- NexusState
- Nexus HP 8000暫定値
- Local通常カードによるNexus攻撃
- Nexus破壊勝敗
- 本番最大Action撤廃
- Simulation Safety Error
- Nexus Event / Snapshot / Viewer

## M4-A: SUPPORT


対象:

- SUPPORT配置
- HPなし
- 攻撃・回復補正
- Trait維持
- 支援要請
- 支援量
- 支援対象

---

## M4-B: 高度戦闘ルール

Status: Decision Gate待ち

開始前必須:

- DG-004 反撃・追撃・割り込み

対象:

- CRT
- EVA
- Status Resistance
- 状態異常
- 反撃
- 追撃
- 割り込み
- Trait runtime

---

## M5: ハクスラ・Instance

- CharacterInstance
- CardInstance
- ItemInstance
- RollRule実行
- ドロップ
- レアリティ
- ロール保存

---

## M6: 構築・選出

- Deck保存
- EquipmentSet
- Build
- Party
- Formation
- DeckRule
- Legendary制限
- 6体登録
- 4体選出

---

## M7: PvE探索

- AreaMaster
- StageMaster
- StageBonus
- 探索深度
- 報酬
- ロスト
- 高速実行

---

## M8: PvP

- 相手Party公開
- StageBonus公開
- 4体選出
- 非公開情報
- 対戦
- レート
- チート対策

---

## M9: 製品化

- 製品UI
- セーブ
- Steam
- Cloud
- 実績
- 配布

---

# 3. M0-B WBS

## C-1. Schema実装

### C-1-1. CharacterMaster Schema
### C-1-2. TraitMaster Schema
### C-1-3. CardMaster Schema
### C-1-4. Effect Schema
### C-1-5. RollRule Schema
### C-1-6. game-data Schema

完了条件:

- Draft 2020-12
- additionalProperties false
- Schema自己検証成功

## C-2. JSON Loader

### C-2-1. UTF-8読込
### C-2-2. BOM拒否
### C-2-3. 重複キー拒否
### C-2-4. JSON構文エラー収集

## C-3. ID検証

### C-3-1. 種別prefix
### C-3-2. ファイル名一致
### C-3-3. 全Master横断一意
### C-3-4. ID変更方針文書化

## C-4. 複合制約

### C-4-1. initial_mp <= max_mp
### C-4-2. RollRule min <= max
### C-4-3. weighted_table value重複禁止
### C-4-4. target_path存在確認
### C-4-5. Character trait参照

## C-5. data-validate

### C-5-1. 生成物非更新
### C-5-2. 全エラー収集
### C-5-3. エラー順固定
### C-5-4. exit code

## C-6. data-build

### C-6-1. validate再利用
### C-6-2. Master id順
### C-6-3. JSON正規化
### C-6-4. 一時ファイル
### C-6-5. atomic replace
### C-6-6. 失敗時既存維持

## C-7. Makefile / CI

### C-7-1. make data-validate
### C-7-2. make data-build
### C-7-3. CI再生成
### C-7-4. Git差分検出

## C-8. テスト

正常系:

- 各Master正常
- 参照正常
- 統合正常
- 同一入力同一出力

異常系:

- 重複キー
- Schema違反
- ファイル名不一致
- 全体ID重複
- 参照切れ
- target_path不正
- 複合数値制約
- 既存生成物保護

---

# 4. M0-B Definition of Ready

- [x] CharacterMaster項目・制約
- [x] TraitMaster項目・制約
- [x] CardMaster項目・制約
- [x] Effect形式
- [x] RollRule形式
- [x] Master参照一覧
- [x] ID一意範囲
- [x] JSON Schema Draft
- [x] validator
- [x] 重複キー仕様
- [x] シリアライズ
- [x] schema_version
- [x] data-validate責務
- [x] data-build責務
- [x] CI方針

判定:

```text
Ready
```

---

# 5. M0-B Definition of Done

- [ ] 全Schemaが存在する
- [ ] 正常データをvalidateできる
- [ ] 正常データをbuildできる
- [ ] game-data.jsonが仕様通り
- [ ] 同一入力でバイト一致
- [ ] 重複キーを拒否
- [ ] 全Master横断ID重複を拒否
- [ ] 参照切れを拒否
- [ ] target_path不正を拒否
- [ ] エラー順が決定的
- [ ] validateが生成物を変更しない
- [ ] build失敗時に既存生成物を維持
- [ ] CIで生成差分を検出
- [ ] make lint成功
- [ ] make test成功
- [ ] API追加なし
- [ ] BattleEngine実装なし
- [ ] Viewer追加なし

---

# 6. M1 WBS

## D-1. BattleScenario

### D-1-1. participant_id
### D-1-2. side
### D-1-3. character_master_id
### D-1-4. deck
### D-1-5. initial_state
### D-1-6. turn_order
### D-1-7. simulation_safety_limit
### D-1-8. seed

## D-2. BattleState

### D-2-1. battle_status
### D-2-2. battle_result
### D-2-3. action_index
### D-2-4. turn_order
### D-2-5. current_turn_index
### D-2-6. participant states

## D-3. Deck Runtime

### D-3-1. ordered draw_pile
### D-3-2. initial hand 3
### D-3-3. hand limit 5
### D-3-4. playable card scan
### D-3-5. card_held
### D-3-6. discard
### D-3-7. deterministic recycle

## D-4. Action Right Resources

### D-4-1. HPR applies only to current actor
### D-4-2. MPR applies only to current actor
### D-4-3. DS advances only current actor Draw Gauge
### D-4-4. draw threshold 100
### D-4-5. multiple draw triggers
### D-4-6. HP / MP cap
### D-4-7. blocked draw

## D-5. Effect

### D-5-1. damage
### D-5-2. heal
### D-5-3. gain_mana
### D-5-4. draw_card
### D-5-5. ordered resolution

## D-6. Death / End

### D-6-1. HP floor 0
### D-6-2. defeated event once
### D-6-3. win / loss / draw
### D-6-4. max action boundary
### D-6-5. no action after completion

## D-7. Event

### D-7-1. common fields
### D-7-2. event_id
### D-7-3. action sequence
### D-7-4. payload validation
### D-7-5. snake_case

## D-8. Snapshot

### D-8-1. action 0
### D-8-2. acted_actor_id
### D-8-3. next_actor_id
### D-8-4. deck zones
### D-8-5. gauge state

## D-9. Summary

### D-9-1. result
### D-9-2. end_reason
### D-9-3. action_count
### D-9-4. participant metrics

## D-10. Tests

- deterministic result
- initial draw
- MP不足後続カード
- discard/recycle
- hand full
- multiple gauge triggers
- MP / HP cap
- death
- max action #1000
- Event / Snapshot / Summary整合

---

# 7. M1 Definition of Ready

- [x] 対象人数
- [x] Scenario
- [x] override範囲
- [x] 行動順
- [x] Action Index
- [x] Deck形式
- [x] 初期手札
- [x] hand limit
- [x] recycle
- [x] MP不足探索
- [x] 保留定義
- [x] Gauge
- [x] Effect
- [x] 死亡
- [x] 最大Action境界
- [x] Event
- [x] Snapshot actor
- [x] Summary
- [x] M2境界
- [x] 復活対象外

判定:

```text
Ready
```

---

# 8. M1 Definition of Done

- [x] 味方1体・敵1体で最後まで計算できる
- [x] BattleScenario検証がある
- [x] Action #0 Snapshotがある
- [x] Action #1以降のSnapshotがある
- [x] Deck Runtimeが仕様通り
- [x] Gaugeが仕様通り
- [x] 4Effectが動く
- [x] 死亡・勝敗が動く
- [x] Action #simulation_safety_limit後に引き分け
- [x] Event payloadが契約通り
- [x] Summaryが生成される
- [x] Event / Snapshot / Summaryが整合
- [x] 同一入力で同一結果
- [x] Viewerは戦闘計算を持たない
- [x] 復活未実装
- [x] 3レーン未実装
- [x] make lint成功
- [x] make test成功

---

# 9. M2 WBS

## E-1. API

### E-1-1. request schema
### E-1-2. engine adapter
### E-1-3. response schema
### E-1-4. validation error
### E-1-5. stateless execution

## E-2. Viewer Replay Store

### E-2-1. events
### E-2-2. snapshots
### E-2-3. summary
### E-2-4. cursor

## E-3. Controls

### E-3-1. next
### E-3-2. previous
### E-3-3. +10
### E-3-4. +100
### E-3-5. first
### E-3-6. last
### E-3-7. jump
### E-3-8. autoplay
### E-3-9. speed
### E-3-10. animation lock

## E-4. Display

### E-4-1. HP / MP
### E-4-2. Draw Gauge
### E-4-3. hand / draw / discard
### E-4-4. Action Pipeline phase summary
### E-4-5. Japanese display names
### E-4-6. Debug raw event
### E-4-7. result

---

# 10. M2 Definition of Ready

- [x] API単位
- [x] Engine一括計算
- [x] state保持場所
- [x] cursor単位
- [x] 操作一覧
- [x] 演出中ロック
- [x] 終了時ボタン
- [x] Viewer非計算

判定:

```text
Ready
```

---

# 11. M2 Definition of Done

- [x] simulate APIがReplayを返す
- [x] simulate APIがReplay response schemaを持つ
- [x] ViewerがReplayを表示する
- [x] Action #0では初期状態専用表示を使う
- [x] nextで1Action進む
- [x] previousで1Action戻る
- [x] +10 / +100が終端へ丸められる
- [x] jumpが動く
- [x] autoplayが動く
- [x] autoplay中は手動移動とjumpを無効化する
- [x] speedが戦闘結果へ影響しない
- [x] 演出中に多重操作できない
- [x] 終了位置でnext無効
- [x] `card_draw_blocked`に`draw_source`がある
- [x] Draw Gauge由来のDraw失敗はドローフェーズへ表示する
- [x] Card Effect由来のDraw失敗は効果解決フェーズへ表示する
- [x] Viewerに戦闘計算がない
- [x] Front test成功
- [x] Back test成功

---

# 12. M3-A WBS

## F-1. BattleRuleConfig

### F-1-1. Rule Config Schema
### F-1-2. Git管理Default Config
### F-1-3. Local Override
### F-1-4. GET Rule Config API
### F-1-5. PUT Rule Config API
### F-1-6. atomic save
### F-1-7. Viewer設定画面
### F-1-8. Replayへapplied config保存

## F-2. Deterministic Random

### F-2-1. stable sub-seed導出
### F-2-2. initial deck shuffle stream
### F-2-3. recycle shuffle stream
### F-2-4. respawn shuffle stream
### F-2-5. adjacent target stream
### F-2-6. 同一入力・Seed再現テスト

## F-3. 3レーンAction Scheduler

### F-3-1. Lane ID top / mid / bot
### F-3-2. ally / enemy slot
### F-3-3. Battle全体Action Index
### F-3-4. TOP味方→TOP敵→MID味方→MID敵→BOT味方→BOT敵
### F-3-5. 死亡中slotもAction消費
### F-3-6. Event lane_id

## F-4. 本番Deck Runtime

### F-4-1. original deck
### F-4-2. 戦闘開始shuffle
### F-4-3. initial hand 3
### F-4-4. hand limit 7
### F-4-5. overflow oldest discard
### F-4-6. recycle shuffle
### F-4-7. oldest card only
### F-4-8. blocked oldest stops action
### F-4-9. grant_card_play
### F-4-10. card chain safety error

## F-5. CharacterMaster / CardMaster v2

### F-5-1. AD
### F-5-2. AP
### F-5-3. AR
### F-5-4. MR
### F-5-5. PUSH
### F-5-6. Effect scope
### F-5-7. Damage type
### F-5-8. base_damage
### F-5-9. scaling ratio_bp
### F-5-10. grant_card_play

## F-6. Position / PUSH / Engagement

### F-6-1. position -1000～1000
### F-6-2. initial position 0
### F-6-3. non-engaged movement
### F-6-4. crossing clamp
### F-6-5. engagement start / end
### F-6-6. engaged push difference
### F-6-7. enemy Nexus reach state

## F-7. Respawn

### F-7-1. own-turn counter
### F-7-2. default 3 skipped turns
### F-7-3. HP / MP max reset
### F-7-4. Deck reinitialize / shuffle
### F-7-5. hand initial draw
### F-7-6. discard clear
### F-7-7. Draw Gauge 0
### F-7-8. own Nexus position
### F-7-9. move and engage before draw
### F-7-10. same-action card use after engage

## F-8. Damage Calculator

### F-8-1. base + scaling
### F-8-2. multiple stat scaling
### F-8-3. physical / magic / true
### F-8-4. AR / MR LoL formula
### F-8-5. basis points
### F-8-6. no intermediate rounding
### F-8-7. final floor
### F-8-8. minimum damage 1

## F-9. Scope / Target Resolver

### F-9-1. local Character target
### F-9-2. adjacent TOP/BOT→MID
### F-9-3. adjacent MID→TOP/BOT random
### F-9-4. adjacent no target failure
### F-9-5. global all living enemies
### F-9-6. global order TOP→MID→BOT
### F-9-7. adjacent/global Nexus exclusion

## F-10. Event / Snapshot / Viewer

### F-10-1. lane movement Event
### F-10-2. engagement Event
### F-10-3. deck shuffle / recycle Event
### F-10-4. overflow discard Event
### F-10-5. respawn Event
### F-10-6. target failure Event
### F-10-7. position / push Snapshot
### F-10-8. respawn counter Snapshot
### F-10-9. 3レーンViewer
### F-10-10. lane marker UI

## F-11. Tests

- Scheduler固定順
- 死亡中slotのAction Index
- 初期shuffle再現性
- recycle shuffle再現性
- 初期手札3 / 最大7
- overflow oldest discard
- oldest card block
- grant_card_playによる追加カード使用権
- 移動・cross clamp
- PUSH差
- 復活3回skip
- 復活時full reset
- 復活Actionで対面後にカード使用
- Damage式・丸め・最低1
- Adjacent対象選択
- Adjacent対象なし不発
- Global全生存敵
- Adjacent / GlobalがNexusを対象にしない

---

# 13. M3-A Definition of Ready

- [x] 3レーン構成
- [x] Scheduler順
- [x] Action Index単位
- [x] 死亡中Action扱い
- [x] shuffle条件
- [x] 初期手札
- [x] 手札上限
- [x] overflow処理
- [x] recycle
- [x] 最古カード優先
- [x] Action消費属性
- [x] 復活カウント単位
- [x] 復活時状態
- [x] 復活後移動・行動
- [x] 位置モデル
- [x] PUSH差計算
- [x] Damage式
- [x] 防御式
- [x] 丸め
- [x] Local / Adjacent / Global
- [x] Adjacent対象なし
- [x] Global Nexus除外
- [x] Rule Config編集・保存境界
- [x] 再現性

判定:

```text
Ready
```

---

# 14. M3-A Definition of Done

- [x] 3レーン6participantを最後まで進行できる
- [x] Schedulerが固定順で巡回する
- [x] 死亡中slotで復活カウントが進む
- [x] Battle SeedによるDeck shuffleが決定的
- [x] 初期手札3 / 最大7
- [x] 最大手札Drawで最古カードをdiscardする
- [x] draw pile枯渇時にdiscardをshuffleする
- [x] 最古カード使用不能時に後続を探索しない
- [x] grant_card_playが機能する
- [x] 個別位置・移動・対面が機能する
- [x] PUSH差で対面位置が移動する
- [x] 3回の自分の行動機会を失った後に復活する
- [x] 復活時にHP / MP / Deck / Draw Gaugeをリセットする
- [x] 復活Actionで対面時にカードを使用できる
- [x] AD / AP / AR / MR Damageが仕様通り
- [x] 中間丸めなし・最終floor・最低1
- [x] Adjacentが仕様通り
- [x] Globalが全生存敵だけを対象にする
- [x] Adjacent / GlobalがNexusへfallbackしない
- [x] Rule ConfigをViewerから編集・保存できる
- [x] Replayに適用Configが含まれる
- [x] 3レーンViewerで位置と対面を確認できる
- [x] make lint成功
- [x] make test成功
- [x] coverage 85%以上

---

# 15. M3-B WBS

## G-1. NexusState

### G-1-1. ally / enemy Nexus
### G-1-2. max HP 8000 default
### G-1-3. AR / MR default 0
### G-1-4. Snapshot

## G-2. Nexus Target

### G-2-1. Local only
### G-2-2. enemy Nexus position reached
### G-2-3. no engaged local enemy
### G-2-4. normal Damage card
### G-2-5. Adjacent exclusion
### G-2-6. Global exclusion
### G-2-7. respawn engagement before draw

## G-3. Nexus Damage / End

### G-3-1. standard Damage Calculator
### G-3-2. nexus_damaged
### G-3-3. nexus_destroyed
### G-3-4. Nexus HP floor 0
### G-3-5. ally_win / ally_loss
### G-3-6. no character elimination victory
### G-3-7. no game max actions
### G-3-8. safety limit is error

## G-4. Viewer

### G-4-1. Nexus HP
### G-4-2. Nexus attack target
### G-4-3. Nexus damage phase result
### G-4-4. final result

## G-5. Tests

- Nexus未到達時は攻撃不可
- 対面中はNexus攻撃不可
- Nexus到達・対面なしでLocal DamageがNexusへ向く
- 復活して対面したActionではNexusへ向かない
- Adjacent / GlobalはNexusへ向かない
- Nexus HP 0でのみBattle終了
- Character全滅では終了しない
- Safety Limitはdrawではなくerror

---

# 16. M3-B Definition of Ready

- [x] Nexus数
- [x] Nexus HP
- [x] Nexus防御暫定値
- [x] 攻撃可能位置
- [x] 使用カード
- [x] 対面優先
- [x] Adjacent Nexus除外
- [x] Global Nexus除外
- [x] 復活との順序
- [x] 勝敗条件
- [x] 最大Action撤廃
- [x] Safety Limitの扱い

判定:

```text
Done
```

---

# 17. M3-B Definition of Done

- [x] NexusStateがBattleに存在する
- [x] Nexus最大HP初期値8000
- [x] 通常Local DamageカードでNexusを攻撃できる
- [x] 敵Nexus位置未到達では攻撃できない
- [x] 対面相手がいればCharacterを優先する
- [x] Adjacent対象なしは不発
- [x] Globalは生存敵Characterだけを対象にする
- [x] Nexus HP 0でBattleが終了する
- [x] Character全滅では終了しない
- [x] 本番最大Action数が存在しない
- [x] Safety Limit到達がSimulation Errorになる
- [x] Nexus Event / Snapshot / Viewerが整合する
- [x] make lint成功
- [x] make test成功
- [x] coverage 85%以上

---

# 18. 暫定制約解除WBS

## M3-A

- M1固定turn_orderを3レーンSchedulerへ置換
- M1 shuffleなしをSeed付きshuffleへ置換
- M1 hand limit 5をConfig初期値7へ置換
- M1 playable card scanを最古カード限定へ置換
- M1固定Damageを本番Damageへ置換
- 1対1を3レーン6participantへ拡張
- 復活、位置、PUSH、Scopeを追加

## M3-B

- 全滅勝敗をNexus勝敗へ置換
- M1 simulation_safety_limit drawをM3本番勝敗から廃止
- Local Nexus攻撃を追加

## M4-A

- SUPPORTを追加

## M4-B

- CRT / EVA / 状態異常
- 反撃 / 追撃 / 割り込み
- Trait runtime

---

# 19. Product Owner Decision Gate

## DG-001: 本番Action Scheduler

期限: M3-A前  
Status: Accepted  
Decision: TOP味方→TOP敵→MID味方→MID敵→BOT味方→BOT敵。Battle全体でAction Indexを共有する。

## DG-002: 本番Deck循環

期限: M3-A前  
Status: Accepted  
Decision: Seed付きshuffle、初期手札3、最大7、Recycle時shuffle、最古カード限定、overflow時最古破棄。

## DG-003: 復活テンポ

期限: M3-A前  
Status: Accepted  
Decision: 自分の行動機会を3回失った後、HP / MP最大、Deck / Draw Gauge reset、自陣Nexusから復活する。

## DG-004: 反撃・追撃・割り込み

期限: M4-B前  
Status: Open

## DG-005: 位置・PUSH・対象Scope・Nexus

期限: M3-A前  
Status: Accepted  
Decision: 個別位置、PUSH差、Local / Adjacent / Global、Adjacent対象なし不発、Global Nexus除外、Nexus HP 8000、Nexus破壊勝敗を採用する。

OpenのDecision Gateは、指定マイルストーン以前の開発を妨げない。

ただし対象マイルストーンはDecision GateがAcceptedになるまでReadyにしない。
