# NixOS Deployment with Colmena

NixOS configuration for deploying Tetris Recorder to a Raspberry Pi 4 using Colmena.

## Prerequisites

- Nix with flakes enabled
- SSH access to the Raspberry Pi via Tailscale

## Target Host

Configured in `secrets/secrets.nix` (not committed to git).

## Commands

```bash
cd nix

# Deploy
nix run github:zhaofengli/colmena -- apply

# Or with colmena installed
colmena apply

# Build without deploying
colmena build

# Update tetris-recorder to latest
nix flake lock --update-input nixpkgs
colmena apply
```

## Structure

```
nix/
├── flake.nix                    # Flake entry point
├── flake.lock
├── hive.nix                     # Colmena hive configuration
├── hosts/
│   └── nix-tetris-recorder.nix  # Host configuration
├── modules/
│   └── tetris-recorder.nix      # Service module
├── pkgs/
│   └── tetris-recorder.nix      # Package definition
├── secrets/                     # Secrets (gitignored)
│   ├── secrets.nix              # Deployment targets (host, user)
│   ├── wifi-secrets             # WiFi PSK
│   ├── user-password            # User password hash
│   └── bot-token.toml           # Telegram bot config
└── README.md
```

## Service Configuration

The `services.tetris-recorder` module provides:

```nix
services.tetris-recorder = {
  enable = true;
  videoDevice = "/dev/video0";  # Video capture device
  fps = 10;                      # Recording framerate
  secretsFile = "/path/to/.secrets.toml";
  dataDir = "/var/lib/tetris-recorder";  # Data directory
  user = "tetris";               # Service user
  group = "tetris";              # Service group
};
```

## Secrets Setup

```bash
cd nix/secrets

# Deployment target
cp secrets.nix.example secrets.nix
# Edit with your targetHost and targetUser

# WiFi PSK
cp wifi-secrets.example wifi-secrets
# Format: psk_home=YourPassword

# User password
mkpasswd -m sha-512 "yourpassword" > user-password

# Bot token
cp bot-token.toml.example bot-token.toml
# Edit with your bot_token and bot_channel
```

## What Changed from Docker Version

- **No Docker**: Uses native NixOS systemd service
- **Proper packaging**: Python app packaged with all dependencies via Nix
- **Service hardening**: Runs as dedicated `tetris` user with restricted permissions
- **Data isolation**: Recordings stored in `/var/lib/tetris-recorder`
- **Declarative config**: All settings managed through NixOS options

## Notes

- Builds on target (`buildOnTarget = true`) to avoid cross-compilation
- Service auto-restarts on failure
- Keys uploaded to `/run/keys/` on each deploy (tmpfs)
