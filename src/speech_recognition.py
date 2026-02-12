import uuid
from time import time
from requests import request
from urllib.parse import urlencode

import structlog

from src.core.config import settings


LOGGER = structlog.get_logger(__file__)


class TokenManager:
    def __init__(self) -> None:
        self.token: str | None = None
        self.token_expire: int | None = None

    def get_token(self) -> str:
        if self.token is None or self.token_expire is None \
                or self.token_expire > time():
            self.token, self.token_expire = self._refresh_token()

        LOGGER.info("Token gathered successfully")
        return self.token

    def _refresh_token(self) -> tuple[str, int]:
        scope = settings.SALUTE_SPEECH_SCOPE
        auth_key = settings.SALUTE_SPEECH_AUTH_KEY

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {auth_key}'
        }

        data = urlencode({
            "scope": scope
        })

        response = request("POST", url, verify=False, headers=headers, data=data)
        if response.status_code != 200:
            LOGGER.error("Request to sberbank went wrong!", url=url, headers=headers, data=data)
            raise Exception("Request to sberbank went wrong!")

        json = response.json()
        return json["access_token"], int(json["expires_at"])


class SpeechSalute:
    token_manager = TokenManager()

    @classmethod
    def get_speech(cls, *, ogg_data: bytes) -> list[str]:
        token = cls.token_manager.get_token()

        url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"

        params = {
            "enable_profanity_filter": False
        }
        headers = {
            "Content-Type": "audio/ogg;codecs=opus",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = request(
            "POST", url, verify=False, params=params, headers=headers, data=ogg_data
        )
        if response.status_code != 200:
            LOGGER.error("Salute speech went wrong!", url=url, params=params, headers=headers, data=ogg_data)
            raise Exception("Salute speech went wrong!")

        return response.json()["result"]
