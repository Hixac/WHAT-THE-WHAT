import os
from pathlib import Path

from pydantic import computed_field
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


class SaluteSpeechSettings(BaseSettings):
    SALUTE_SPEECH_SCOPE: str
    SALUTE_SPEECH_AUTH_KEY: str


class MongoSettings(BaseSettings):
    MONGO_ENGINE: str

    MONGO_HOST: str
    MONGO_PORT: int

    MONGO_NAME: str

    @computed_field
    @property
    def mongo_url(self) -> str:
        return str(Url.build(
            scheme=self.MONGO_ENGINE,
            host=self.MONGO_HOST,
            port=self.MONGO_PORT
        ))


class Settings(
    MongoSettings,
    SaluteSpeechSettings
):
    APP_NAME: str = "kuhnya_kadri"

    VK_USER_TOKEN: str
    VK_GROUP_ID: int

    POST_DELAY_IN_SECONDS: int
    INITIAL_FRAME: int

    LOG_LEVEL: str

    VIDEO_FILE_PATH: Path
    FRAME_OUTPUT_PATH: Path
    CHANGED_OUTPUT_PATH: Path
    IMPACT_FONT_PATH: Path

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
