from datetime import datetime, UTC
from pathlib import Path

_root = Path.cwd()
full_frames_path = _root / "full_frames"
frames_path = _root / "frames"
regions_path = _root / "regions"
videos_path = _root / "videos"
games_path = _root / "games"
frames_not_tetris_path = _root / "frames_not_tetris"


def clean_dir(path: Path):
    if not path.exists():
        return
    for i in path.iterdir():
        if i.suffix == ".png":
            i.unlink()


def create_game_folder() -> Path:
    """Create a timestamped folder for a new game.

    Returns:
        Path to the new game folder (e.g., games/game_2024_01_15_14_30_45)
    """
    games_path.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y_%m_%d_%H_%M_%S")
    game_folder = games_path / f"game_{timestamp}"
    game_folder.mkdir(exist_ok=True)
    return game_folder


def cleanup_old_games(keep_count: int = 5) -> list[Path]:
    """Remove old game folders, keeping only the most recent ones.

    Args:
        keep_count: Number of recent game folders to keep

    Returns:
        List of removed folder paths
    """
    if not games_path.exists():
        return []

    # Get all game folders sorted by name (timestamp ensures chronological order)
    game_folders = sorted(
        [f for f in games_path.iterdir() if f.is_dir() and f.name.startswith("game_")],
        key=lambda x: x.name,
    )

    # Remove oldest folders if we have more than keep_count
    removed = []
    while len(game_folders) > keep_count:
        folder = game_folders.pop(0)
        _remove_folder(folder)
        removed.append(folder)

    return removed


def _remove_folder(folder: Path):
    """Remove a folder and all its contents."""
    if not folder.exists():
        return
    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            _remove_folder(item)
    folder.rmdir()


def cleanup_not_tetris_frames(keep_count: int = 100) -> int:
    """Remove old frames from frames_not_tetris folder, keeping only the most recent ones.

    Args:
        keep_count: Number of recent frames to keep

    Returns:
        Number of removed frames
    """
    if not frames_not_tetris_path.exists():
        return 0

    frames = sorted(
        [f for f in frames_not_tetris_path.iterdir() if f.is_file() and f.suffix == ".png"],
        key=lambda x: x.name,
    )

    removed = 0
    while len(frames) > keep_count:
        frame = frames.pop(0)
        frame.unlink()
        removed += 1

    return removed
