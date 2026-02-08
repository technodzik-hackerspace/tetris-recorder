from pathlib import Path

import cv2
import numpy as np


def _is_capture_device(path: Path) -> bool:
    """Check if path is a capture device (e.g., /dev/video0)."""
    return str(path).startswith("/dev/")


def frame_generator(path: Path, loop: bool = False):
    """Generate frames from a 1920x1080 video file, device, or directory of images.

    Args:
        path: Path to video file, video device (e.g., /dev/video0), or directory of PNG images
        loop: If True, loop the video indefinitely (useful for debug mode)

    Note:
        For video files (not capture devices), a black frame is yielded at the end
        to trigger proper state transitions in the game loop.
    """
    if path.is_dir():
        for i in sorted(path.iterdir()):
            if i.suffix == ".png":
                yield cv2.imread(str(i))
        # Add black frame at end of directory
        yield np.zeros((1080, 1920, 3), dtype=np.uint8)
    else:
        is_device = _is_capture_device(path)
        # Handle video files and video devices (e.g., /dev/video0)
        while True:
            cap = cv2.VideoCapture(str(path))
            if is_device:
                # Use MJPEG format for capture devices (much faster than YUYV)
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                cap.set(cv2.CAP_PROP_FOURCC, fourcc)
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
                # For video files, yield a black frame to trigger state transition
                if not is_device:
                    yield np.zeros((1080, 1920, 3), dtype=np.uint8)
                break
