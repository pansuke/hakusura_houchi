# Lane Relay

放置系 x ハクスラ x デッキ構築 RPG のプロトタイプ基盤です。Docker で FastAPI と Vue/Vite Viewer を起動し、M3の3レーンBattleEngineとReplay API / 開発Viewerを検証できます。

## 現在のスコープ

M0-A 開発環境基盤:
- Docker Compose でバックエンドと Viewer を起動する
- `make` から build / up / lint / test を実行する
- Viewer のトップページから FastAPI の health API を確認する
- DDD と TDD で進めるためのドキュメント置き場を作る

M0-B Master データ基盤:
- `data/source` の個別 JSON
- `schemas` の JSON Schema
- `tools/build_data.py`
- ID 重複チェック
- 参照整合性チェック
- `data/generated/game-data.json` の決定的生成

現在の到達点:

- M0-A: 完了
- M0-B: 完了
- M1: 完了
- M2: 完了
- M3-A: 完了
- M3-B: 完了

未実装:

- SUPPORT
- Counter / Follow-up / Interrupt
- Trait Runtime
- Instance
- PvE
- PvP
- Postgres、認証、課金、Steam 連携

## 必要環境

- Docker
- Docker Compose v2
- GNU Make

## 起動

```bash
make local-build
make local-up
```

起動後に以下を確認します。

- Viewer: http://localhost:5173
- Backend health: http://localhost:8000/health
- Backend API docs: http://localhost:8000/docs

Viewer のトップページでReplayが表示されれば、フロントエンドからBackendのsimulate APIへ疎通できています。

Backend は Docker healthcheck で起動完了を判定し、Viewer は health API を自動リトライします。手動で再確認したい場合はトップページの `Retry` を押します。

## 検証コマンド

```bash
make back-lint
make back-test
make front-lint
make front-test
make data-build
make data-validate
make coverage
```

まとめて実行する場合:

```bash
make lint
make test
```

`make data-build` は `data/source` と `schemas` を検証し、成功時のみ `data/generated/game-data.json` を置き換えます。`make data-validate` は一時ファイルへ出力するため、既存の生成物を変更しません。

Coverage は 85%以上を品質ゲートとします。

```bash
make back-coverage
make front-coverage
make coverage
```

Backend coverage は `tools/coverage_inspector.py` で未実行行をシンボル単位に表示します。

## 構成

```text
backend/
  src/lane_relay/
    api/          FastAPI entrypoint and routers
    domain/       Domain model placeholder
    engine/       M3 BattleEngine
    data/         Master data loading placeholder
  tests/
viewer/
  src/            Vue 3 + TypeScript Viewer
data/
  source/         Character / Trait / Card の個別JSON
  generated/      生成済み game-data.json
schemas/          JSON Schema files
tools/
  build_data.py   Masterデータ統合CLI
docs/             Development notes and decisions
```

## 開発方針

- 戦闘ロジックと表示は分離する
- BattleEngine は Action Index ベースで進行する
- Viewer はイベントとスナップショットを再生する
- 同一入力と同一 Seed から同一結果を生成する
- Master / Instance / Build / BattleState を混同しない
- 未確定仕様は推測で実装しない
- Viewer の依存関係は `package-lock.json` と `npm ci` で固定する
- Masterデータは `data/source` を正本とし、`game-data.json` を直接編集しない

詳細は `docs/development_overview.md` と `docs/decision_log.md` を参照してください。
