import cv2
import numpy as np


def find_game_field(image: np.array) -> np.array:
    image = image[image.shape[0] // 5 :, : image.shape[1] // 4 * 3]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([90, 0, 0])
    upper = np.array([150, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    for n, line in enumerate(mask):
        last_pixel = line[-1]
        if last_pixel:
            h = n
            for nl, p in enumerate(line[::-1]):
                if not p:
                    w = nl
                    return image[h:, :-w]
