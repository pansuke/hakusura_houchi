# 放置系 × ハクスラ × デッキ構築 RPG
# 開発方針・WBS v1.0

作成日: 2026-06-22  
対象: プロトタイプ開始からSteam向け製品化判断まで

---

# 0. この文書の目的

本書は、ゲームの実装を開始するための開発管理基盤である。

目的は以下。

- 開発順序を固定する
- 大項目・中項目・小項目を明確にする
- 仕様検討と実装作業を混同しない
- AIへ作業を依頼するときの単位を小さくする
- 各機能の完了条件を明確にする
- バランス調整可能な基盤を先に作る
- 画面演出より先に、再現可能な戦闘エンジンを完成させる

本書の優先順位は、ゲーム仕様書よりも実装順序に関して優先する。

---

# 1. 開発方針

## 1.1 最重要原則

1. 戦闘ロジックと表示を分離する
2. 戦闘は実時間ではなくAction Indexで進行する
3. 同一入力・同一Seedから同一結果を生成する
4. すべての重要な判断理由をログに残す
5. データは個別JSONで管理し、自動統合する
6. Master・Instance・Build・BattleStateを混同しない
7. 最初から3レーン全機能を作らず、1レーンで核を検証する
8. UI完成よりも、1行動ずつ検証できるViewerを優先する
9. バランス値はコードに埋め込まず、データまたは設定へ出す
10. 未確定仕様を推測で実装しない

---

## 1.2 戦闘進行方式

戦闘エンジンは実時間ベースではなく、行動権ベースとする。

```text
Action #1
↓
行動権の決定
↓
ゲージ更新
↓
カード処理
↓
効果解決
↓
状態更新
↓
Action #2
```

### Action Index

戦闘内で発生した行動単位の連番。

例:

```text
Action #1
Action #2
Action #3
```

BattleEngineはAction Indexを基準に進行・保存・再生する。

### 表示時間

ユーザーに見せる秒数やアニメーション時間はViewer側で管理する。

```text
内部:
Action #152

表示:
0.8秒かけてカード演出
```

表示速度を変えても、戦闘結果は変化しない。

---

## 1.3 ゲージ進行方式

以下はActionの進行に紐づくゲージとして実装する。

- DS: Draw Speed / ドローゲージ増加量
- MRG: Mana Regeneration / MP回復ゲージ増加量
- HRG: Health Regeneration / HP回復ゲージ増加量

基本モデル:

```text
行動権が移動
↓
対象ゲージへ増加値を加算
↓
しきい値以上なら効果発動
↓
超過分は次回へ繰り越し
```

例:

```text
DrawGauge = 85
DS = 20
Threshold = 100

85 + 20 = 105
↓
カードを1枚ドロー
↓
DrawGauge = 5
```

### 未確定事項

以下は最初の設計スパイクで確定する。

- ゲージ増加対象が全キャラか、行動者か、同一レーンの2体か
- SUPPORTの行動権
- 3レーン間の行動順序
- 死亡中キャラのゲージ進行可否
- 保留カードが行動権を消費するか

---

## 1.4 データ駆動

ゲーム定義は個別JSONで管理する。

```text
data/
  source/
    characters/
    traits/
    cards/
    items/
    stages/
  generated/
    game-data.json
```

ゲーム本体は `game-data.json` のみを読む。

個別JSONは人間・AIの編集単位であり、実行時データではない。

---

## 1.5 レイヤー分離

### Master

ゲームに存在する定義。

- CharacterMaster
- TraitMaster
- CardMaster
- ItemMaster
- StageMaster

### Instance

プレイヤーが所有する個体。

- CharacterInstance
- CardInstance
- ItemInstance

### 構築データ

- Deck
- EquipmentSet
- Build
- Party
- Formation

### BattleState

戦闘中のみ存在する一時状態。

---

## 1.6 ログ・リプレイ優先

すべての戦闘は、結果だけでなく理由を追跡可能にする。

必須出力:

- battle_events.jsonl
- battle_snapshots.jsonl
- battle_summary.json

Viewerはこれらを読み込むだけとし、戦闘計算を行わない。

---

## 1.7 テスト方針

最低限、以下を自動テストする。

- 同じSeedで同じ結果になる
- ゲージ超過分が正しく繰り越される
- MP不足時にカードが発動しない
- 死亡中のキャラが不正に行動しない
- 復活後のHPが仕様どおりになる
- データ参照切れをビルド時に検知する
- JSONのID重複を検知する
- ログからBattleStateを再現できる

