import cv2
import numpy as np


def have_next(ff1: np.array):
    image = ff1[: ff1.shape[0] // 5, : ff1.shape[1] // 3]
    # cv2.imwrite(str(regions_path / "red.png"), image)
    lower = np.array([0, 0, 150])
    upper = np.array([100, 100, 255])
    mask = cv2.inRange(image, lower, upper)
    # cv2.imwrite(str(regions_path / "red1.png"), mask)

    return mask.sum() > 10000
