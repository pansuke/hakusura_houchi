"""
テスト一覧:
- 正常な Character / Trait / Card の個別JSONから決定的な game-data.json を生成する
- Schema違反はファイルパスとJSON Pathつきで失敗する
- ID形式不正とファイル名不一致を検出する
- Master種別をまたいだID重複を検出する
- CharacterMaster.trait_ids の存在しないTrait参照を検出する
- 検証失敗時に既存の生成済みgame-data.jsonを破壊しない
"""

import json
from pathlib import Path

import pytest

from lane_relay.data.master_data_builder import DataBuildError, build_master_data, main


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_schemas(schema_dir: Path) -> None:
    write_json(
        schema_dir / "trait.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "name", "description"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "description": {"type": "string", "minLength": 1},
            },
        },
    )
    write_json(
        schema_dir / "character.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "name", "base_stats", "trait_ids"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "base_stats": {
                    "type": "object",
                    "required": ["hp", "mp", "ad", "ap", "ar", "mr", "ds", "mrg", "hrg"],
                    "additionalProperties": False,
                    "properties": {
                        "hp": {"type": "integer", "minimum": 1},
                        "mp": {"type": "integer", "minimum": 0},
                        "ad": {"type": "integer", "minimum": 0},
                        "ap": {"type": "integer", "minimum": 0},
                        "ar": {"type": "integer", "minimum": 0},
                        "mr": {"type": "integer", "minimum": 0},
                        "ds": {"type": "integer", "minimum": 0},
                        "mrg": {"type": "integer", "minimum": 0},
                        "hrg": {"type": "integer", "minimum": 0},
                    },
                },
                "trait_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
            },
        },
    )
    write_json(
        schema_dir / "card.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["id", "name", "rarity", "mp_cost", "effects"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "rarity": {
                    "type": "string",
                    "enum": ["common", "rare", "epic", "legendary"],
                },
                "mp_cost": {"type": "integer", "minimum": 0},
                "effects": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["type", "target", "power"],
                        "additionalProperties": False,
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["damage", "heal", "gain_mana", "draw_card"],
                            },
                            "target": {"type": "string", "enum": ["self", "enemy"]},
                            "power": {"type": "integer", "minimum": 0},
                        },
                    },
                },
            },
        },
    )


def write_valid_source(source_dir: Path) -> None:
    write_json(
        source_dir / "traits" / "trait_adjacent_splash.json",
        {
            "id": "trait_adjacent_splash",
            "name": "Adjacent Splash",
            "description": "Deals splash damage to adjacent lanes.",
        },
    )
    write_json(
        source_dir / "characters" / "character_warrior_001.json",
        {
            "id": "character_warrior_001",
            "name": "Warrior",
            "base_stats": {
                "hp": 120,
                "mp": 20,
                "ad": 12,
                "ap": 0,
                "ar": 5,
                "mr": 3,
                "ds": 10,
                "mrg": 8,
                "hrg": 2,
            },
            "trait_ids": ["trait_adjacent_splash"],
        },
    )
    write_json(
        source_dir / "cards" / "card_fire_ball.json",
        {
            "id": "card_fire_ball",
            "name": "Fire Ball",
            "rarity": "common",
            "mp_cost": 3,
            "effects": [{"type": "damage", "target": "enemy", "power": 12}],
        },
    )


