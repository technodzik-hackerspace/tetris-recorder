import cv2
import numpy as np


def strip_frame(frame: np.ndarray) -> np.ndarray:
    """Extract game area from 1920x1080 frame.

    Returns the cropped game area with even dimensions for video encoding.
    Raises Exception if frame is invalid (black screen, wrong dimensions).
    """
    im_bw = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 5, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(
        thresh_original, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    lst_contours = []
    for cnt in contours:
        ctr = cv2.boundingRect(cnt)
        lst_contours.append(ctr)
    if not lst_contours:
        raise Exception("No contours")
    x, y, w, h = sorted(lst_contours, key=lambda coef: coef[3])[-2]

    _frame = frame[y + 1 : y + h - 1, x + 1 : x + w - 1]

    # Validate dimensions for 1080p input (game area ~900-1250px)
    h, w = _frame.shape[:2]
    if not (1250 > h > 900):
        raise Exception(f"Wrong height: {h}")
    if not (1250 > w > 900):
        raise Exception(f"Wrong width: {w}")

    # Ensure even dimensions for video encoding
    if _frame.shape[0] % 2:
        _frame = _frame[:-1, :]
    if _frame.shape[1] % 2:
        _frame = _frame[:, :-1]

    return _frame
