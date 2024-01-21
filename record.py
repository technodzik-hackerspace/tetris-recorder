# sudo apt install v4l-utils ffmpeg python3-pip
# python3 -m venv venv
# source venv/bin/activate
# pip install aiogram opencv-python

import cv2
import subprocess
import numpy as np
import time
import sys
import asyncio
from aiogram import Bot, types
from aiogram.types import InputFile

def generate_unique_filename():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"gameplay_{timestamp}.mp4"

async def send_video_to_telegram(bot_token, chat_id, video_path):
    bot = Bot(token=bot_token)
    await bot.send_chat_action(chat_id=chat_id, action=types.ChatActions.UPLOAD_VIDEO)
    with open(video_path, "rb") as video_file:
        await bot.send_video(chat_id=chat_id, video=InputFile(video_file))

# Video capture settings
video_device = "/dev/video2"
video_resolution = (1280, 720)

# Screenshots capture settings
image_device = "/dev/video0"

# 122 x 33
start_reference_image = cv2.imread("game_start.png")
start_xy = (122, 33)

# 159 x 204, 415 x 204
end_reference_image = cv2.imread("game_over.png")
end_p1_xy = (159, 204)
end_p2_xy = (415, 204)

video_capture_cmd = f"ffmpeg -f v4l2 -input_format mjpeg -video_size {video_resolution[0]}x{video_resolution[1]} -i {video_device} -hide_banner -loglevel error"

# Initialize recording status
recording = False

debug = False

while True:
    # Generate a unique filename for each game play
    output_file = generate_unique_filename()

    # Video capture
    cap = cv2.VideoCapture(image_device)

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        start_roi = frame[
            start_xy[1]:start_xy[1]+start_reference_image.shape[0],
            start_xy[0]:start_xy[0]+start_reference_image.shape[1]
        ]

        p1_end_roi = frame[
            end_p1_xy[1]:end_p1_xy[1]+end_reference_image.shape[0],
            end_p1_xy[0]:end_p1_xy[0]+end_reference_image.shape[1]
        ]

        p2_end_roi = frame[
            end_p2_xy[1]:end_p2_xy[1]+end_reference_image.shape[0],
            end_p2_xy[0]:end_p2_xy[0]+end_reference_image.shape[1]
        ]

        if (debug):
            frame_filename = f"frames/frame_{frame_count}.png"        
            start_region_filename = f"regions/reg_start_{frame_count}.png"
            p1_end_region_filename = f"regions/reg_end_p1_{frame_count}.png"
            p2_end_region_filename = f"regions/reg_end_p2_{frame_count}.png"

            cv2.imwrite(frame_filename, frame)
            cv2.imwrite(start_region_filename, start_roi)
            cv2.imwrite(p1_end_region_filename, p1_end_roi)
            cv2.imwrite(p2_end_region_filename, p2_end_roi)

        ssd_start = np.sum((start_roi - start_reference_image) ** 2)

        p1_end = np.sum((p1_end_roi - end_reference_image) ** 2)
        p2_end = np.sum((p2_end_roi - end_reference_image) ** 2)

        print(str(frame_count) + ' (s:' + str(ssd_start) + ' p1:' + str(p1_end) + ' p2:' + str(p2_end) + ')')

        if ssd_start < 10000:
            print('Game start position detected')
            # Detected start trigger, initiate recording if not already recording
            if not recording:
                print('=== RECORDING STARTED === ' + output_file)
                start_recording_cmd = f"{video_capture_cmd} {output_file}"
                subprocess.Popen(start_recording_cmd, shell=True)
                recording = True
        elif p1_end < 1000:
            print('Game end position detected')
            if recording:
                print('=== STOPPING RECORDING === ' + output_file)
                subprocess.Popen("sleep 3 && pkill ffmpeg", shell=True)
                recording = False

                # Send the video to the Telegram channel
                bot_token = 'YOUR_BOT_TOKEN'
                chat_id = 'YOUR_CHANNEL_ID'
                send_video_to_telegram(bot_token, chat_id, output_file)
                break
        time.sleep(1)
        frame_count += 1

    # Pause for a moment before starting a new recording
    time.sleep(1)
