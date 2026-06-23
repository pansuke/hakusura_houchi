from fastapi import APIRouter

from lane_relay.api.schemas import MasterDataStatus

router = APIRouter(prefix="/master-data", tags=["master-data"])


@router.get("/status", response_model=MasterDataStatus)
def get_master_data_status() -> MasterDataStatus:
    return MasterDataStatus(
        source_dir="data/source",
        generated_file="data/generated/game-data.json",
    )
