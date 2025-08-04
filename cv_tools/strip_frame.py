import cv2
import numpy as np


def strip_frame(frame: np.ndarray):
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

    # save_image("frame.png", _frame)
    hs, ws, _ = _frame.shape

    if not (450 > hs > 350):
        raise Exception(f"Wrong height: {hs}x{ws}")
    if not (450 > ws > 350):
        raise Exception(f"Wrong width: {hs}x{ws}")

    assert not hs % 2
    assert not ws % 2

    return _frame