---

# 2. 推奨技術構成

## 2.1 開発環境

- Docker / Docker Compose
- Python
- pytest
- JSON SchemaまたはPydanticによる検証
- HTML / TypeScript
- ブラウザベースの開発Viewer
- SQLiteは所持データ実装時に導入

## 2.2 推奨プロジェクト構成

```text
project-root/
  docs/
  data/
    source/
    generated/
  schemas/
  simulator/
    domain/
    engine/
    application/
    tests/
  tools/
    build_data.py
    run_simulation.py
  viewer/
    src/
    public/
  replays/
  docker-compose.yml
  README.md
```

## 2.3 初期段階で導入しないもの

- Postgres
- オンラインPvPサーバー
- Steamworks
- Steam Cloud
- Electron
- Godot
- 本番用アカウント管理
- 課金システム
- AIによる戦闘判断

これらはBattleEngineの成立後に判断する。

---

# 3. 開発マイルストーン

## M0: 開発基盤成立

完了状態:

- Dockerで開発環境が起動する
- 個別JSONを統合できる
- Schema検証が動く
- 自動テストが実行できる

## M1: 1レーン戦闘成立

完了状態:

- 1対1の行動権戦闘が最後まで動く
- DS / MRG / HRGがAction単位で進む
- カードのドロー・保留・発動が動く
- 死亡・復活が動く
- 同じSeedで同じ結果になる
- 1行動ずつログで追える

## M2: 開発Viewer成立

完了状態:

- 次の行動ボタンで1Action進められる
- 10Action・100Action・最後まで進められる
- 任意Actionから再生できる
- HP / MP / 各ゲージ / 手札 / 保留理由を確認できる

## M3: 3レーン戦闘成立

完了状態:

- TOP / MID / BOTが並行して進行する
- 各レーンの進軍が押し引きする
- 敵不在時にネクサスへ攻撃する
- 復活でレーン戦へ戻る

## M4: SUPPORT成立

完了状態:

- 4体目をSUPPORTへ配置できる
- HPなし・補正付きで動作する
- 支援要請残量と支援量が動作する

## M5: ハクスラ基盤成立

完了状態:

- CardMasterからCardInstanceを生成できる
- 数値ロールが保存される
- レアリティごとのドロップ率を設定できる
- ItemInstanceにも同じロール基盤を利用できる

## M6: 構築・選出成立

完了状態:

- Deckを独立保存できる
- Buildを作成できる
- Build×6でPartyを作成できる
- 6体から4体を選出しFormationを作成できる

## M7: PvE縦切り成立

完了状態:

- 探索エリアを選べる
- 固定ステージボーナスが適用される
- 複数ステージを連続実行できる
- 探索深度・報酬・敗北ペナルティが動く

## M8: PvPプロトタイプ成立

完了状態:

- 相手Party6体を表示できる
- 装備・Deckは非公開
- ステージボーナス公開後に4体選出できる
- 自動戦闘結果をViewerで再生できる

## M9: 製品化判断

完了状態:

- HTMLクライアントでゲームループを遊べる
- 保存・読込が安定する
- Steam向けパッケージ方式を比較できる
- コンテンツ量産コストを測定できる

---

# 4. WBS

# 4.1 大項目A: ドキュメント・ルール固定 [P0]

## A-1. 用語の固定

### A-1-1. ユビキタス言語を文書化する

対象:

- Master
- Instance
- Deck
- EquipmentSet
- Build
- Party
- Formation
- BattleState
- Action
- ActionRight
- ActionIndex
- Trait
- Effect
- RollRule

完了条件:

- 各用語に「何を保持するか」「何を保持しないか」が記載されている
- コード名と文書名が一致している

### A-1-2. DS / MRG / HRGの定義を更新する

完了条件:

- 「毎秒」ではなく「Action進行時のゲージ増加量」と記載されている
- しきい値・繰り越しルールが記載されている

## A-2. 未確定仕様一覧を管理する

### A-2-1. Decision Logを作る

例:

```text
DEC-001 行動権を実時間からAction方式へ変更
DEC-002 DeckはBuildと別に保存
DEC-003 CardのレアリティとInstance性能ロールを分離
```

完了条件:

- 決定理由と影響範囲が残る

---

# 4.2 大項目B: リポジトリ・開発環境 [P0]

## B-1. リポジトリ初期化

### B-1-1. ディレクトリ作成
### B-1-2. README作成
### B-1-3. .gitignore作成
### B-1-4. 命名規約作成

完了条件:

