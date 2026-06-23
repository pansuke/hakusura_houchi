# 放置系 × ハクスラ × デッキ構築 RPG

# 開発方針・WBS v1.1

更新日: 2026-06-23
対象: プロトタイプ開始からSteam向け製品化判断まで

---

# 0. この文書の目的

本書は、ゲーム開発を管理するためのWBSおよびマイルストーン定義である。

目的:

* 開発順序を固定する
* 大項目・中項目・小項目を明確にする
* 仕様検討と実装作業を分離する
* AIへ依頼する作業単位を小さくする
* 各マイルストーンのReady条件と完了条件を明確にする
* 未確定仕様を推測で実装しない
* BattleEngineより先にMasterデータ基盤を安定させる

---

# 1. 開発原則

1. 戦闘ロジックと表示を分離する
2. 戦闘は実時間ではなくAction Indexで進行する
3. 同一入力・同一Seedから同一結果を生成する
4. 重要な判断理由を構造化イベントとして残す
5. Masterデータは個別JSONを正本とする
6. 統合JSONを直接編集しない
7. Master・Instance・Build・BattleStateを混同しない
8. 最初から3レーン全体を作らず、1レーンで核を検証する
9. UI完成より、1Actionずつ検証できるViewerを優先する
10. バランス値をコードへ埋め込まない
11. 未確定仕様を勝手に確定しない
12. 各マイルストーンの対象外を明記する

---

# 2. 技術方針

## 2.1 初期構成

* Docker / Docker Compose
* Python 3.12
* FastAPI
* pytest
* Ruff
* JSON Schema
* Vue 3
* TypeScript
* Vite
* Vitest
* HTML開発Viewer

## 2.2 初期段階で導入しないもの

* Postgres
* SQLite
* オンラインPvPサーバー
* 認証
* 課金
* Steamworks
* Steam Cloud
* Electron
* Godot
* AIによる戦闘判断

---

# 3. マイルストーン構成

## M0-A: 開発環境基盤

対象:

* Docker
* FastAPI
* Vue / Vite Viewer
* health API
* Backend / Viewer疎通
* lint
* test
* Makefile
* ドキュメント配置

完了条件:

* `docker compose up`または`make local-up`で起動できる
* Viewerからhealth APIを確認できる
* `make lint`が成功する
* `make test`が成功する
* BattleEngineとViewerの配置が分離されている

対象外:

* Masterデータ統合
* JSON Schema
* BattleEngine
* DB
* 戦闘Viewer

---

## M0-B: Masterデータ基盤

目的:

将来のBattleEngine、API、Viewerが共通利用できる、検証済みで再現可能なMasterデータを生成できるようにする。

対象:

* 1レコード1JSON
* CharacterMaster
* TraitMaster
* CardMaster
* JSON Schema
* build_data.py
* ID規約
* ファイル名とIDの一致確認
* ID重複チェック
* Master間参照チェック
* 決定的な統合JSON生成
* 正常系・異常系テスト

入力:

```text
data/source/**/*.json
schemas/**/*.schema.json
```

出力:

```text
data/generated/game-data.json
```

対象外:

* BattleEngine
* Action Scheduler
* 行動権
* 「次の行動を見る」
* BattleEvent
* MasterデータAPI
* Viewer機能追加
* DB
* CardInstance
* ItemInstance
* Deck
* Build
* PvE
* PvP

完了条件:

* 正常な個別JSONから統合JSONを生成できる
* Schema違反で失敗する
* ID重複で失敗する
* 存在しない参照で失敗する
* ファイル名とID不一致で失敗する
* エラーにファイルパスとJSON Pathが表示される
* 同一入力からバイト単位で同一出力を生成する
* 検証失敗時に既存生成物を破壊しない
* `make data-build`が成功する
* `make lint`が成功する
* `make test`が成功する

---

## M1: 1レーンBattleEngine

目的:

固定された2体以上のキャラクターについて、Actionを1回ずつ解決し、構造化イベントと状態変化を確認できるようにする。

主な対象:

* BattleState
* Action Scheduler
* Action Index
* 固定行動順または採用した最小行動順
* 汎用Gauge
* DS / MRG / HRG
* Deck Runtime
* カード試行
* MP不足
* 保留
* ダメージ
* 死亡
* 復活
* BattleEvent
* BattleSummary
* Seed

