"""
テスト一覧:
- health API は status=ok と service 名を返す
- master-data status API は source と generated のパスを返す
- battle prototype status API はM1/M2の準備状態を返す
- battle simulate API はReplayを返す
- battle simulate API は不正Scenarioを422で返す
- battle simulate API は不正なenum相当値を422で返す
- battle simulate API のCORS preflightが成功する
- battle simulate API はOpenAPI上でReplayレスポンスSchemaを持つ
"""

from fastapi.testclient import TestClient

from lane_relay.api.main import create_app


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
    assert response.json()["engine"] == "m1_ready"


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
        "max_actions": 5,
        "seed": 1,
    }


def test_battle_simulate_api_returns_replay() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/battles/simulate", json=valid_battle_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["result"] == "ally_win"
    assert payload["snapshots"][0]["action_index"] == 0
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
