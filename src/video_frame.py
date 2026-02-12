import os
from typing import Self
from types import TracebackType
from pathlib import Path
from functools import cached_property

import structlog
import cv2
import numpy as np
import ffmpeg

from cv2.typing import MatLike

from src.speech_recognition import SpeechSalute
from src.core.config import settings


LOGGER = structlog.get_logger(__name__)


class Video:
    Picture = MatLike

    @cached_property
    def frame_count(self) -> int:
        length = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        return length

    @cached_property
    def fps(self) -> int:
        fps = int(self.video_capture.get(cv2.CAP_PROP_FPS))
        return fps

    def __init__(self, path: Path) -> None:
        self.video_capture = cv2.VideoCapture(path)
        if not self.video_capture.isOpened():
            LOGGER.error(f"Could not open video file", video_file=settings.VIDEO_FILE_PATH)
            raise Exception("Could not open video file")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.video_capture.release()

    def get_frame_by_index(self, index: int) -> Picture:
        _ = self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.video_capture.read()

        if ret:
            LOGGER.info(
                "Frame extracted",
                frame_index=index,
            )
        else:
            LOGGER.error(
                "Could not read frame",
                frame_index=index,
                total_frames=self.frame_count,
                video_file=settings.VIDEO_FILE_PATH
            )
            raise Exception("Could not read frame")

        return frame

    def save_frame_into_file(self, *, path: Path, frame: MatLike) -> None:
        LOGGER.info("Frame saved as file")

        _ = cv2.imwrite(path, frame)

    def read_frame(self, *, path: Path) -> Picture:
        mat = cv2.imread(path)
        if mat is None:
            LOGGER.error(
                "Wrong path or file doesn't exist",
                filepath=settings.FRAME_OUTPUT_PATH
            )
            raise Exception("Wrong path or file doesn't exist")

        return mat


def image_difference(m1: MatLike, m2: MatLike) -> float:
    res = cv2.absdiff(m1, m2)

    similarity_percentage = 100 - (np.count_nonzero(res) * 100) / res.size
    LOGGER.info("Image diffrence", diff=similarity_percentage)

    return similarity_percentage


def does_file_exist(p: Path) -> bool:
    return os.path.exists(p)


def get_speech_from_video(*, prev_frame: int, newest_frame: int, fps: int) -> str | None:
    try: 
        out, _ = (
            ffmpeg  # pyright: ignore
            .input(settings.VIDEO_FILE_PATH)
            .audio
            .filter('atrim', start=(prev_frame / fps), duration=(newest_frame - prev_frame)/fps)
            .output('pipe:', format='ogg', acodec='libopus')
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
    except ffmpeg.Error:
        LOGGER.exception("Ffmpeg went wrong")
    else:
        return "".join(SpeechSalute.get_speech(ogg_data=out))  # pyright: ignore
