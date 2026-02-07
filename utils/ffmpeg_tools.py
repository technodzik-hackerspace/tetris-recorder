import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


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
            "-y",  # Overwrite output file if exists
            str(filename),
        ]
    )
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        logger.error(f"ffmpeg failed with return code {proc.returncode}")
        logger.error(f"ffmpeg stderr: {stderr.decode()}")
        logger.error(f"ffmpeg stdout: {stdout.decode()}")
        raise RuntimeError(f"ffmpeg failed: {stderr.decode()}")
