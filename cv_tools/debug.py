from pathlib import Path

import cv2


def save_image(path: Path | str, image):
    cv2.imwrite(str(path), image)
