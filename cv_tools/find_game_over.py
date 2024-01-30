from pathlib import Path

import cv2
import numpy as np

from .find_game_field import find_game_field

regions_path = Path("regions")


def find_game_over(image: np.array, reversed=False) -> bool:
    image = find_game_field(image)
    image = image[image.shape[0]//3:image.shape[0]//3*2, :]

    cv2.imwrite(str(regions_path / "game_over1.png"), image)
    lower = np.array([0, 0, 150])
    upper = np.array([100, 100, 255])
    mask = cv2.inRange(image, lower, upper)
    # result = cv2.bitwise_and(result, result, mask=mask)
    # cv2.imwrite(str(regions_path / "red1.png"), mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False

    cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
    x, y, w, h = cv2.boundingRect(cnt)
    img = image[y : y + h, x : x + w]
    cv2.imwrite(str(regions_path / "game_over2.png"), img)

    im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 10, 255, cv2.THRESH_BINARY)
    cv2.imwrite(str(regions_path / "game_over3.png"), thresh_original)

    contours, _ = cv2.findContours(
        thresh_original, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    if len(contours) < 3:
        return False

    return True

    # cnt = sorted(contours, key=cv2.contourArea, reverse=True)[3]
    # x, y, w, h = cv2.boundingRect(cnt)
    # img = img[y : y + h, x : x + w]

    # if reversed:
    #     img = cv2.flip(img, 1)
    # cv2.imwrite(str(regions_path / "red3.png"), img)
    #
    # digit_roi = cv2.imread("game_over2.png")
    # result = cv2.matchTemplate(img, digit_roi, cv2.TM_CCOEFF)
    # (_, score, _, _) = cv2.minMaxLoc(result)

    # return True
