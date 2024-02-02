from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .detect_digit import detect_digit
from .have_next import have_next

regions_path = Path("regions")

def get_score_images(image: np.array, reverse=False):
    score_img = image[: image.shape[0] // 4, image.shape[1] // 4 : -image.shape[1] // 6]

    im_bw = cv2.cvtColor(score_img, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)
    cv2.imwrite(str(regions_path / "thresh_original.png"), thresh_original)

    # trim zeros
    bottom_line = thresh_original[-1].flatten()
    l = np.unique((bottom_line == 0).cumsum()[bottom_line > 0])
    r = np.unique((bottom_line[::-1] == 0).cumsum()[bottom_line[::-1] > 0])
    trim_1 = thresh_original[:, l[0] : thresh_original.shape[1] - r[0]]
    cv2.imwrite(str(regions_path / "trim_1.png"), trim_1)

    # trim white borders
    bottom_line = trim_1[-1].flatten()
    l = np.unique((bottom_line == 255).cumsum()[bottom_line == 0])
    r = np.unique((bottom_line[::-1] == 255).cumsum()[bottom_line[::-1] == 0])
    trim_2 = trim_1[:, l[0] : trim_1.shape[1] - r[0]]
    cv2.imwrite(str(regions_path / "trim_2.png"), trim_2)

    bottom_line = trim_2[-1].flatten()
    if 255 in bottom_line:
        l = np.unique((bottom_line == 0).cumsum()[bottom_line > 0])
        trim_1 = trim_2[:, l[0] :]
        cv2.imwrite(str(regions_path/"trim_1.png"), trim_1)

        bottom_line = trim_1[-1].flatten()
        l = np.unique((bottom_line == 255).cumsum()[bottom_line == 0])
        trim_2 = trim_1[:, l[0] :]
        cv2.imwrite(str(regions_path / "trim_2.png"), trim_2)

    if reverse:
        trim_2 = cv2.flip(trim_2, 1)

    contours, _ = cv2.findContours(trim_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda d: d[0][0][0])

    numbers = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        numbers.append(trim_2[y : y + h, x : x + w])

    # for n, i in enumerate(numbers):
    #     cv2.imwrite(f"{n}.png", i)

    return numbers


def get_score(
    img: np.array, roi_ref: dict[int, np.array], reverse=False
) -> Optional[int]:
    ff1 = img[0 : img.shape[0] // 5, :]

    _next = have_next(ff1)
    if not _next:
        return

    imgs = get_score_images(ff1, reverse)

    digits = [detect_digit(i, roi_ref) for i in imgs]

    val = 0
    for i in digits:
        val = val * 10 + i

    return val