- 新規開発者がREADMEだけで起動方法を理解できる

## B-2. Docker環境

### B-2-1. Python開発コンテナ
### B-2-2. Viewer開発コンテナ
### B-2-3. Docker Compose統合
### B-2-4. ボリューム・ホットリロード設定

完了条件:

```text
docker compose up
```

でSimulatorとViewerの開発環境が起動する。

## B-3. 品質基盤

### B-3-1. テスト実行コマンド
### B-3-2. 静的解析
### B-3-3. フォーマッタ
### B-3-4. CI候補の設定

完了条件:

- 1コマンドで検証一式を実行できる

---

# 4.3 大項目C: Masterデータ基盤 [P0]

## C-1. データファイル構成

### C-1-1. CharacterMaster個別JSON
### C-1-2. TraitMaster個別JSON
### C-1-3. CardMaster個別JSON
### C-1-4. ItemMaster個別JSON
### C-1-5. StageMaster個別JSON

完了条件:

- 1定義1ファイルになっている
- 人間とAIが他ファイルを触らず追加できる

## C-2. Schema設計

### C-2-1. 共通ID形式
### C-2-2. Character Schema
### C-2-3. Trait Schema
### C-2-4. Card Schema
### C-2-5. Effect Schema
### C-2-6. RollRule Schema

完了条件:

- 不正なJSONをビルド前に検知する

## C-3. データ統合

### C-3-1. build_data.py
### C-3-2. ID重複チェック
### C-3-3. 参照先存在チェック
### C-3-4. 統合JSON出力
### C-3-5. ビルドレポート出力

完了条件:

- `game-data.json` が決定的な順序で生成される
- 同じsourceから同一ファイルが生成される

---

# 4.4 大項目D: Action戦闘モデル設計 [P0]

## D-1. Action Scheduler設計スパイク

### D-1-1. 行動権の保持単位を決める
### D-1-2. 1レーン内の交互行動ルールを決める
### D-1-3. 3レーン間の選択ルール候補を比較する
### D-1-4. SUPPORTの行動タイミング候補を比較する
### D-1-5. 保留カードの扱いを決める

成果物:

- Action Scheduler仕様書
- 代表的な時系列例
- 採用案の決定記録

完了条件:

- 乱数なしの簡易戦闘を紙上で最後まで追える

## D-2. BattleState設計

### D-2-1. Battle全体状態
### D-2-2. CharacterBattleState
### D-2-3. LaneBattleState
### D-2-4. NexusBattleState
### D-2-5. CardRuntimeState
### D-2-6. GaugeState

完了条件:

- 保存データと戦闘中データが分離されている

## D-3. Action実行パイプライン

### D-3-1. Action開始
### D-3-2. ゲージ増加
### D-3-3. しきい値解決
### D-3-4. ドロー処理
### D-3-5. カード試行
### D-3-6. MP判定
### D-3-7. 対象判定
### D-3-8. Effect解決
### D-3-9. 死亡判定
### D-3-10. 進軍判定
### D-3-11. Action終了

完了条件:

- 各処理順がテストで固定されている

---

# 4.5 大項目E: リソース・ゲージ基盤 [P0]

## E-1. 汎用Gauge

### E-1-1. currentValue
### E-1-2. gainPerTrigger
### E-1-3. threshold
### E-1-4. overflow繰り越し
### E-1-5. 複数回発動対応
### E-1-6. 上限値対応

完了条件:

- DS / MRG / HRGが同じGauge実装を利用する

## E-2. Draw Gauge

### E-2-1. ゲージ増加
### E-2-2. ドロー
### E-2-3. 山札切れ
### E-2-4. 手札上限
### E-2-5. 捨て札・再シャッフル

## E-3. Mana Gauge

### E-3-1. MP回復
### E-3-2. MP上限
### E-3-3. MP消費
### E-3-4. MP不足時の保留

## E-4. Health Regeneration Gauge

### E-4-1. HP回復
### E-4-2. 最大HP制限
### E-4-3. 死亡中の回復可否
### E-4-4. 過剰回復の扱い

---

# 4.6 大項目F: カード実行基盤 [P0]

## F-1. Deck Runtime

### F-1-1. 山札生成
### F-1-2. シャッフル
### F-1-3. ドロー
### F-1-4. 手札
### F-1-5. 保留
### F-1-6. 捨て札
### F-1-7. 再シャッフル

## F-2. Card Attempt

