"""
テスト一覧:
- health API は status=ok と service 名を返す
- master-data status API は source と generated のパスを返す
- battle prototype status API はM3の準備状態を返す
- battle simulate API はReplayを返す
- battle simulate API のSnapshotはAD / AP / AR / MRを返す
- battle simulate API は不正Scenarioを422で返す
- battle simulate API は不正なenum相当値を422で返す
- dev battle-rule-config API はdefault取得・atomic保存・422検証を行う
- battle simulate API のCORS preflightが成功する
- battle simulate API はOpenAPI上でReplayレスポンスSchemaを持つ
"""

from fastapi.testclient import TestClient

from lane_relay.api.main import create_app
from lane_relay.api.routers import dev


def test_health_api_returns_ok_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "lane-relay-backend"}


def test_master_data_status_api_returns_expected_paths() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/master-data/status")

    assert response.status_code == 200
    assert response.json() == {
        "source_dir": "data/source",
        "generated_file": "data/generated/game-data.json",
    }


def test_battle_prototype_status_api_marks_engine_as_ready() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/battles/prototype-status")

    assert response.status_code == 200
    assert response.json()["engine"] == "m3_ready"


def valid_battle_payload() -> dict[str, object]:
    return {
        "battle_id": "battle_api_001",
        "participants": [
            {
                "participant_id": "ally_001",
                "side": "ally",
                "character_master_id": "character_ally_001",
                "max_hp": 20,
                "max_mp": 3,
                "initial_hp": 20,
                "initial_mp": 3,
                "ds": 0,
                "mpr": 0,
                "hpr": 0,
                "ad": 18,
                "ap": 8,
                "ar": 10,
                "mr": 6,
                "deck": [
                    {
                        "card_id": "card_slash",
                        "mp_cost": 0,
                        "effects": [{"effect_type": "damage", "target": "enemy", "value": 99}],
                    }
                ],
            },
            {
                "participant_id": "enemy_001",
                "side": "enemy",
                "character_master_id": "character_enemy_001",
                "max_hp": 10,
                "max_mp": 3,
                "initial_hp": 10,
                "initial_mp": 3,
                "ds": 0,
                "mpr": 0,
                "hpr": 0,
                "deck": [
                    {
                        "card_id": "card_claw",
                        "mp_cost": 0,
                        "effects": [{"effect_type": "damage", "target": "enemy", "value": 1}],
                    }
                ],
            },
        ],
        "turn_order": ["ally_001", "enemy_001"],
        "rule_config": {"simulation_safety_limit": 5},
        "seed": 1,
    }


def test_battle_simulate_api_returns_replay() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/battles/simulate", json=valid_battle_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["result"] == "ally_win"
    assert payload["snapshots"][0]["action_index"] == 0
    ally_snapshot = payload["snapshots"][0]["participants"]["ally_001"]
    assert {
        key: ally_snapshot[key]
        for key in ("ad", "ap", "ar", "mr")
    } == {"ad": 18, "ap": 8, "ar": 10, "mr": 6}
    assert any(event["event_type"] == "battle_completed" for event in payload["events"])
    assert payload["display_catalog"]["participants"]["ally_001"]["name"] == "名称未設定"
    assert payload["display_catalog"]["cards"]["card_slash"]["name"] == "名称未設定"


def test_battle_simulate_api_builds_display_catalog_from_master_data() -> None:
    client = TestClient(create_app())
    payload = valid_battle_payload()
    participants = payload["participants"]
    assert isinstance(participants, list)
    participants[0]["character_master_id"] = "character_warrior_001"
    participants[0]["deck"][0]["card_id"] = "card_fire_ball"

    response = client.post("/api/v1/battles/simulate", json=payload)

    assert response.status_code == 200
    catalog = response.json()["display_catalog"]
    assert catalog["participants"]["ally_001"]["name"] == "戦士"
    assert catalog["cards"]["card_fire_ball"]["name"] == "火球"


def test_battle_simulate_api_returns_422_for_invalid_scenario() -> None:
    client = TestClient(create_app())
    payload = valid_battle_payload()
    payload["turn_order"] = ["ally_001"]

    response = client.post("/api/v1/battles/simulate", json=payload)

    assert response.status_code == 422
    assert "turn_order" in response.json()["detail"]


