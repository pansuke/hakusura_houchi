# 放置系 × ハクスラ × デッキ構築 RPG
# 開発方針・WBS v1.2

更新日: 2026-06-23  
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

Status: Ready

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

Status: Ready

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

Status: Decision Gate待ち

開始前必須:

- DG-001 本番Action Scheduler
- DG-002 本番Deck循環
- DG-003 復活テンポ

対象:

- TOP / MID / BOT
- 複数participant
- 本番Action Scheduler
- CharacterMaster Schema v2
- AD / AP / AR / MR
- 本番Damage式
- 復活
- レーン復帰
- 3レーンSnapshot

---

## M3-B: 進軍・ネクサス

Status: M3-A完了待ち

対象:

- Lane進軍
- NexusState
- ネクサス攻撃
- 本番勝敗
- 本番最大Action・膠着判定
- Local / Adjacent / Global

---

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
### D-1-7. max_actions
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
- [x] Action #max_actions後に引き分け
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

# 12. 暫定制約解除WBS

## M3-A

- M1固定turn_orderを本番Schedulerへ置換
- M1 Deck暫定値を本番値へ置換
- 1対1を複数participantへ拡張
- 1レーンを3レーンへ拡張
- 固定Damageを本番Damageへ置換
- 復活を追加

## M3-B

- 全滅勝敗をNexus勝敗へ置換
- 進軍を追加
- 本番最大Actionを決定

## M4-A

- SUPPORTを追加

## M4-B

- CRT / EVA / 状態異常
- 反撃 / 追撃 / 割り込み
- Trait runtime

---

# 13. Product Owner Decision Gate

## DG-001: 本番Action Scheduler

期限: M3-A前  
Status: Open

## DG-002: 本番Deck循環

期限: M3-A前  
Status: Open

## DG-003: 復活テンポ

期限: M3-A前  
Status: Open

## DG-004: 反撃・追撃・割り込み

期限: M4-B前  
Status: Open

OpenのDecision Gateは、指定マイルストーン以前の開発を妨げない。

ただし対象マイルストーンはDecision GateがAcceptedになるまでReadyにしない。
