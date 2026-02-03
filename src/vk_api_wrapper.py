import structlog
from vk_api import VkApi, VkUpload

from src.core.config import settings


LOGGER = structlog.get_logger(__name__)


_session: VkApi | None = None


def _get_session() -> VkApi:
    global _session
    if _session is None:
        _session = VkApi(token=settings.VK_USER_TOKEN)
    return _session


def wall_post(*, msg: str, attachments: str) -> None:
    _get_session().method(  # pyright: ignore[reportUnknownMemberType]
        "wall.post",
        {"owner_id": settings.VK_GROUP_ID, "message": msg, "attachments": attachments}
    )


def upload_photo(direc: str) -> list[str]:
    upload = VkUpload(_get_session())
    temp = upload.photo_wall(  # pyright: ignore[reportUnknownMemberType]
        direc,
        group_id=-settings.VK_GROUP_ID
    )

    ret: list[str] = []
    for photo in temp:
        ret.append("photo" + str(photo["owner_id"]) + "_" + str(photo["id"]))

    return ret
