# Lane Relay

放置系 x ハクスラ x デッキ構築 RPG のプロトタイプ基盤です。現段階ではゲーム本体の実装ではなく、Docker で FastAPI と Vue/Vite Viewer を起動し、トップ画面からバックエンド疎通を確認できる M0 開発環境を整えています。

## 現在のスコープ

- Docker Compose でバックエンドと Viewer を起動する
- `make` から build / up / lint / test を実行する
- Viewer のトップページから FastAPI の health API を確認する
- DDD と TDD で進めるためのドキュメント置き場を作る

Postgres、PvP サーバー、認証、課金、Steam 連携、戦闘ロジック本体はまだ導入しません。WBS の M0/B 系を先に固める扱いです。

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

Viewer のトップページで `backend: ok` が表示されれば、フロントエンドからバックエンドへ疎通できています。

## 検証コマンド

```bash
make back-lint
make back-test
make front-lint
make front-test
```

まとめて実行する場合:

```bash
make lint
make test
```

## 構成

```text
backend/
  src/lane_relay/
    api/          FastAPI entrypoint and routers
    domain/       Domain model placeholder
    engine/       Battle engine placeholder
    data/         Master data loading placeholder
  tests/
viewer/
  src/            Vue 3 + TypeScript Viewer
data/
  source/         Source JSON master data
  generated/      Generated game-data.json output
schemas/          JSON Schema files
docs/             Development notes and decisions
```

## 開発方針

- 戦闘ロジックと表示は分離する
- BattleEngine は Action Index ベースで進行する
- Viewer はイベントとスナップショットを再生する
- 同一入力と同一 Seed から同一結果を生成する
- Master / Instance / Build / BattleState を混同しない
- 未確定仕様は推測で実装しない

詳細は `docs/development_overview.md` と `docs/decision_log.md` を参照してください。
