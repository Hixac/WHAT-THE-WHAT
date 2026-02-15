import structlog

from src.core import logger  # init logger # pyright: ignore
from src.core.config import settings
from src.poster import Poster


LOGGER = structlog.get_logger(__name__)


def main():
    LOGGER.info("APPLICATION STARTED")
    p = Poster(
        video_path=settings.VIDEO_FILE_PATH,
        output_path=settings.FRAME_OUTPUT_PATH,
        second_output_path=settings.CHANGED_OUTPUT_PATH,
        font_path=settings.IMPACT_FONT_PATH,
        delay_in_seconds=settings.POST_DELAY_IN_SECONDS
    )
    p.posting()


if __name__ == "__main__":
    main()
