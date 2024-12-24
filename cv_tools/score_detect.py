import cv2
import numpy as np


def get_countours(image: np.array):
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda d: d[0][0][0])

    numbers = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        numbers.append(image[y - 1 : y + h + 1, x - 1 : x + w + 1])

    return numbers
