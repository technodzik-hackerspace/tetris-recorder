import cv2
import numpy as np


def split_img(img: np.array) -> tuple[np.array, np.array]:
    p1 = img[0 : img.shape[0], 0 : img.shape[1] // 2]
    p2 = img[0 : img.shape[0], img.shape[1] // 2 : img.shape[1]]
    p2 = cv2.flip(p2, 1)
    return p1, p2
