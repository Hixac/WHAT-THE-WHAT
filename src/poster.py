from datetime import datetime
from time import sleep

import structlog

from src.core.config import settings
from src.app_data import app_data
from src.vk_api_wrapper import upload_photo, wall_post
from src.video_frame import (
    get_frame_count,
    get_frame_by_index,
    write_frame,
    download_frame,
    image_difference,
    file_of_frame_exists,
    Picture
)


LOGGER = structlog.get_logger(__name__)


def do_sleep():
    date: datetime = app_data.get()["datetime"]
    time_diff = (datetime.now() - date).total_seconds()
    delay = settings.POST_DELAY_IN_SECONDS - time_diff

    if delay < 0:
        LOGGER.info("Skip", seconds=delay)
    else:
        LOGGER.info("Sleeping", seconds=delay)
        sleep(delay)


def do_post():
    attachment = upload_photo(str(settings.FRAME_OUTPUT_PATH))[0]
    index: int = app_data.get()["frame_index"]
    total_indices = get_frame_count()

    wall_post(
        msg=f"{index} из {total_indices} кадров",
        attachments=attachment
    )


def posting():
    while True:
        frame_index: int = app_data.get()["frame_index"]
        frame_mat: Picture = get_frame_by_index(frame_index)

        if file_of_frame_exists():
            image_diff = image_difference(frame_mat, download_frame())
            if image_diff > 5:  # IF IMAGES ARE MOSTLY LIKE THE SAME WE SKIP
                LOGGER.info("Images are same")
                app_data.increment_frame_index()
                continue

        write_frame(frame_mat)
        try:
            do_post()
        except:
            LOGGER.exception("Stupid ass vk")
        app_data.increment_frame_index()

        do_sleep()
