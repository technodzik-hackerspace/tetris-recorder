import cv2
import numpy as np


def get_countours(image: np.array):
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda d: d[0][0][0])

    numbers = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # Filter out non-digit contours:
        # - Too small (noise) - min 25x20 for fullhd digits
        # - Too flat (horizontal lines)
        # - Ensure reasonable aspect ratio for digits
        if h < 25 or w < 20:
            continue
        if h < w * 0.7:  # Too flat (horizontal)
            continue
        aspect = w / h
        if aspect < 0.6 or aspect > 1.5:  # Digits have aspect ratio ~0.8-1.2
            continue
        numbers.append(image[y - 1 : y + h + 1, x - 1 : x + w + 1])

    return numbers
