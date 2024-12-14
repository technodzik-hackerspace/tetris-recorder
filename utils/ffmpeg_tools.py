import subprocess
from pathlib import Path


def ffmpeg_cmd(args: list[str]):
    return subprocess.Popen(
        " ".join(["ffmpeg"] + args),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_video(filename: Path, framerate=10):
    proc = ffmpeg_cmd(
        [
            f"-framerate {framerate}",
            "-pattern_type glob",
            "-i 'frames/frame_*.png'",
            "-c:v libx264",
            "-pix_fmt yuv420p",
            str(filename),
        ]
    )
    stdin, stdout = proc.communicate()

    # print(stdin.decode())
    # print(stdout.decode())

    assert proc.returncode == 0
