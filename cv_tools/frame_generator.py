from pathlib import Path

import cv2


def frame_generator(path: Path, loop: bool = False):
    """Generate frames from a 1920x1080 video file, device, or directory of images.

    Args:
        path: Path to video file, video device (e.g., /dev/video0), or directory of PNG images
        loop: If True, loop the video indefinitely (useful for debug mode)
    """
    if path.is_dir():
        for i in sorted(path.iterdir()):
            if i.suffix == ".png":
                yield cv2.imread(str(i))
    else:
        # Handle video files and video devices (e.g., /dev/video0)
        while True:
            cap = cv2.VideoCapture(str(path))
            # Set resolution to 1920x1080 for video capture devices
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame
            cap.release()
            if not loop:
                break
