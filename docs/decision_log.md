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

## DEC-009: M2ではAction #0をAction Pipelineとして表示しない

- Status: Accepted
- Date: 2026-06-24
- Context: Action #0は戦闘開始前Snapshotであり、行動準備・ドロー・カードアクション・効果解決・行動終了は実行されていない。
- Decision: Action #0は専用の初期状態表示とし、最初の行動者と初期手札を表示する。
- Impact: ViewerはAction #1以降だけ5フェーズのAction Pipelineを表示する。

## DEC-010: 自動再生中は手動移動を無効化する

- Status: Accepted
- Date: 2026-06-24
- Context: 自動再生タイマーと手動操作が同時にcursorを進めると、Actionを飛ばして表示する可能性がある。
- Decision: 自動再生中は最初・前へ・次へ・+10・+100・最後・Jumpを無効化し、一時停止ボタンだけ操作可能にする。
- Impact: 自動再生と手動操作の競合をM2ではUI制御で防ぐ。

## DEC-011: SUPPORTを8Slot Schedulerへ追加する

- Status: Accepted
- Date: 2026-06-27
- Context: M4-Aでは各SideをTOP / MID / BOT / SUPPORTの4体編成へ拡張する。
- Decision: 固定順をTOP味方、TOP敵、MID味方、MID敵、BOT味方、BOT敵、SUPPORT味方、SUPPORT敵とする。
- Impact: SUPPORTも通常Action Indexを持ち、支援要請0でもActionを実行する。

## DEC-012: SUPPORT Runtimeからレーン固有Stateを除外する

- Status: Accepted
- Date: 2026-06-27
- Context: SUPPORTはレーン上のCharacterではなく、支援先を選択してカードを使用する。
- Decision: SUPPORTはMP / MPR / DS / Draw Gauge / Deck Runtimeを持ち、HP / HPR / 位置 / PUSH / 対面 / 死亡 / 復活を持たない。
- Impact: SUPPORT Snapshotのレーン固有Stateは`null`とし、通常の死亡・復活・移動処理へ流さない。

## DEC-013: 支援先はAction開始時に決定して固定する

- Status: Accepted
- Date: 2026-06-27
- Context: 同一Action内で追加カード使用権が発生しても、支援先がカードごとに変わるとReplay検証が複雑になる。
- Decision: 最大支援要請レーンを選び、同値または全0は専用Seed付きRNGで選択し、同一Action中は固定する。
- Impact: SUPPORTのlocal / adjacent / globalは選択支援レーンを基準に解決し、Nexusは対象にしない。

## DEC-014: 支援属性と支援要請EffectをSchema化する

- Status: Accepted
- Date: 2026-06-27
- Context: 支援属性カードと通常カードをデータで識別し、レーナーから支援要請を追加する必要がある。
- Decision: CardMasterは`support.enabled`と`support.request_reduction`を持ち、支援要請増加Effectは`add_support_request`とする。
- Impact: 支援要請は0～9へclampし、カード使用成功後だけ選択支援レーンから減少する。

## DEC-015: SUPPORT通常カードは対象効果を10%へ減衰する

- Status: Accepted
- Date: 2026-06-27
- Context: SUPPORTは通常Deckを利用できるが、レーナーと同等性能では編成上の役割が崩れる。
- Decision: 非支援カードのDamage / Heal / Draw Gauge増加へ1000BPを適用する。Damageは防御計算前、Heal / Draw Gauge増加は倍率後切り捨てとする。
- Impact: Damageは既存最低値を適用し、通常カード使用成功後は支援要請を1減らす。
