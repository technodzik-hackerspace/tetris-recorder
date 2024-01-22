import asyncio
import subprocess
from asyncio import sleep
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from aiogram import Bot, types
from aiogram.types import InputFile

from config import settings

frames_path = Path("frames")
regions_path = Path("regions")
videos_path = Path("videos")


def generate_unique_filename():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"gameplay_{timestamp}.mp4"


async def send_video_to_telegram(bot_token: str, chat_id, video_path: str):
    bot = Bot(token=bot_token)
    await bot.send_chat_action(chat_id=chat_id, action=types.ChatActions.UPLOAD_VIDEO)
    with open(video_path, "rb") as video_file:
        await bot.send_video(chat_id=chat_id, video=InputFile(video_file))


def ffmpeg_cmd(args: list[str]):
    return subprocess.Popen(
        " ".join(["ffmpeg"] + args),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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


def get_score_images(image: np.array, reverse=False):
    score_img = image[: image.shape[0] // 4, image.shape[1] // 4 : -image.shape[1] // 6]

    im_bw = cv2.cvtColor(score_img, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)
    # cv2.imwrite(str(regions_path / "thresh_original.png"), thresh_original)

    # trim zeros
    bottom_line = thresh_original[-1].flatten()
    l = np.unique((bottom_line == 0).cumsum()[bottom_line > 0])
    r = np.unique((bottom_line[::-1] == 0).cumsum()[bottom_line[::-1] > 0])
    trim_1 = thresh_original[:, l[0] : thresh_original.shape[1] - r[0]]
    # cv2.imwrite(str(regions_path / "trim_1.png"), trim_1)

    # trim white borders
    bottom_line = trim_1[-1].flatten()
    l = np.unique((bottom_line == 255).cumsum()[bottom_line == 0])
    r = np.unique((bottom_line[::-1] == 255).cumsum()[bottom_line[::-1] == 0])
    trim_2 = trim_1[:, l[0] : trim_1.shape[1] - r[0]]
    # cv2.imwrite(str(regions_path / "trim_2.png"), trim_2)

    bottom_line = trim_2[-1].flatten()
    if 255 in bottom_line:
        l = np.unique((bottom_line == 0).cumsum()[bottom_line > 0])
        trim_1 = trim_2[:, l[0] :]
        # cv2.imwrite(str(regions_path/"trim_1.png"), trim_1)

        bottom_line = trim_1[-1].flatten()
        l = np.unique((bottom_line == 255).cumsum()[bottom_line == 0])
        trim_2 = trim_1[:, l[0] :]
        # cv2.imwrite(str(regions_path / "trim_2.png"), trim_2)

    if reverse:
        trim_2 = cv2.flip(trim_2, 1)

    contours, _ = cv2.findContours(trim_2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda d: d[0][0][0])

    numbers = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        numbers.append(trim_2[y : y + h, x : x + w])

    # for n, i in enumerate(numbers):
    #     cv2.imwrite(f"{n}.png", i)

    return numbers


def frame_generator(debug=False):
    if not debug:
        cap = cv2.VideoCapture(settings.image_device)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
    else:
        for i in sorted(Path("test_frames").iterdir()):
            if i.suffix == ".png":
                yield cv2.imread(str(i.absolute()))


def split_img(img: np.array) -> tuple[np.array, np.array]:
    p1 = img[0 : img.shape[0], 0 : img.shape[1] // 2]
    p2 = img[0 : img.shape[0], img.shape[1] // 2 : img.shape[1]]
    p2 = cv2.flip(p2, 1)
    return p1, p2


def get_score(img: np.array, roi_ref: dict[int, np.array], reverse=False) -> int:
    ff1 = img[0 : img.shape[0] // 5, :]
    imgs = get_score_images(ff1, reverse)

    digits = [detect_digit(i, roi_ref) for i in imgs]

    val = 0
    for i in digits:
        val = val * 10 + i

    return val


def clean_dir(path: Path):
    for i in path.iterdir():
        if i.suffix == ".png":
            i.unlink()


def create_video(filename: Path):
    proc = ffmpeg_cmd(
        [
            "-framerate 2",
            "-pattern_type glob",
            "-i 'frames/*.png'",
            "-c:v libx264",
            "-pix_fmt yuv420p",
            str(filename),
        ]
    )
    proc.communicate()


def find_asd(image: np.array, reversed=False):
    # result = image.copy()
    image = image[image.shape[0] // 4 :, :]
    cv2.imwrite(str(regions_path / "red.png"), image)
    lower = np.array([0, 0, 150])
    upper = np.array([100, 100, 255])
    mask = cv2.inRange(image, lower, upper)
    # result = cv2.bitwise_and(result, result, mask=mask)
    cv2.imwrite(str(regions_path / "red1.png"), mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False

    cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
    x, y, w, h = cv2.boundingRect(cnt)
    img = image[y : y + h, x : x + w]
    # cv2.imwrite(str(regions_path / "red1.png"), img)

    im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh_original = cv2.threshold(im_bw, 10, 255, cv2.THRESH_BINARY)
    cv2.imwrite(str(regions_path / "red2.png"), thresh_original)
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


async def main(recording=False, debug=False):
    roi_ref = get_refs()

    while True:
        game_end = True

        clean_dir(frames_path)
        clean_dir(regions_path)

        for frame_number, frame in enumerate(frame_generator(debug=debug)):
            _frame = strip_frame(frame)
            cv2.imwrite(
                str(frames_path / f"frame_{frame_number:04d}.png"),
                cv2.resize(_frame, (400, 400)),
            )

            f1, f2 = split_img(_frame)

            if game_end:
                score1 = get_score(f1, roi_ref=roi_ref)
                score2 = get_score(f2, roi_ref=roi_ref, reverse=True)
                if score1 == 0 and score2 == 0:
                    game_end = False
                else:
                    continue

            if debug:
                cv2.imwrite(str(regions_path / f"p1_{frame_number:04d}.png"), f1)
                cv2.imwrite(str(regions_path / f"p2_{frame_number:04d}.png"), f2)

            p1_end = find_asd(f1)
            p2_end = find_asd(f2, reversed=True)

            if p1_end and p2_end and game_end is False:
                # score1 = get_score(f1, roi_ref=roi_ref)
                # score2 = get_score(f2, roi_ref=roi_ref, reverse=True)

                if recording:
                    create_video(videos_path / generate_unique_filename())
                clean_dir(frames_path)
                clean_dir(regions_path)
                game_end = True
                return
            # await sleep(1)

        # Pause for a moment before starting a new recording
        await sleep(1)


def detect_digit(roi: np.array, roi_ref: dict[int, np.array]) -> int:
    scores = {}
    for digit, digit_roi in roi_ref.items():
        # apply correlation-based template matching, take the
        # score, and update the scores list
        result = cv2.matchTemplate(roi, digit_roi, cv2.TM_CCOEFF)
        (_, score, _, _) = cv2.minMaxLoc(result)
        scores[digit] = score
    val = max(scores, key=scores.get)
    return val


def get_refs():
    results = {}

    for i in Path("digits").iterdir():
        val = int(i.stem)
        img = cv2.imread(str(i))

        im_bw = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, thresh_original = cv2.threshold(im_bw, 50, 255, cv2.THRESH_BINARY)
        results[val] = thresh_original

    return results


if __name__ == "__main__":
    asyncio.run(main(debug=True, recording=True))
