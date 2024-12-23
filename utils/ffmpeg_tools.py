import subprocess
from pathlib import Path


def ffmpeg_cmd(args: list[str]):
    return subprocess.Popen(
        " ".join(["ffmpeg"] + args),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_video(
    filename: Path, frames_path: Path = Path("frames/*.png"), framerate=10
):
    proc = ffmpeg_cmd(
        [
            f"-framerate {framerate}",
            "-pattern_type glob",
            f"-i '{frames_path}'",
            "-c:v libx264",
            "-pix_fmt yuv420p",
            str(filename),
        ]
    )
    stdin, stdout = proc.communicate()

    # print(stdin.decode())
    # print(stdout.decode())

    assert proc.returncode == 0
