# Development Overview

## 目的

このリポジトリの最初の完了条件は、ゲーム実装ではなく M0-A 開発環境基盤の成立です。

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

現在は M0-A 完了候補、M0-B 実装開始済みとして扱う。

## 採用方針

- Backend は FastAPI と Python で構築する
- Viewer は Vue 3 + Vite + TypeScript で構築する
- Viewer は `package-lock.json` と `npm ci` で依存を固定する
- 初期段階では Postgres を導入しない
- 戦闘ロジックは Viewer に入れない
- Masterデータは `data/source` の個別 JSON から `data/generated/game-data.json` へ統合する
- M0-Bでは CharacterMaster / TraitMaster / CardMaster のみ対象にする

## 初期ドメイン境界

- `domain`: Master / Instance / Build / BattleState などの概念
- `engine`: Action Scheduler、Effect Resolver、Event Logger などの戦闘進行
- `data`: Master data のロードと検証
- `api`: Viewer や開発ツールから呼び出す HTTP API

## 未実装

- 1レーン戦闘
- リプレイ出力
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
