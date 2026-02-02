{ config, lib, pkgs, ... }:

let
  cfg = config.services.tetris-recorder;

  tetris-recorder = pkgs.callPackage ../pkgs/tetris-recorder.nix { };
in {
  options.services.tetris-recorder = {
    enable = lib.mkEnableOption "Tetris Recorder service";

    videoDevice = lib.mkOption {
      type = lib.types.str;
      default = "/dev/video0";
      description = "Video capture device path";
    };

    fps = lib.mkOption {
      type = lib.types.int;
      default = 10;
      description = "Frames per second for recording";
    };

    secretsFile = lib.mkOption {
      type = lib.types.path;
      description = "Path to .secrets.toml file containing bot_token";
    };

    dataDir = lib.mkOption {
      type = lib.types.str;
      default = "/var/lib/tetris-recorder";
      description = "Directory for storing recordings and frames";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "tetris";
      description = "User to run the service as";
    };

    group = lib.mkOption {
      type = lib.types.str;
      default = "tetris";
      description = "Group to run the service as";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.${cfg.user} = lib.mkIf (cfg.user == "tetris") {
      isSystemUser = true;
      group = cfg.group;
      extraGroups = [ "video" "keys" ];
    };

    users.groups.${cfg.group} = lib.mkIf (cfg.group == "tetris") { };

    systemd.tmpfiles.rules = [
      "d ${cfg.dataDir} 0755 ${cfg.user} ${cfg.group} -"
      "d ${cfg.dataDir}/frames 0755 ${cfg.user} ${cfg.group} -"
      "d ${cfg.dataDir}/full_frames 0755 ${cfg.user} ${cfg.group} -"
      "d ${cfg.dataDir}/videos 0755 ${cfg.user} ${cfg.group} -"
      "d ${cfg.dataDir}/regions 0755 ${cfg.user} ${cfg.group} -"
    ];

    systemd.services.tetris-recorder = {
      description = "Tetris Recorder";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        SETTINGS_FILES_FOR_DYNACONF = "${cfg.dataDir}/settings.toml;${cfg.dataDir}/.secrets.toml";
      };

      preStart = ''
        # Create settings.toml
        cat > ${cfg.dataDir}/settings.toml << EOF
        [default]
        image_device = "${cfg.videoDevice}"
        fps = ${toString cfg.fps}
        EOF

        # Link secrets file
        ln -sf ${cfg.secretsFile} ${cfg.dataDir}/.secrets.toml
      '';

      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.group;
        WorkingDirectory = cfg.dataDir;
        ExecStart = "${tetris-recorder}/bin/tetris-recorder";
        Restart = "always";
        RestartSec = 5;

        # Hardening
        NoNewPrivileges = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.dataDir ];
        PrivateTmp = true;

        # Access to video device
        DeviceAllow = [ cfg.videoDevice ];
        SupplementaryGroups = [ "video" ];
      };
    };

    environment.systemPackages = [
      tetris-recorder
      pkgs.ffmpeg
      pkgs.v4l-utils
    ];
  };
}
