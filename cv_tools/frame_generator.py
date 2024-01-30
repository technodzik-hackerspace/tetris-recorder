from pathlib import Path

import cv2


def frame_generator(path: Path):
    if path.absolute():
        cap = cv2.VideoCapture(str(path))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
    else:
        for i in sorted(path.iterdir()):
            if i.suffix == ".png":
                yield cv2.imread(str(i))
