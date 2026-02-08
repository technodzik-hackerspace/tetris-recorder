import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGameFolders:
    """Tests for game folder creation and cleanup."""

    def test_create_game_folder(self):
        """Test that create_game_folder creates a timestamped folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "games"
            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import create_game_folder

                folder = create_game_folder()

                assert folder.exists()
                assert folder.is_dir()
                assert folder.name.startswith("game_")
                assert folder.parent == tmp_games

    def test_cleanup_old_games_removes_oldest(self):
        """Test that cleanup_old_games removes oldest folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "games"
            tmp_games.mkdir()

            # Create 7 game folders with predictable names
            folders = []
            for i in range(7):
                folder = tmp_games / f"game_2024_01_{i+10:02d}_12_00_00"
                folder.mkdir()
                # Add a file to each folder
                (folder / "frame.png").touch()
                folders.append(folder)

            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import cleanup_old_games

                removed = cleanup_old_games(keep_count=5)

                # Should have removed 2 oldest folders
                assert len(removed) == 2
                assert removed[0].name == "game_2024_01_10_12_00_00"
                assert removed[1].name == "game_2024_01_11_12_00_00"

                # Only 5 folders should remain
                remaining = list(tmp_games.iterdir())
                assert len(remaining) == 5

                # Oldest remaining should be game_2024_01_12
                remaining_names = sorted([f.name for f in remaining])
                assert remaining_names[0] == "game_2024_01_12_12_00_00"

    def test_cleanup_old_games_no_removal_needed(self):
        """Test that cleanup_old_games does nothing if under limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "games"
            tmp_games.mkdir()

            # Create only 3 folders
            for i in range(3):
                folder = tmp_games / f"game_2024_01_{i+10:02d}_12_00_00"
                folder.mkdir()

            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import cleanup_old_games

                removed = cleanup_old_games(keep_count=5)

                assert len(removed) == 0
                assert len(list(tmp_games.iterdir())) == 3

    def test_cleanup_old_games_empty_dir(self):
        """Test that cleanup_old_games handles empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "games"
            tmp_games.mkdir()

            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import cleanup_old_games

                removed = cleanup_old_games(keep_count=5)

                assert len(removed) == 0

    def test_cleanup_old_games_nonexistent_dir(self):
        """Test that cleanup_old_games handles nonexistent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "nonexistent"

            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import cleanup_old_games

                removed = cleanup_old_games(keep_count=5)

                assert len(removed) == 0

    def test_cleanup_ignores_non_game_folders(self):
        """Test that cleanup_old_games ignores folders not starting with game_."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_games = Path(tmpdir) / "games"
            tmp_games.mkdir()

            # Create game folders
            for i in range(6):
                folder = tmp_games / f"game_2024_01_{i+10:02d}_12_00_00"
                folder.mkdir()

            # Create non-game folders
            (tmp_games / "other_folder").mkdir()
            (tmp_games / "backup").mkdir()

            with patch("utils.dirs.games_path", tmp_games):
                from utils.dirs import cleanup_old_games

                removed = cleanup_old_games(keep_count=5)

                # Should only remove 1 game folder (oldest)
                assert len(removed) == 1
                assert removed[0].name == "game_2024_01_10_12_00_00"

                # Non-game folders should still exist
                assert (tmp_games / "other_folder").exists()
                assert (tmp_games / "backup").exists()
