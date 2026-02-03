import os

import structlog
import cv2
import numpy as np

from cv2.typing import MatLike

from src.core.config import settings


LOGGER = structlog.get_logger(__name__)


def image_difference(m1: MatLike, m2: MatLike) -> float:
    res = cv2.absdiff(m1, m2)

    similarity_percentage = 100 - (np.count_nonzero(res) * 100) / res.size
    LOGGER.info("Image diffrence", diff=similarity_percentage)

    return similarity_percentage


def get_frame_count() -> int:
    cap = cv2.VideoCapture(settings.VIDEO_FILE_PATH)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return length


def get_frame_by_index(frame_index: int) -> MatLike:
    cap = cv2.VideoCapture(settings.VIDEO_FILE_PATH)

    if not cap.isOpened():
        LOGGER.error(f"Could not open video file", video_file=settings.VIDEO_FILE_PATH)
        raise Exception("Could not open video file")

    _ = cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()

    if ret:
        LOGGER.info(
            "Frame extracted",
            frame_index=frame_index,
        )
    else:
        LOGGER.error(
            "Could not read frame",
            frame_index=frame_index,
            total_frames=get_frame_count(),
            video_file=settings.VIDEO_FILE_PATH
        )
        raise Exception("Could not read frame")

    cap.release()

    return frame


def write_frame(frame_mat: MatLike) -> None:
    LOGGER.info("Frame saved as file")

    _ = cv2.imwrite(settings.FRAME_OUTPUT_PATH, frame_mat)


def download_frame() -> MatLike:
    mat = cv2.imread(settings.FRAME_OUTPUT_PATH)
    if mat is None:
        LOGGER.error(
            "Wrong path or file doesn't exist",
            filepath=settings.FRAME_OUTPUT_PATH
        )
        raise Exception("Wrong path or file doesn't exist")

    return mat


def file_of_frame_exists() -> bool:
    return os.path.exists(settings.FRAME_OUTPUT_PATH)


Picture = MatLike