def test_battle_simulate_api_returns_422_for_invalid_side() -> None:
    client = TestClient(create_app())
    payload = valid_battle_payload()
    participants = payload["participants"]
    assert isinstance(participants, list)
    participants[0]["side"] = "neutral"

    response = client.post("/api/v1/battles/simulate", json=payload)

    assert response.status_code == 422


def test_battle_simulate_api_returns_422_for_invalid_effect_type() -> None:
    client = TestClient(create_app())
    payload = valid_battle_payload()
    participants = payload["participants"]
    assert isinstance(participants, list)
    participants[0]["deck"][0]["effects"][0]["effect_type"] = "poison"

    response = client.post("/api/v1/battles/simulate", json=payload)

    assert response.status_code == 422


def test_dev_battle_rule_config_returns_default_when_local_missing(
    tmp_path,
    monkeypatch,
) -> None:
    default_path = tmp_path / "source" / "rules" / "battle_rule_default.json"
    local_path = tmp_path / "local" / "battle_rule_config.json"
    default_path.parent.mkdir(parents=True)
    default_path.write_text(
        """
        {
          "initial_hand_size": 3,
          "max_hand_size": 7,
          "draw_gauge_threshold": 100,
          "respawn_skip_turns": 3,
          "ally_nexus_position": -1000,
          "enemy_nexus_position": 1000,
          "initial_position": 0,
          "nexus_max_hp": 8000,
          "nexus_ar": 0,
          "nexus_mr": 0,
          "defense_constant": 100,
          "minimum_damage": 1,
          "simulation_safety_limit": 1000,
          "simulation_card_play_limit_per_action": 100
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(dev, "DEFAULT_RULE_CONFIG_PATH", default_path)
    monkeypatch.setattr(dev, "LOCAL_RULE_CONFIG_PATH", local_path)
    client = TestClient(create_app())

    response = client.get("/api/v1/dev/battle-rule-config")

    assert response.status_code == 200
    assert response.json()["nexus_max_hp"] == 8000


def test_dev_battle_rule_config_put_saves_atomically(tmp_path, monkeypatch) -> None:
    default_path = tmp_path / "source" / "rules" / "battle_rule_default.json"
    local_path = tmp_path / "local" / "battle_rule_config.json"
    default_path.parent.mkdir(parents=True)
    default_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(dev, "DEFAULT_RULE_CONFIG_PATH", default_path)
    monkeypatch.setattr(dev, "LOCAL_RULE_CONFIG_PATH", local_path)
    client = TestClient(create_app())
    payload = {
        "initial_hand_size": 3,
        "max_hand_size": 7,
        "draw_gauge_threshold": 100,
        "respawn_skip_turns": 3,
        "ally_nexus_position": -1000,
        "enemy_nexus_position": 1000,
        "initial_position": 0,
        "nexus_max_hp": 9000,
        "nexus_ar": 0,
        "nexus_mr": 0,
        "defense_constant": 100,
        "minimum_damage": 1,
        "simulation_safety_limit": 1000,
        "simulation_card_play_limit_per_action": 100,
    }

    response = client.put("/api/v1/dev/battle-rule-config", json=payload)

    assert response.status_code == 200
    assert response.json()["nexus_max_hp"] == 9000
    assert local_path.exists()
    assert not local_path.with_suffix(".json.tmp").exists()


def test_dev_battle_rule_config_rejects_invalid_values() -> None:
    client = TestClient(create_app())

    response = client.put(
        "/api/v1/dev/battle-rule-config",
        json={"initial_hand_size": 1, "max_hand_size": 0},
    )

    assert response.status_code == 422


def test_battle_simulate_api_returns_422_for_invalid_target() -> None:
    client = TestClient(create_app())
    payload = valid_battle_payload()
    participants = payload["participants"]
    assert isinstance(participants, list)
    participants[0]["deck"][0]["effects"][0]["target"] = "all"

    response = client.post("/api/v1/battles/simulate", json=payload)

    assert response.status_code == 422


def test_battle_simulate_cors_preflight_allows_post() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/battles/simulate",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_battle_simulate_openapi_has_replay_response_schema() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/v1/battles/simulate"]["post"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/BattleReplayResponse"
    }
