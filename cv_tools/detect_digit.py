from pathlib import Path

import cv2
import numpy as np

RoiRef = dict[str, np.array]


def detect_digit(roi: np.array, roi_ref: RoiRef) -> str:
    # Skip empty ROIs
    if roi is None or roi.size == 0 or roi.shape[0] == 0 or roi.shape[1] == 0:
        return ""

    scores = {}
    # Get expected size from first template
    template_h, template_w = next(iter(roi_ref.values())).shape[:2]

    # Always resize input ROI to match template size
    if roi.shape[0] != template_h or roi.shape[1] != template_w:
        roi = cv2.resize(roi, (template_w, template_h))

    for digit, digit_roi in roi_ref.items():
        # apply correlation-based template matching, take the
        # score, and update the scores list
        result = cv2.matchTemplate(roi, digit_roi, cv2.TM_CCOEFF_NORMED)
        (_, score, _, _) = cv2.minMaxLoc(result)
        scores[digit] = score
    val = max(scores, key=scores.get)
    return val


def get_refs() -> RoiRef:
    results = {}

    for i in (Path(__file__).parent.parent / "digits_fullhd").iterdir():
        val = i.stem
        img = cv2.imread(str(i))

        im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)
        results[val] = thresh_original

    return results