### F-2-1. 発動条件
### F-2-2. MP条件
### F-2-3. 対象条件
### F-2-4. レーン条件
### F-2-5. 失敗理由
### F-2-6. 保留とキャンセル

## F-3. Effect基盤

初期Effect:

- Damage
- Heal
- GainMana
- DrawCard
- AddAdvance
- AddSupportRequest

完了条件:

- Effect追加時にBattleEngine本体を大きく変更しない

---

# 4.7 大項目G: ダメージ・死亡・復活 [P0]

## G-1. ダメージ計算

### G-1-1. AD参照
### G-1-2. AP参照
### G-1-3. AR軽減
### G-1-4. MR軽減
### G-1-5. CRT
### G-1-6. EVA

初期方針:

- 低い数値レンジで開始
- 計算式は単純にする
- 計算過程をログへ出す

## G-2. 死亡

### G-2-1. HP0判定
### G-2-2. 行動停止
### G-2-3. 手札の扱い
### G-2-4. ゲージの扱い
### G-2-5. レーン不在状態

## G-3. 復活

### G-3-1. 復活条件
### G-3-2. 復活待ちをAction数で管理
### G-3-3. HP回復率
### G-3-4. MP・ゲージの復帰状態
### G-3-5. レーン復帰

---

# 4.8 大項目H: 決定的乱数・リプレイ [P0]

## H-1. Seed管理

### H-1-1. Battle Seed
### H-1-2. シャッフル用乱数
### H-1-3. CRT / EVA用乱数
### H-1-4. 対象選択用乱数

完了条件:

- 同じ入力とSeedでevent logが完全一致する

## H-2. Event Log

### H-2-1. eventId
### H-2-2. actionIndex
### H-2-3. actorId
### H-2-4. targetId
### H-2-5. eventType
### H-2-6. before / after
### H-2-7. reason

## H-3. Snapshot

### H-3-1. Action単位の保存頻度
### H-3-2. 全状態シリアライズ
### H-3-3. 任意Actionから再生
### H-3-4. SnapshotとEventの整合確認

---

# 4.9 大項目I: HTML開発Viewer [P0]

## I-1. Viewer骨格

### I-1-1. リプレイ読込
### I-1-2. Battle Summary表示
### I-1-3. Action Index表示
### I-1-4. 現在の行動者表示

## I-2. 再生操作

### I-2-1. 次の行動
### I-2-2. 前の行動
### I-2-3. 10行動進む
### I-2-4. 100行動進む
### I-2-5. 最後まで進む
### I-2-6. 最初へ戻る
### I-2-7. 任意Actionへジャンプ
### I-2-8. 自動再生
### I-2-9. 表示速度変更

## I-3. キャラ状態表示

### I-3-1. HP
### I-3-2. MP
### I-3-3. Draw Gauge
### I-3-4. Mana Gauge
### I-3-5. Health Regeneration Gauge
### I-3-6. 手札
### I-3-7. 保留カード
### I-3-8. バフ・デバフ

## I-4. イベント詳細

### I-4-1. 試行した行動
### I-4-2. 成功理由
### I-4-3. 失敗理由
### I-4-4. ダメージ計算内訳
### I-4-5. ゲージ増加内訳
### I-4-6. 乱数結果

完了条件:

- 1Actionずつ進めながら、なぜその結果になったか説明できる

---

# 4.10 大項目J: 3レーン・進軍・ネクサス [P1]

## J-1. 3レーン状態

### J-1-1. TOP
### J-1-2. MID
### J-1-3. BOT
### J-1-4. 各レーン独立状態
### J-1-5. グローバルBattle状態

## J-2. 進軍

### J-2-1. 進軍値
### J-2-2. 中立位置
### J-2-3. 味方最大位置
### J-2-4. 敵最大位置
### J-2-5. 進軍増減イベント
### J-2-6. Viewerゲージ表示

## J-3. ネクサス

### J-3-1. Nexus HP
### J-3-2. 攻撃開始条件
### J-3-3. レーナー復活による攻撃停止
### J-3-4. 勝敗判定
### J-3-5. 不可逆ダメージ

## J-4. レーン介入

### J-4-1. Local
### J-4-2. Adjacent
### J-4-3. Global
### J-4-4. MIDの隣接関係
### J-4-5. 進軍と介入条件

---

# 4.11 大項目K: SUPPORT [P1]

## K-1. SUPPORT配置

### K-1-1. 全キャラ配置可能
### K-1-2. HPなし
### K-1-3. 攻撃補正
### K-1-4. 回復補正
### K-1-5. Trait維持

