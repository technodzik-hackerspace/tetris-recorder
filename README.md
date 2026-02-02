# tetris-recorder

Script to record and post to Telegram tetris games played on the 8-bit game console.

## Requirements

- Python 3.11+
- Video capture device (e.g., `/dev/video0`)
- FFmpeg
- v4l-utils

## Installation

### NixOS / Nix

```bash
nix-shell
python main.py
```

Or with flakes:

```bash
nix develop
python main.py
```

### Ubuntu/Debian

```bash
sudo apt install v4l-utils ffmpeg python3-pipenv
pipenv install
pipenv shell
python main.py
```

## Configuration

Copy `settings.toml` and create `.secrets.toml`:

```toml
[default]
bot_token = "your-telegram-bot-token"
bot_channel = -1000000000000
```

## Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_frame.py

# Run a specific test
pytest tests/test_frame.py::test_function_name

# Run tests with coverage
coverage run -m pytest
coverage report

# Generate HTML coverage report
coverage html
```

## Deployment

See [nix/README.md](nix/README.md) for NixOS deployment with Colmena.
