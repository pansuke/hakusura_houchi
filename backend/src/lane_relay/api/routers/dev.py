import json
import os
from pathlib import Path

from fastapi import APIRouter

from lane_relay.api.schemas import BattleRuleConfigRequest, BattleRuleConfigResponse

router = APIRouter(prefix="/dev", tags=["dev"])

DEFAULT_RULE_CONFIG_PATH = Path("/workspace/data/source/rules/battle_rule_default.json")
LOCAL_RULE_CONFIG_PATH = Path("/workspace/data/local/battle_rule_config.json")


@router.get("/battle-rule-config", response_model=BattleRuleConfigResponse)
def get_battle_rule_config() -> BattleRuleConfigRequest:
    return load_battle_rule_config()


@router.put("/battle-rule-config", response_model=BattleRuleConfigResponse)
def put_battle_rule_config(config: BattleRuleConfigRequest) -> BattleRuleConfigRequest:
    save_battle_rule_config(config)
    return config


def load_battle_rule_config() -> BattleRuleConfigRequest:
    path = LOCAL_RULE_CONFIG_PATH if LOCAL_RULE_CONFIG_PATH.exists() else DEFAULT_RULE_CONFIG_PATH
    with path.open(encoding="utf-8") as config_file:
        return BattleRuleConfigRequest.model_validate(json.load(config_file))


def save_battle_rule_config(config: BattleRuleConfigRequest) -> None:
    LOCAL_RULE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = LOCAL_RULE_CONFIG_PATH.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as config_file:
        json.dump(config.model_dump(), config_file, ensure_ascii=False, indent=2)
        config_file.write("\n")
        config_file.flush()
        os.fsync(config_file.fileno())
    temp_path.replace(LOCAL_RULE_CONFIG_PATH)
