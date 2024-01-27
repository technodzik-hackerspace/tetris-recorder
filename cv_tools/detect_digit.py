from pathlib import Path

import cv2
import numpy as np


def detect_digit(roi: np.array, roi_ref: dict[int, np.array]) -> int:
    scores = {}
    for digit, digit_roi in roi_ref.items():
        # apply correlation-based template matching, take the
        # score, and update the scores list
        result = cv2.matchTemplate(roi, digit_roi, cv2.TM_CCOEFF)
        (_, score, _, _) = cv2.minMaxLoc(result)
        scores[digit] = score
    val = max(scores, key=scores.get)
    return val


def get_refs() -> dict[int, np.array]:
    results = {}

    for i in Path("digits").iterdir():
        val = int(i.stem)
        img = cv2.imread(str(i))

        im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)
        results[val] = thresh_original

    return results
