import cv2
import numpy as np


def strip_frame(frame: np.ndarray):
    im_bw = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 3, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(
        thresh_original, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    lst_contours = []
    for cnt in contours:
        ctr = cv2.boundingRect(cnt)
        lst_contours.append(ctr)
    x, y, w, h = sorted(lst_contours, key=lambda coef: coef[3])[-2]

    _frame = frame[y : y + h, x : x + w]

    return _frame
