"""
Urban Traffic Brain — Application Configuration
=================================================
Pydantic Settings loading all env vars with validation and defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ── AI ──
    kimi_api_key: str = Field(default="", description="Kimi/Moonshot API key")
    kimi_base_url: str = Field(default="https://api.moonshot.cn/v1")
    kimi_model: str = Field(default="moonshot-v1-128k")

    # ── Traffic Data ──
    tomtom_api_key: str = Field(default="", description="TomTom API key")
    here_api_key: str = Field(default="", description="HERE Maps API key")

    # ── Weather ──
    openweathermap_api_key: str = Field(default="", description="OpenWeatherMap key")

    # ── Events ──
    ticketmaster_api_key: str = Field(default="", description="Ticketmaster key")

    # Mapping (MapLibre + OpenFreeMap - No Key Required)

    # ── Database ──
    database_url: str = Field(
        default="postgresql+asyncpg://trafficbrain:trafficbrain_secret@localhost:5432/trafficbrain"
    )
    redis_url: str = Field(default="redis://localhost:6379")

    # ── App ──
    city_name: str = Field(default="Mumbai")
    city_bbox: str = Field(
        default="18.89,72.77,19.27,72.99",
        description="south_lat,west_lng,north_lat,east_lng",
    )
    polling_interval_seconds: int = Field(default=60)
    ai_decision_interval_seconds: int = Field(default=120)
    simulation_mode: bool = Field(default=True)

    # ── Derived ──
    @property
    def city_bbox_tuple(self) -> tuple[float, float, float, float]:
        parts = [float(x.strip()) for x in self.city_bbox.split(",")]
        return (parts[0], parts[1], parts[2], parts[3])

    @property
    def city_center(self) -> tuple[float, float]:
        s, w, n, e = self.city_bbox_tuple
        return ((s + n) / 2, (w + e) / 2)

    def update_city(self, new_city: str, new_bbox: str):
        self.city_name = new_city
        self.city_bbox = new_bbox

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
