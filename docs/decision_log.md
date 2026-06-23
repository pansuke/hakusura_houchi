# Decision Log

## DEC-001: M0 では Postgres を導入しない

- Status: Accepted
- Date: 2026-06-23
- Context: WBS では初期段階で Postgres を導入しない方針が明記されている。
- Decision: まず FastAPI と Viewer の疎通、lint、test、Docker 起動を優先する。
- Impact: 永続化は BattleEngine とデータ基盤が固まった後に再判断する。

## DEC-002: Backend API は FastAPI で開始する

- Status: Accepted
- Date: 2026-06-23
- Context: Python シミュレーション、pytest、Pydantic 検証との相性が高い。
- Decision: `backend/src/lane_relay/api` に FastAPI entrypoint と router を置く。
- Impact: Viewer は HTTP API 経由で Backend の状態を確認する。

## DEC-003: Viewer は戦闘計算を持たない

- Status: Accepted
- Date: 2026-06-23
- Context: 設計書では BattleEngine と Viewer の分離が最重要原則になっている。
- Decision: 初期 Viewer は health API の表示だけにする。
- Impact: 戦闘再生機能は battle events / snapshots の形式が決まってから追加する。