## K-2. 支援要請

### K-2-1. レーン別要請残量
### K-2-2. 要請加算
### K-2-3. 最大値候補
### K-2-4. 同値時の処理

## K-3. 支援実行

### K-3-1. 支援量
### K-3-2. 対象選択
### K-3-3. 要請残量減算
### K-3-4. 0未満にしない
### K-3-5. 支援不能ログ

---

# 4.12 大項目L: CardInstance・ItemInstance [P1]

## L-1. レアリティ

### L-1-1. CardMaster自身がrarityを持つ
### L-1-2. rarityごとのドロップ率
### L-1-3. レアカードはカード自体が希少
### L-1-4. Instanceロールとrarityを分離

## L-2. RollRule

採用候補:

- fixed
- flat_range
- percent_range
- weighted_table

`weighted_table` は離散値抽選に使用する。

`tier_table` は採用しない。

### L-2-1. 数値ロール
### L-2-2. スキルレベルロール
### L-2-3. 対象数ロール
### L-2-4. Seedによる再現
### L-2-5. 結果のInstance保存

## L-3. CardInstance生成

### L-3-1. instanceId
### L-3-2. masterId
### L-3-3. rolledValues
### L-3-4. 所有者
### L-3-5. ロック・お気に入り候補

## L-4. ItemInstance生成

CardInstanceと共通のロール基盤を利用する。

## L-5. デッキ構築制限

レジェンダリーは、コスト効率が意図的に高い強カードとする。

検討事項:

- デッキ内レジェンダリー総数制限
- カード個別の最大採用枚数
- PvPのみの制限
- 制限値のデータ化

完了条件:

- 制限方式がCardMasterまたはDeckRuleから検証可能

---

# 4.13 大項目M: Deck・Build・Party・Formation [P1]

## M-1. Deck

### M-1-1. Deck独立保存
### M-1-2. CardInstance参照
### M-1-3. コピー
### M-1-4. 名前変更
### M-1-5. 構築ルール検証
### M-1-6. 複数Buildから共有

## M-2. EquipmentSet

### M-2-1. ItemInstance参照
### M-2-2. 装備スロット
### M-2-3. コピー
### M-2-4. 競合チェック

## M-3. Build

```text
CharacterInstance
+
Deck
+
EquipmentSet
```

### M-3-1. 作成
### M-3-2. 更新
### M-3-3. コピー
### M-3-4. 戦闘用Snapshot生成

## M-4. Party

### M-4-1. Build×6
### M-4-2. 重複ルール
### M-4-3. 保存
### M-4-4. PvE / PvP用途

## M-5. Formation

### M-5-1. 6体から4体選出
### M-5-2. TOP配置
### M-5-3. MID配置
### M-5-4. BOT配置
### M-5-5. SUPPORT配置
### M-5-6. 配置妥当性検証

---

# 4.14 大項目N: セーブデータ [P1]

## N-1. 保存対象

- CharacterInstance
- CardInstance
- ItemInstance
- Deck
- EquipmentSet
- Build
- Party
- 設定
- 進行状況

## N-2. SQLite

### N-2-1. DB Schema
### N-2-2. Migration
### N-2-3. Repository層
### N-2-4. Export / Import
### N-2-5. バックアップ

## N-3. 保存しない対象

BattleStateは原則保存しない。

保存対象はReplayとして分離する。

---

# 4.15 大項目O: PvE探索 [P1]

## O-1. エリア

### O-1-1. エリアMaster
### O-1-2. 固定レーンボーナス
### O-1-3. ドロップテーブル
### O-1-4. 敵Party

## O-2. 1探索

### O-2-1. 複数ステージ
### O-2-2. 深度
### O-2-3. 逓減報酬倍率
### O-2-4. 敗北終了
### O-2-5. 資源ロスト
### O-2-6. 上限到達

## O-3. 高速実行

### O-3-1. 結果のみ
### O-3-2. 複数戦闘一括
### O-3-3. Replay選択保存

---

# 4.16 大項目P: バランス検証基盤 [P1]

## P-1. バッチシミュレーション

### P-1-1. N回実行
### P-1-2. Seed一覧
### P-1-3. キャラ組み合わせ
### P-1-4. Deck組み合わせ
### P-1-5. Formation組み合わせ

## P-2. 集計

- 勝率
- 平均Action数
- 平均Nexus残HP
- 与ダメージ
- 被ダメージ
- 回復量
- MP不足回数
- カード保留回数
- ドロー回数
- レーン別進軍占有率
- カード別採用率
- カード別勝率

