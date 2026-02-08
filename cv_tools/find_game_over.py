import cv2
import numpy as np

from utils.dirs import regions_path  # noqa


def find_game_over(image: np.array) -> bool:
    # Search in upper half of the screen where GAME OVER box typically appears
    image = image[: image.shape[0] // 2, :]

    # save_image(regions_path / "game_over1.png", image)
    lower = np.array([0, 0, 150])
    upper = np.array([100, 100, 255])
    mask = cv2.inRange(image, lower, upper)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False

    cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
    x, y, w, h = cv2.boundingRect(cnt)
    img = image[y : y + h, x : x + w]
    # save_image(regions_path / "game_over2.png", img)

    im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 10, 255, cv2.THRESH_BINARY)
    # save_image(regions_path / "game_over3.png", thresh_original)

    contours, _ = cv2.findContours(
        thresh_original, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    if len(contours) < 3:
        return False

    return True
