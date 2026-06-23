from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lane_relay.api.routers.battles import router as battles_router
from lane_relay.api.routers.health import router as health_router
from lane_relay.api.routers.master_data import router as master_data_router
from lane_relay.api.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Lane Relay API",
        version="0.1.0",
        summary="Developer API for the idle hack-and-slash deck-building prototype.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(battles_router, prefix="/api/v1")
    app.include_router(master_data_router, prefix="/api/v1")
    return app


app = create_app()