## P-3. 異常検知

### P-3-1. 無限ループ
### P-3-2. Action上限超過
### P-3-3. 永久保留
### P-3-4. 一方的すぎる勝率
### P-3-5. 未使用カード

---

# 4.17 大項目Q: PvPプロトタイプ [P2]

## Q-1. マッチ入力

### Q-1-1. 自Party
### Q-1-2. 相手Party
### Q-1-3. ステージボーナス
### Q-1-4. Seed

## Q-2. 公開情報

- 相手キャラ6体
- ステージボーナス

非公開:

- Deck
- EquipmentSet
- 詳細Build

## Q-3. 選出・配置

### Q-3-1. 自分の4体選出
### Q-3-2. 相手の4体選出
### Q-3-3. Formation作成
### Q-3-4. Battle開始

## Q-4. 公平性

### Q-4-1. レート候補
### Q-4-2. 同期対戦か非同期対戦か
### Q-4-3. 相手データSnapshot
### Q-4-4. チート対策方針

---

# 4.18 大項目R: 製品UI・演出 [P3]

## R-1. 開発Viewerから製品Viewerへ

### R-1-1. レーン表示
### R-1-2. キャラ表示
### R-1-3. カード演出
### R-1-4. 進軍アニメーション
### R-1-5. ネクサス攻撃
### R-1-6. 支援演出

## R-2. 必殺技映像

### R-2-1. 動画参照方式
### R-2-2. 再生条件
### R-2-3. スキップ
### R-2-4. AI生成素材の権利管理
### R-2-5. 軽量化

---

# 4.19 大項目S: Steam製品化 [P3]

## S-1. パッケージ方式比較

候補:

- Electron
- NW.js
- Godot移植

評価軸:

- AIによる編集容易性
- 配布サイズ
- パフォーマンス
- Steamworks連携
- 動画再生
- 自動ビルド

## S-2. Steam連携

### S-2-1. 実績
### S-2-2. Steam Cloud
### S-2-3. リーダーボード
### S-2-4. ビルド配布
### S-2-5. セーブ互換性

---

# 5. 最初の実装バッチ

以下だけを最初の開発者へ依頼する。

## 5.1 対象

1. Docker開発環境
2. Master JSON最小Schema
3. build_data.py
4. 1レーンのAction Scheduler
5. 汎用Gauge
6. DS / MRG / HRG
7. 2種類のカード
8. MP不足による保留
9. ダメージ・死亡・復活
10. Event Log
11. 最小HTML Viewer
12. 次の行動ボタン

## 5.2 使用する最小データ

キャラ:

- Character A
- Character B

カード:

- 低コスト攻撃カード
- 高コスト攻撃カード

状態:

- HP
- MP
- DrawGauge
- ManaGauge
- HealthRegenerationGauge

## 5.3 対象外

- 3レーン
- 進軍
- ネクサス
- SUPPORT
- アイテム
- ハクスラ
- Party
- Formation
- PvP
- 探索
- Steam

## 5.4 完了条件

Viewerで以下を確認できる。

```text
Action #12
Character A
高コスト攻撃カードを試行
MP不足
カードを保留

ManaGauge +20
しきい値到達
MP +1

Action #16
Character A
保留カードを再試行
発動成功
Character Bへ30ダメージ
```

---

# 6. Definition of Done

各タスクは以下を満たして完了とする。

- 仕様が文書化されている
- Master / Instance / BattleStateのどの層か明記されている
- 自動テストがある
- 失敗理由がログに出る
- 同一Seedで再現できる
- Viewerで結果を確認できる
- 数値がコードに直接埋め込まれていない
- READMEまたは該当ドキュメントが更新されている
- 未確定仕様を勝手に確定していない

---

# 7. 優先順位まとめ

## P0: 最初に必須

- ドキュメント・用語
- Docker
- Masterデータ基盤
- Action Scheduler
- Gauge
- Card Runtime
- ダメージ・死亡・復活
- Seed
- Event / Snapshot
- HTML Viewer
- 1レーン縦切り

## P1: ゲーム性の核

- 3レーン
- 進軍
- ネクサス
- SUPPORT
- CardInstance / ItemInstance
- Deck / Build / Party / Formation
- SQLite
- PvE探索
- バランス検証

## P2: 対戦検証

- PvP選出
- 公開情報
- レート
- 非同期対戦方式

## P3: 製品化

- 製品UI
- 必殺技映像
- Steamパッケージ
- Steam Cloud
- 実績
