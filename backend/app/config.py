"""
Configuration loading.

Uses environment variables to keep the application twelve-factor friendly.
No business logic should be derived here—only static configuration values.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    app_name: str = Field("mcp-hackathon", description="Service identifier")
    version: str = Field("0.1.0", description="Semantic version for OpenAPI")
    environment: str = Field("development", description="Runtime environment")
    elevenlabs_api_key: str = Field("sk_4fb470c35317b89fc5e75acf9474d873e60dbd96171b5eae", description="ElevenLabs API key")
    elevenlabs_voice_id: str = Field(
        "21m00Tcm4TlvDq8ikWAM",
        description="Default ElevenLabs voice id",
    )
    elevenlabs_model_id: str = Field(
        "eleven_multilingual_v2",
        description="Default ElevenLabs TTS model id",
    )
    elevenlabs_stt_model_id: str = Field(
        "scribe_v1",
        description="Default ElevenLabs STT model id",
    )

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings loader.

    Keeping this in a function avoids global state that is hard to override
    in tests. Modify configuration through environment variables rather than
    importing and mutating Settings directly.
    """

    return Settings()
