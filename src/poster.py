from datetime import datetime
from time import sleep
from pathlib import Path

import structlog

from src.core.exceptions import RecognitionError, VkConnectionError
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


class Poster:
    @property
    def frame_index(self):
        return app_data.get()["frame_index"]

    def __init__(
        self,
        *,
        video_path: Path,
        output_path: Path,
        second_output_path: Path,
        font_path: Path,
        delay_in_seconds: int
    ) -> None:
        self.video = Video(video_path)

        self.output_path = output_path
        self.second_output_path = second_output_path
        self.font_path = font_path
        self.delay_in_seconds = delay_in_seconds

        self.minimal_image_difference = 5  # in %
        self.frame_count: int = self.video.frame_count
        self.fps: int = self.video.fps

    def _sleep(self) -> None:
        date: datetime = app_data.get()["datetime"]
        time_diff = (datetime.now() - date).total_seconds()
        delay = self.delay_in_seconds - time_diff

        if delay < 0:
            LOGGER.info("Skip", seconds=delay)
        else:
            LOGGER.info("Sleeping", seconds=delay)
            sleep(delay)

    def _post(self, *, path: Path) -> None:
        attachment = upload_photo(str(path))[0]
        index: int = self.frame_index

        wall_post(
            msg=f"{index} из {self.frame_count} кадров",
            attachments=attachment
        )

    def _speeched_post(self) -> None:
        text = get_speech_from_video(
            prev_frame=self.frame_index-500, 
            newest_frame=self.frame_index,
            fps=self.fps
        )
        if text is not None:
            composer = ImageTextComposer(font_path=self.font_path)
            composer.compose(text=text, input_path=self.output_path, output_path=self.second_output_path)

    def _push_cached(self, *, path: Path) -> None:
        LOGGER.info("Pushing cached post")
        while True:
            try:
                self._post(path=path)
            except:
                sleep(60)  # minute sleeping and trying again
            else:
                LOGGER.info("Successfully pushed")
                return

    def posting(self):
        while True:
            path: Path = self.output_path

            frame = self.video.get_frame_by_index(self.frame_index)

            if does_file_exist(self.output_path):
                newest_frame = self.video.read_frame(path=self.output_path)
                image_diff = image_difference(frame, newest_frame)
                if image_diff > self.minimal_image_difference:  # IF IMAGES ARE MOSTLY LIKE THE SAME WE SKIP
                    LOGGER.info("Images are same")
                    app_data.increment_frame_index()
                    continue

            self.video.save_frame_into_file(path=self.output_path, frame=frame)


            try:
                self._speeched_post()
            except RecognitionError:
                self.minimal_image_difference = 20
                LOGGER.info("All tokens left I suppose so we post without text")
            else:
                self.minimal_image_difference = 5
                path = self.second_output_path


            try:
                self._post(path=path)
            except VkConnectionError:
                self._push_cached(path=path)
            finally:
                app_data.increment_frame_index()


            self._sleep()