Ready条件:

* 行動順の決定方法が定義されている
* 1Actionの境界が定義されている
* 行動不能・死亡時の扱いが定義されている
* 戦闘終了条件が定義されている
* BattleStateの正をBackendとするか決定されている
* BattleEventの最小形式が定義されている

完了条件:

* 1対1の戦闘が最後まで動く
* 1Actionごとに状態が変化する
* 同一入力・同一Seedで結果が一致する
* Actionごとの構造化イベントが生成される

---

## M2: 開発Viewer

目的:

BattleEngineが生成したイベントとSnapshotを、1Actionずつ検証可能にする。

対象:

* 次の行動
* 前の行動
* 10行動進む
* 100行動進む
* 最初に戻る
* 最後まで進む
* 任意Actionへ移動
* 自動再生
* 表示速度変更
* HP / MP / Gauge
* 手札
* 保留理由
* Event詳細

完了条件:

* 1Actionずつ理由を確認できる
* Viewerが戦闘計算を行っていない
* 表示速度が戦闘結果へ影響しない

---

## M3: 3レーン・進軍・ネクサス

対象:

* TOP
* MID
* BOT
* 各レーンBattleState
* 進軍
* ネクサスHP
* レーナー死亡時のネクサス攻撃
* 復活時のレーン復帰
* Local / Adjacent / Global

---

## M4: SUPPORT

対象:

* SUPPORT配置
* HPなし
* 攻撃補正
* 回復補正
* Trait維持
* 支援要請残量
* 支援量
* 支援対象決定

---

## M5: ハクスラ基盤

対象:

* CardInstance
* ItemInstance
* rarity
* RollRule
* fixed
* flat_range
* percent_range
* weighted_table
* Instance性能保存
* ドロップ率
* Seedによる再現

---

## M6: 構築・選出

対象:

* Deck
* EquipmentSet
* Build
* Party
* Formation
* DeckRule
* Legendary採用制限
* 6体登録
* 4体選出

---

## M7: PvE探索

対象:

* 探索エリア
* 固定ステージボーナス
* 複数ステージ
* 探索深度
* 逓減報酬
* 敗北終了
* 資源ロスト
* 高速実行

---

## M8: PvPプロトタイプ

対象:

* 相手Party6体公開
* ステージボーナス公開
* Deck / 装備非公開
* 4体選出
* Formation
* 対戦結果
* バランス集計

---

## M9: 製品化判断

対象:

* 製品UI
* 保存・読込
* HTMLアプリ化
* Electron / NW.js / Godot比較
* Steam配布
* Steam Cloud
* 実績

---

# 4. WBS

# 4.1 大項目A: ドキュメント・Decision Log [P0]

## A-1. ユビキタス言語

対象:

* Master
* Instance
* Deck
* EquipmentSet
* Build
* Party
* Formation
* BattleState
* Action
* ActionIndex
* Trait
* Effect
* RollRule

## A-2. Decision Log

### A-2-1. M0-A / M0-B分割

### A-2-2. Postgres非導入

### A-2-3. FastAPI採用

### A-2-4. Viewer非計算

### A-2-5. Masterデータ正本

### A-2-6. JSON Schema正本

### A-2-7. M0-B対象Master

### A-2-8. 統合JSON出力

### A-2-9. 再現可能ビルド

### A-2-10. M0-B API対象外

完了条件:

* 決定理由と影響範囲が記録されている

---

# 4.2 大項目B: M0-A 開発環境 [P0]

## B-1. Docker

* Backendコンテナ
* Viewerコンテナ
* Docker Compose
* ホットリロード

## B-2. FastAPI

* entrypoint
* health router
* CORS
* API docs

## B-3. Viewer

* Vue 3
* TypeScript
* Vite
* health表示

## B-4. 品質基盤

* pytest
* Ruff
* Vitest
* vue-tsc
* Makefile

完了条件:

* `make local-up`
* `make lint`
* `make test`

が成功する

---

# 4.3 大項目C: M0-B Masterデータ基盤 [P0]

## C-1. ディレクトリ構成

```text
data/
  source/
    characters/
    traits/
    cards/
  generated/
    game-data.json

schemas/
  character.schema.json
  trait.schema.json
  card.schema.json
  definitions/
    effect.schema.json
    roll_rule.schema.json
```

