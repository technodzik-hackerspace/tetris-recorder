import logging
from pathlib import Path

import cv2

from cv_tools import strip_frame
from cv_tools.debug import save_image
from utils.dirs import full_frames_path


def frame_generator(path: Path):
    if path.absolute():
        cap = cv2.VideoCapture(str(path))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
    else:
        for i in sorted(path.iterdir()):
            if i.suffix == ".png":
                yield cv2.imread(str(i))


def frame_stripper(image_device: Path):
    log = logging.getLogger("frame_generator")
    last_error = None

    for frame_number, frame in enumerate(frame_generator(image_device)):
        save_image(full_frames_path / f"{frame_number:06d}.png", frame)

        try:
            f = strip_frame(frame)
        except Exception as e:
            err_text = str(e)
            if last_error != err_text:
                log.exception(f"Frame {frame_number} failed: {err_text}")
                last_error = err_text
            continue

        last_error = None
        yield frame_number, f
