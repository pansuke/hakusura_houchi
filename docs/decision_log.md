# Decision Log

## DEC-000: M0 を M0-A と M0-B に分割する

- Status: Accepted
- Date: 2026-06-23
- Context: 元 WBS の M0 には開発環境と Master データ基盤の両方が含まれる。
- Decision: Docker / FastAPI / Viewer / health / lint / test を M0-A、個別 JSON / JSON Schema / build_data.py / 整合性チェックを M0-B として管理する。
- Impact: M0-A と M0-B を別々に完了判定する。

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
- Decision: Viewer は BattleEngine が生成した Replay を表示するだけにする。
- Impact: Action cursor、フェーズ表示、日本語表示は Viewer の責務だが、戦闘結果の計算は行わない。

## DEC-004: M0-B 対象Masterは3種に限定する

- Status: Accepted
- Date: 2026-06-23
- Context: 更新されたWBSでは M0-B の対象を CharacterMaster / TraitMaster / CardMaster に限定している。
- Decision: M0-B では `characters`、`traits`、`cards` の個別JSON、Schema、統合生成だけを実装する。
- Impact: Item / Stage / Area / DropTable などは後続マイルストーンで追加する。

## DEC-005: MasterデータAPIはM0-B対象外とする

- Status: Accepted
- Date: 2026-06-23
- Context: 更新された設計書では M0-B で MasterデータAPIを作らないと明記されている。
- Decision: `game-data.json` の生成までをM0-B範囲とし、API公開はBattleEngineやViewerが必要になった時点で追加する。
- Impact: 既存の health / status API 以外に Masterデータ取得APIは追加しない。

## DEC-006: HPR / MPR / DS は行動権獲得者だけ処理する

- Status: Accepted
- Date: 2026-06-23
- Context: 全生存者のGauge更新だと、相手Action中にも非行動者が回復・ドロー進行し、Action単位の検証が分かりにくくなる。
- Decision: HPR / MPR / DS は行動権を獲得した現在行動者だけに適用する。HPR / MPR はGaugeではなく確定回復、DSのみDraw Gaugeとして扱う。
- Impact: `mana_recovered`と`health_recovered`は行動権獲得時の回復を表し、非行動者の回復・Draw Gauge進行は発生しない。

## DEC-007: Replay は display_catalog を含める

- Status: Accepted
- Date: 2026-06-23
- Context: Eventは内部IDを正とするが、Viewer通常表示で内部IDを出すと検証しにくい。
- Decision: BattleReplayに`display_catalog`を含め、参加者名・カード名・カード説明をViewer表示へ渡す。
- Impact: Viewerは通常表示で日本語名を優先し、内部IDと生EventはDebug表示へ隔離する。

## DEC-008: Action Summary はフェーズ表示にする

- Status: Accepted
- Date: 2026-06-23
- Context: Event時系列の箇条書きだけでは、行動準備、ドロー、カード使用、効果、終了判定のどこで何が起きたか判別しづらい。
- Decision: ViewerのAction Summaryは「行動準備」「ドロー」「カードアクション」「効果解決」「行動終了」の5フェーズで表示する。
- Impact: ドロー権獲得、引いたカード、対象、MP消費、HP変化、次行動者をAction単位で確認できる。