### C-1-1. 1レコード1JSON

### C-1-2. ファイル名を`<id>.json`に統一

### C-1-3. 統合JSONを直接編集禁止

## C-2. ID規約

### C-2-1. 小文字snake_case

### C-2-2. 種別プレフィックス

### C-2-3. IDとファイル名一致

### C-2-4. ID変更は原則禁止

例:

```text
character_warrior_001
trait_adjacent_splash
card_fire_ball
```

## C-3. JSON Schema

### C-3-1. CharacterMaster Schema

### C-3-2. TraitMaster Schema

### C-3-3. CardMaster Schema

### C-3-4. Effect Schema

### C-3-5. RollRule Schema

### C-3-6. additionalProperties制御

### C-3-7. enum・数値範囲

## C-4. build_data.py

処理:

1. ファイル一覧取得
2. JSON構文検証
3. Schema検証
4. ID形式検証
5. ファイル名一致検証
6. ID重複検証
7. Master間参照検証
8. ID順ソート
9. 一時ファイル生成
10. 正常時のみ正式ファイル置換

## C-5. 整合性チェック

### C-5-1. JSON構文

### C-5-2. 必須フィールド

### C-5-3. 型

### C-5-4. enum

### C-5-5. 数値範囲

### C-5-6. ID重複

### C-5-7. ファイル名とID

### C-5-8. CharacterからTrait参照

### C-5-9. Card内Effect / RollRule整合性

## C-6. エラー仕様

* 全エラーを可能な限り列挙
* ファイルパス表示
* JSON Path表示
* 理由表示
* 成功終了コード0
* 失敗終了コード1
* 失敗時に既存生成物を維持

## C-7. 再現可能ビルド

### C-7-1. 出力順固定

### C-7-2. キー順固定

### C-7-3. UTF-8

### C-7-4. LF

### C-7-5. 実行日時を含めない

### C-7-6. 同一入力で同一出力

## C-8. テスト

正常系:

* 正常ビルド
* 複数Master統合
* 正常参照
* Pythonから読込

異常系:

* JSON構文エラー
* 必須項目欠落
* 型不一致
* enum不正
* ID形式不正
* ファイル名不一致
* ID重複
* 存在しない参照
* 数値範囲不正

再現性:

* ファイル作成順に依存しない
* 同一入力で同一出力
* 失敗時に既存生成物を破壊しない

## C-9. Makefile

### C-9-1. `make data-build`

### C-9-2. `make data-validate`

### C-9-3. `make lint`

### C-9-4. `make test`

---

# 4.4 大項目D: Action戦闘モデル [P0]

## D-1. Ready仕様確定

### D-1-1. 最初の行動者

### D-1-2. 行動順

### D-1-3. 同値優先順位

### D-1-4. 1Action境界

### D-1-5. 死亡時のスキップ

### D-1-6. 行動不能

### D-1-7. 追加攻撃・反撃

### D-1-8. 終了条件

## D-2. BattleState

* 現在行動者
* Action Index
* キャラ状態
* Gauge
* Deck Runtime
* BattleStatus

## D-3. Actionパイプライン

1. Action開始
2. 現在行動者決定
3. Gauge更新
4. ドロー
5. カード試行
6. MP判定
7. 対象判定
8. Effect解決
9. 死亡判定
10. 終了判定
11. 次行動者決定
12. Action終了

---

# 4.5 大項目E: Gauge [P0]

## E-1. 汎用Gauge

* currentValue
* gainPerTrigger
* threshold
* overflow
* 複数回発動
* 上限

## E-2. Draw Gauge

## E-3. Mana Gauge

## E-4. Health Regeneration Gauge

---

# 4.6 大項目F: カード実行 [P0]

## F-1. Deck Runtime

## F-2. Card Attempt

## F-3. MP不足

## F-4. 保留

## F-5. Effect Resolver

初期Effect:

* Damage
* Heal
* GainMana
* DrawCard
* AddAdvance
* AddSupportRequest

---

# 4.7 大項目G: 死亡・復活 [P0]

## G-1. ダメージ

## G-2. 死亡

## G-3. 行動対象除外

## G-4. 復活待ち

## G-5. 復活

---

# 4.8 大項目H: Event・Replay [P0]

## H-1. Seed

## H-2. BattleEvent

## H-3. Snapshot