def test_build_master_data_generates_deterministic_game_data(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    output_path = tmp_path / "generated" / "game-data.json"
    write_schemas(schema_dir)
    write_valid_source(source_dir)

    first = build_master_data(source_dir=source_dir, schema_dir=schema_dir, output_path=output_path)
    first_bytes = output_path.read_bytes()
    second = build_master_data(
        source_dir=source_dir,
        schema_dir=schema_dir,
        output_path=output_path,
    )

    assert first.errors == []
    assert second.errors == []
    assert output_path.read_bytes() == first_bytes
    assert json.loads(first_bytes) == {
        "cards": [
            {
                "effects": [{"power": 12, "target": "enemy", "type": "damage"}],
                "id": "card_fire_ball",
                "mp_cost": 3,
                "name": "Fire Ball",
                "rarity": "common",
            }
        ],
        "characters": [
            {
                "base_stats": {
                    "ad": 12,
                    "ap": 0,
                    "ar": 5,
                    "ds": 10,
                    "hp": 120,
                    "hrg": 2,
                    "mp": 20,
                    "mr": 3,
                    "mrg": 8,
                },
                "id": "character_warrior_001",
                "name": "Warrior",
                "trait_ids": ["trait_adjacent_splash"],
            }
        ],
        "traits": [
            {
                "description": "Deals splash damage to adjacent lanes.",
                "id": "trait_adjacent_splash",
                "name": "Adjacent Splash",
            }
        ],
    }


def test_schema_error_reports_file_path_and_json_path(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    write_json(source_dir / "cards" / "card_fire_ball.json", {"id": "card_fire_ball"})

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "data/source/cards/card_fire_ball.json" in message
    assert "$.name" in message
    assert "required property" in message


def test_nested_schema_error_reports_indexed_json_path(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    card_path = source_dir / "cards" / "card_fire_ball.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["effects"][0]["target"] = "missing_target"
    write_json(card_path, card)

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "$.effects[0].target" in message
    assert "missing_target" in message


def test_invalid_json_duplicate_key_and_non_object_are_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    (source_dir / "traits" / "trait_adjacent_splash.json").write_text(
        '{"id": "trait_adjacent_splash", "id": "trait_adjacent_splash"}\n',
        encoding="utf-8",
    )
    (source_dir / "cards" / "card_fire_ball.json").write_text("[]\n", encoding="utf-8")

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "Duplicate JSON key: id" in message
    assert "Master data must be a JSON object." in message


def test_missing_id_uses_schema_error_without_id_validation_crash(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    write_json(
        source_dir / "traits" / "trait_adjacent_splash.json",
        {"name": "Missing ID", "description": "Missing id."},
    )

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    assert "$.id" in str(exc_info.value)


def test_id_format_and_filename_mismatch_are_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    write_json(
        source_dir / "traits" / "trait_wrong_name.json",
        {"id": "Trait_Invalid", "name": "Invalid", "description": "Invalid id."},
    )

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "$.id" in message
    assert "does not match" in message
    assert "Invalid id format" in message


def test_id_prefix_mismatch_is_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    write_json(
        source_dir / "traits" / "card_wrong_prefix.json",
        {"id": "card_wrong_prefix", "name": "Wrong Prefix", "description": "Wrong prefix."},
    )

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    assert 'Invalid id prefix "card_wrong_prefix". Expected "trait_".' in str(exc_info.value)


def test_duplicate_ids_across_master_types_are_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    write_json(
        source_dir / "cards" / "trait_adjacent_splash.json",
        {
            "id": "trait_adjacent_splash",
            "name": "Duplicate",
            "rarity": "common",
            "mp_cost": 0,
            "effects": [{"type": "heal", "target": "self", "power": 1}],
        },
    )

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    assert "Duplicate id" in str(exc_info.value)


def test_card_roll_rule_range_error_is_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    card_path = source_dir / "cards" / "card_fire_ball.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["roll_rules"] = [
        {"type": "fixed", "value": 10},
        {"type": "flat_range", "min": 5, "max": 3},
        {"type": "weighted_table", "table": [{"value": 1, "weight": 1}]},
    ]
    write_json(card_path, card)

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "$.roll_rules[1]" in message
    assert "RollRule.min must be less than or equal to RollRule.max." in message


def test_schema_ref_resolution_and_missing_ref_schema_are_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    (schema_dir / "definitions").mkdir()
    write_json(
        schema_dir / "definitions" / "name.schema.json",
        {"type": "string", "minLength": 1},
    )
    trait_schema = json.loads((schema_dir / "trait.schema.json").read_text(encoding="utf-8"))
    trait_schema["properties"]["name"] = {"$ref": "definitions/name.schema.json"}
    write_json(schema_dir / "trait.schema.json", trait_schema)

    result = build_master_data(
        source_dir=source_dir,
        schema_dir=schema_dir,
        output_path=tmp_path / "generated" / "game-data.json",
    )

    assert result.errors == []

    trait_schema["properties"]["name"] = {"$ref": "definitions/missing.schema.json"}
    write_json(schema_dir / "trait.schema.json", trait_schema)
    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    assert "schemas/trait.schema.json" in str(exc_info.value)


def test_missing_trait_reference_is_reported(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    character_path = source_dir / "characters" / "character_warrior_001.json"
    character = json.loads(character_path.read_text(encoding="utf-8"))
    character["trait_ids"] = ["trait_missing"]
    write_json(character_path, character)

    with pytest.raises(DataBuildError) as exc_info:
        build_master_data(
            source_dir=source_dir,
            schema_dir=schema_dir,
            output_path=tmp_path / "generated" / "game-data.json",
        )

    message = str(exc_info.value)
    assert "data/source/characters/character_warrior_001.json" in message
    assert "$.trait_ids[0]" in message
    assert 'Referenced TraitMaster "trait_missing" does not exist.' in message


def test_failed_build_preserves_existing_generated_file(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    output_path = tmp_path / "generated" / "game-data.json"
    write_schemas(schema_dir)
    write_valid_source(source_dir)
    output_path.parent.mkdir(parents=True)
    output_path.write_text('{"previous": true}\n', encoding="utf-8")
    write_json(source_dir / "cards" / "card_fire_ball.json", {"id": "card_fire_ball"})

    with pytest.raises(DataBuildError):
        build_master_data(source_dir=source_dir, schema_dir=schema_dir, output_path=output_path)

    assert output_path.read_text(encoding="utf-8") == '{"previous": true}\n'


def test_cli_main_returns_success_and_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dir = tmp_path / "source"
    schema_dir = tmp_path / "schemas"
    output_path = tmp_path / "generated" / "game-data.json"
    write_schemas(schema_dir)
    write_valid_source(source_dir)

    success_code = main(
        [
            "--source",
            str(source_dir),
            "--schemas",
            str(schema_dir),
            "--output",
            str(output_path),
        ]
    )

    assert success_code == 0
    assert f"Built {output_path}" in capsys.readouterr().out

    write_json(source_dir / "cards" / "card_fire_ball.json", {"id": "card_fire_ball"})
    failure_code = main(
        [
            "--source",
            str(source_dir),
            "--schemas",
            str(schema_dir),
            "--output",
            str(output_path),
        ]
    )

    assert failure_code == 1
    assert "ERROR data/source/cards/card_fire_ball.json" in capsys.readouterr().err
