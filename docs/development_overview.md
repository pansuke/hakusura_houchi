# Development Overview

## 目的

このリポジトリの最初の完了条件は、ゲーム実装ではなく M0-A 開発環境基盤の成立でした。

- Docker で開発環境が起動する
- Backend と Viewer の疎通を確認できる
- lint / test を `make` 経由で実行できる
- coverage を `make coverage` 経由で実行できる
- DDD / TDD で拡張できる置き場がある

## マイルストーン分割

### M0-A: 開発環境基盤

- Docker
- FastAPI
- Viewer
- health 疎通
- lint / test
- coverage 85%以上

### M0-B: Master データ基盤

- 個別 JSON
- JSON Schema
- `build_data.py`
- ID 重複チェック
- 参照整合性チェック

現在は M0-A / M0-B 完了候補、M1 / M2 実装済みとして扱う。

### M1: 1対1BattleEngine

- 固定`turn_order`による味方1体・敵1体の戦闘
- 行動権獲得時のHPR / MPR / DS処理
- DSによるDraw Gauge進行とドロー判定
- `damage` / `heal` / `gain_mana` / `draw_card`のEffect解決
- Event / Snapshot / Summary / Display CatalogのReplay生成

### M2: Replay API・開発Viewer

- `POST /api/v1/battles/simulate`
- 計算済みReplayのAction cursor表示
- Action Pipelineによるフェーズ表示
- 日本語名を優先した表示とDebug raw eventの分離

## 採用方針

- Backend は FastAPI と Python で構築する
- Viewer は Vue 3 + Vite + TypeScript で構築する
- Viewer は `package-lock.json` と `npm ci` で依存を固定する
- 初期段階では Postgres を導入しない
- 戦闘ロジックは Viewer に入れない
- Viewer はBattleEngineが生成したReplayを表示するだけにする
- Masterデータは `data/source` の個別 JSON から `data/generated/game-data.json` へ統合する
- M0-Bでは CharacterMaster / TraitMaster / CardMaster のみ対象にする
- HPR / MPR はGaugeではなく、行動権獲得時の確定回復とする
- DSのみDraw Gaugeへ加算し、相手Action中の非行動者には適用しない

## 初期ドメイン境界

- `domain`: Master / Instance / Build / BattleState などの概念
- `engine`: Action Scheduler、Effect Resolver、Event Logger などの戦闘進行
- `data`: Master data のロードと検証
- `api`: Viewer や開発ツールから呼び出す HTTP API

## 未実装

- 3レーン戦闘
- SUPPORT
- 進軍 / ネクサス
- Postgres 永続化
- Playwright E2E

## Masterデータ基盤

- 正本: `data/source/{characters,traits,cards}/*.json`
- Schema: `schemas/*.schema.json`
- CLI: `tools/build_data.py`
- 生成物: `data/generated/game-data.json`
- 検証: Schema、ID形式、ファイル名一致、ID重複、CharacterからTraitへの参照

`make data-build` は検証成功時のみ生成物を置き換える。失敗時は既存の `game-data.json` を維持する。

## Coverage

- Backend: `make back-coverage`
- Frontend: `make front-coverage`
- 全体: `make coverage`

品質ゲートは 85%以上。Backend は Python `coverage` で計測し、`tools/coverage_inspector.py` で未実行行をシンボル単位に出力する。Frontend は Vitest V8 coverage で計測する。