## H-4. Summary

BattleEvent候補:

* ActionStarted
* CardAttempted
* CardHeld
* CardUsed
* DamageApplied
* HealApplied
* CharacterDefeated
* CharacterRevived
* ActionCompleted
* BattleCompleted

---

# 4.9 大項目I: HTML開発Viewer [P0]

## I-1. Replay読込

## I-2. 次の行動

## I-3. 前の行動

## I-4. 複数Action進行

## I-5. 任意Action移動

## I-6. 自動再生

## I-7. Gauge表示

## I-8. Event詳細

## I-9. 失敗理由

## I-10. 多重実行防止

---

# 4.10 大項目J: 3レーン・進軍・ネクサス [P1]

* TOP
* MID
* BOT
* 進軍
* ネクサス
* Local
* Adjacent
* Global

---

# 4.11 大項目K: SUPPORT [P1]

* SUPPORT配置
* HPなし
* 攻撃・回復補正
* 支援要請
* 支援量
* 対象選択

---

# 4.12 大項目L: Instance・ハクスラ [P1]

* CardInstance
* ItemInstance
* rarity
* fixed
* flat_range
* percent_range
* weighted_table
* ドロップ
* ロール保存

---

# 4.13 大項目M: 構築 [P1]

* Deck
* EquipmentSet
* Build
* Party
* Formation
* DeckRule
* Legendary制限

---

# 4.14 大項目N: セーブ [P1]

* SQLite
* Migration
* Repository
* Export / Import
* Backup

---

# 4.15 大項目O: PvE [P1]

* AreaMaster
* StageBonus
* 探索
* 深度
* 報酬
* ロスト
* 高速処理

---

# 4.16 大項目P: バランス検証 [P1]

* N回シミュレーション
* 勝率
* Action数
* Nexus残HP
* MP不足回数
* 保留回数
* カード採用率
* 無限ループ検知

---

# 4.17 大項目Q: PvP [P2]

* Party公開
* StageBonus公開
* 4体選出
* Formation
* 非公開Deck / 装備
* レート
* 非同期方式
* チート対策

---

# 4.18 大項目R: 製品UI [P3]

* レーン表示
* キャラ表示
* カード演出
* 進軍演出
* ネクサス演出
* 支援演出
* 必殺技映像

---

# 4.19 大項目S: Steam [P3]

* パッケージ方式
* Steamworks
* Steam Cloud
* 実績
* リーダーボード
* 配布

---

# 5. M0-B Definition of Ready

以下が決まっている場合、M0-BはReadyとする。

* [x] 目的
* [x] 対象Master
* [x] 1ファイル単位
* [x] ID規則
* [x] Schemaの正本
* [x] build_data.pyの入力
* [x] build_data.pyの出力
* [x] 整合性チェック範囲
* [x] エラー仕様
* [x] 生成物Git管理方針
* [x] 対象外
* [x] 受け入れ条件

判定:

```text
Ready
```

---

# 6. M0-B Definition of Done

* [ ] CharacterMaster個別JSONがある
* [ ] TraitMaster個別JSONがある
* [ ] CardMaster個別JSONがある
* [ ] JSON Schemaがある
* [ ] ID規則を検証できる
* [ ] ファイル名とIDを検証できる
* [ ] ID重複を検出できる
* [ ] 存在しない参照を検出できる
* [ ] エラーにファイルパスとJSON Pathが出る
* [ ] `game-data.json`を生成できる
* [ ] 出力順序が決定的である
* [ ] 同一入力から同一出力になる
* [ ] 失敗時に既存生成物を壊さない
* [ ] 正常系テストがある
* [ ] 異常系テストがある
* [ ] `make data-build`が成功する
* [ ] `make lint`が成功する
* [ ] `make test`が成功する
* [ ] DBを導入していない
* [ ] APIを追加していない
* [ ] BattleEngineを実装していない
* [ ] Viewerへ機能追加していない

---

# 7. 優先順位

## P0

* M0-A
* M0-B
* Action Scheduler
* Gauge
* Card Runtime
* BattleEvent
* 1レーンBattleEngine
* 開発Viewer

## P1

* 3レーン
* 進軍
* ネクサス
* SUPPORT
* Instance
* 構築
* SQLite
* PvE
* バランス検証

## P2

* PvP

## P3

* 製品UI
* Steam
