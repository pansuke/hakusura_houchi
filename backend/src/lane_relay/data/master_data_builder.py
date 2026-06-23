from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

JsonObject = dict[str, Any]

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class MasterConfig:
    output_key: str
    source_dir_name: str
    schema_file_name: str
    id_prefix: str


@dataclass(frozen=True)
class MasterRecord:
    config: MasterConfig
    path: Path
    display_path: str
    payload: JsonObject


@dataclass(frozen=True)
class BuildErrorDetail:
    path: str
    json_path: str
    reason: str


@dataclass(frozen=True)
class BuildResult:
    output_path: Path
    errors: list[BuildErrorDetail]


class DataBuildError(Exception):
    def __init__(self, errors: list[BuildErrorDetail]) -> None:
        self.errors = errors
        super().__init__(format_errors(errors))


MASTER_CONFIGS = [
    MasterConfig(
        output_key="characters",
        source_dir_name="characters",
        schema_file_name="character.schema.json",
        id_prefix="character_",
    ),
    MasterConfig(
        output_key="traits",
        source_dir_name="traits",
        schema_file_name="trait.schema.json",
        id_prefix="trait_",
    ),
    MasterConfig(
        output_key="cards",
        source_dir_name="cards",
        schema_file_name="card.schema.json",
        id_prefix="card_",
    ),
]


def build_master_data(source_dir: Path, schema_dir: Path, output_path: Path) -> BuildResult:
    errors: list[BuildErrorDetail] = []
    validators = load_validators(schema_dir=schema_dir, errors=errors)
    records = load_records(source_dir=source_dir, validators=validators, errors=errors)

    validate_unique_ids(records=records, errors=errors)
    validate_references(records=records, errors=errors)

    if errors:
        raise DataBuildError(errors)

    output = build_output(records)
    write_output_atomically(output_path=output_path, payload=output)
    return BuildResult(output_path=output_path, errors=[])


def load_validators(
    schema_dir: Path,
    errors: list[BuildErrorDetail],
) -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    for config in MASTER_CONFIGS:
        schema_path = schema_dir / config.schema_file_name
        try:
            schema = resolve_local_refs(read_json_file(schema_path), schema_dir=schema_dir)
        except JSONDecodeError as exc:
            errors.append(
                BuildErrorDetail(
                    path=display_schema_path(schema_path),
                    json_path="$",
                    reason=f"Invalid JSON: {exc.msg}",
                )
            )
            continue
        except (OSError, ValueError) as exc:
            errors.append(
                BuildErrorDetail(
                    path=display_schema_path(schema_path),
                    json_path="$",
                    reason=f"Cannot read schema: {exc}",
                )
            )
            continue
        validators[config.output_key] = Draft202012Validator(schema)
    return validators


def load_records(
    source_dir: Path,
    validators: dict[str, Draft202012Validator],
    errors: list[BuildErrorDetail],
) -> list[MasterRecord]:
    records: list[MasterRecord] = []
    for config in MASTER_CONFIGS:
        master_dir = source_dir / config.source_dir_name
        for path in sorted(master_dir.glob("*.json")):
            display_path = display_source_path(path=path, config=config)
            try:
                payload = read_json_file(path)
            except JSONDecodeError as exc:
                errors.append(
                    BuildErrorDetail(
                        path=display_path,
                        json_path="$",
                        reason=f"Invalid JSON: {exc.msg}",
                    )
                )
                continue
            except (OSError, ValueError) as exc:
                errors.append(
                    BuildErrorDetail(
                        path=display_path,
                        json_path="$",
                        reason=f"Cannot read file: {exc}",
                    )
                )
                continue

            if not isinstance(payload, dict):
                errors.append(
                    BuildErrorDetail(
                        path=display_path,
                        json_path="$",
                        reason="Master data must be a JSON object.",
                    )
                )
                continue

            records.append(
                MasterRecord(config=config, path=path, display_path=display_path, payload=payload)
            )
            validate_schema(
                validator=validators.get(config.output_key),
                record=records[-1],
                errors=errors,
            )
            validate_id(record=records[-1], errors=errors)
            validate_card_roll_rules(record=records[-1], errors=errors)
    return records


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)


