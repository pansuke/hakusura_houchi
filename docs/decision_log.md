# Decision Log

## DEC-000: M0 を M0-A と M0-B に分割する

- Status: Accepted
- Date: 2026-06-23
- Context: 元 WBS の M0 には開発環境と Master データ基盤の両方が含まれる。
- Decision: Docker / FastAPI / Viewer / health / lint / test を M0-A、個別 JSON / JSON Schema / build_data.py / 整合性チェックを M0-B として管理する。
- Impact: 現在の成果物は M0-A 完了候補、M0-B 未着手として判定する。

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
