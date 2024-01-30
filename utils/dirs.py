from pathlib import Path

_root = Path(__file__).parent.parent
frames_path = _root / "frames"
regions_path = _root / "regions"
videos_path = _root / "videos"


def clean_dir(path: Path):
    for i in path.iterdir():
        if i.suffix == ".png":
            i.unlink()
