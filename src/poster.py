from datetime import datetime
from time import sleep
from pathlib import Path

import structlog

from src.core.config import settings
from src.app_data import app_data
from src.vk_api_wrapper import upload_photo, wall_post
from src.video_frame import (
    image_difference,
    Video,
    does_file_exist,
    get_speech_from_video
)
from src.image import ImageTextComposer


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


def do_post(frame_count: int, *, path: Path):
    attachment = upload_photo(str(path))[0]
    index: int = app_data.get()["frame_index"]

    wall_post(
        msg=f"{index} из {frame_count} кадров",
        attachments=attachment
    )


def posting():
    while True:
        frame_index: int = app_data.get()["frame_index"]
        path: Path = settings.FRAME_OUTPUT_PATH

        frame_count: int
        fps: int
        with Video(settings.VIDEO_FILE_PATH) as video:
            frame_count = video.frame_count
            fps = video.fps

            frame = video.get_frame_by_index(frame_index)

            if does_file_exist(settings.FRAME_OUTPUT_PATH):
                newest_frame = video.read_frame(path=settings.FRAME_OUTPUT_PATH)
                image_diff = image_difference(frame, newest_frame)
                if image_diff > 5:  # IF IMAGES ARE MOSTLY LIKE THE SAME WE SKIP
                    LOGGER.info("Images are same")
                    app_data.increment_frame_index()
                    continue

            video.save_frame_into_file(path=settings.FRAME_OUTPUT_PATH, frame=frame)


        text = get_speech_from_video(prev_frame=frame_index-500, newest_frame=frame_index, fps=fps)
        if text is not None:
            composer = ImageTextComposer(font_path=settings.IMPACT_FONT_PATH)
            composer.compose(text=text, input_path=settings.FRAME_OUTPUT_PATH, output_path=settings.CHANGED_OUTPUT_PATH)
            path = settings.CHANGED_OUTPUT_PATH


        try:
            do_post(frame_count, path=path)
        except:
            LOGGER.exception("Stupid ass vk")
            continue
        app_data.increment_frame_index()

        do_sleep()
