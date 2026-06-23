"""
テスト一覧:
- health API は status=ok と service 名を返す
- master-data status API は source と generated のパスを返す
- battle prototype status API は M0 で戦闘エンジン未実装であることを返す
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


def test_battle_prototype_status_api_marks_engine_as_not_implemented() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/battles/prototype-status")

    assert response.status_code == 200
    assert response.json()["engine"] == "not_implemented"
