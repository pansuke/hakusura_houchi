import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict


class ApiSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    cors_origins: list[str]


@lru_cache
def get_settings() -> ApiSettings:
    raw_origins = os.getenv(
        "LANE_RELAY_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return ApiSettings(cors_origins=origins)