def resolve_local_refs(value: Any, schema_dir: Path) -> Any:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            ref_path = schema_dir / ref
            return resolve_local_refs(read_json_file(ref_path), schema_dir=schema_dir)
        return {
            key: resolve_local_refs(child, schema_dir=schema_dir)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [resolve_local_refs(child, schema_dir=schema_dir) for child in value]
    return value


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_schema(
    validator: Draft202012Validator | None,
    record: MasterRecord,
    errors: list[BuildErrorDetail],
) -> None:
    if validator is None:
        return
    for error in sorted(validator.iter_errors(record.payload), key=schema_error_sort_key):
        errors.append(
            BuildErrorDetail(
                path=record.display_path,
                json_path=json_path_for_schema_error(error),
                reason=schema_error_reason(error),
            )
        )


def validate_id(record: MasterRecord, errors: list[BuildErrorDetail]) -> None:
    record_id = record.payload.get("id")
    if not isinstance(record_id, str):
        return

    expected_id = record.path.stem
    if record_id != expected_id:
        errors.append(
            BuildErrorDetail(
                path=record.display_path,
                json_path="$.id",
                reason=f'ID "{record_id}" does not match file name "{expected_id}".',
            )
        )
    if not ID_PATTERN.fullmatch(record_id):
        errors.append(
            BuildErrorDetail(
                path=record.display_path,
                json_path="$.id",
                reason=f'Invalid id format "{record_id}". Expected lowercase snake_case.',
            )
        )
    if not record_id.startswith(record.config.id_prefix):
        errors.append(
            BuildErrorDetail(
                path=record.display_path,
                json_path="$.id",
                reason=f'Invalid id prefix "{record_id}". Expected "{record.config.id_prefix}".',
            )
        )


def validate_card_roll_rules(record: MasterRecord, errors: list[BuildErrorDetail]) -> None:
    if record.config.output_key != "cards":
        return
    roll_rules = record.payload.get("roll_rules")
    if not isinstance(roll_rules, list):
        return
    for index, roll_rule in enumerate(roll_rules):
        if not isinstance(roll_rule, dict):
            continue
        roll_type = roll_rule.get("type")
        if roll_type not in {"flat_range", "percent_range"}:
            continue
        min_value = roll_rule.get("min")
        max_value = roll_rule.get("max")
        if isinstance(min_value, int) and isinstance(max_value, int) and min_value > max_value:
            errors.append(
                BuildErrorDetail(
                    path=record.display_path,
                    json_path=f"$.roll_rules[{index}]",
                    reason="RollRule.min must be less than or equal to RollRule.max.",
                )
            )


def validate_unique_ids(records: list[MasterRecord], errors: list[BuildErrorDetail]) -> None:
    records_by_id: dict[str, list[MasterRecord]] = defaultdict(list)
    for record in records:
        record_id = record.payload.get("id")
        if isinstance(record_id, str):
            records_by_id[record_id].append(record)

    for record_id, duplicated_records in sorted(records_by_id.items()):
        if len(duplicated_records) < 2:
            continue
        paths = ", ".join(record.display_path for record in duplicated_records)
        for record in duplicated_records:
            errors.append(
                BuildErrorDetail(
                    path=record.display_path,
                    json_path="$.id",
                    reason=f'Duplicate id "{record_id}" found in: {paths}.',
                )
            )


def validate_references(records: list[MasterRecord], errors: list[BuildErrorDetail]) -> None:
    trait_ids = {
        record.payload["id"]
        for record in records
        if record.config.output_key == "traits" and isinstance(record.payload.get("id"), str)
    }
    for record in records:
        if record.config.output_key != "characters":
            continue
        trait_refs = record.payload.get("trait_ids")
        if not isinstance(trait_refs, list):
            continue
        for index, trait_id in enumerate(trait_refs):
            if isinstance(trait_id, str) and trait_id not in trait_ids:
                errors.append(
                    BuildErrorDetail(
                        path=record.display_path,
                        json_path=f"$.trait_ids[{index}]",
                        reason=f'Referenced TraitMaster "{trait_id}" does not exist.',
                    )
                )


def build_output(records: list[MasterRecord]) -> JsonObject:
    output: JsonObject = {}
    for config in MASTER_CONFIGS:
        output[config.output_key] = [
            record.payload
            for record in sorted(
                (record for record in records if record.config == config),
                key=lambda record: record.payload["id"],
            )
        ]
    return output


def write_output_atomically(output_path: Path, payload: JsonObject) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(content)
    temp_path.chmod(0o644)
    temp_path.replace(output_path)


def schema_error_sort_key(error: ValidationError) -> tuple[str, str]:
    return (".".join(str(part) for part in error.path), error.message)


def json_path_for_schema_error(error: ValidationError) -> str:
    if error.validator == "required":
        missing_property = next(iter(error.validator_value))
        if isinstance(error.message, str):
            match = re.search(r"'([^']+)' is a required property", error.message)
            if match:
                missing_property = match.group(1)
        return append_json_path(error.absolute_path, str(missing_property))
    return json_path(error.absolute_path)


def schema_error_reason(error: ValidationError) -> str:
    if error.validator == "required":
        return f"{error.message} required property"
    return error.message


def json_path(parts: Any) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def append_json_path(parts: Any, property_name: str) -> str:
    base = json_path(parts)
    return f"{base}.{property_name}" if base != "$" else f"$.{property_name}"


def display_source_path(path: Path, config: MasterConfig) -> str:
    return f"data/source/{config.source_dir_name}/{path.name}"


def display_schema_path(path: Path) -> str:
    if path.parent.name == "definitions":
        return f"schemas/definitions/{path.name}"
    return f"schemas/{path.name}"


def format_errors(errors: list[BuildErrorDetail]) -> str:
    lines: list[str] = []
    for error in errors:
        lines.extend([f"ERROR {error.path}", f"  {error.json_path}", f"  {error.reason}"])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic Lane Relay master data.")
    parser.add_argument("--source", type=Path, default=Path("data/source"))
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))
    parser.add_argument("--output", type=Path, default=Path("data/generated/game-data.json"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        build_master_data(source_dir=args.source, schema_dir=args.schemas, output_path=args.output)
    except DataBuildError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Built {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
