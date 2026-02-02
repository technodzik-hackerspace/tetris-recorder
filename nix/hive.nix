let
  nodeName = "nix-tetris-recorder";
in
{
  meta = {
    nixpkgs = import (builtins.fetchGit {
      name = "nixos-24.11-2025-01-15";
      url = "https://github.com/NixOS/nixpkgs";
      ref = "refs/heads/nixos-24.11";
    }) {};
  };

  ${nodeName} = { lib, name, ... }: let
    secretsFile = ./secrets/secrets.nix;
    secrets = if builtins.pathExists secretsFile then import secretsFile else {};
    get = path: lib.attrByPath path null secrets;
  in {
    imports = [ ./hosts/nix-tetris-recorder.nix ];

    deployment = {
      targetHost = lib.mkForce (get [ "hosts" name "targetHost" ]);
      targetUser = lib.mkForce (get [ "hosts" name "targetUser" ]);
      buildOnTarget = true;

      keys = {
        "user-password" = {
          text = get [ "hosts" name "userPassword" ];
          destDir = "/run/keys";
          permissions = "0600";
        };
        "bot-secrets.toml" = {
          text = get [ "hosts" name "botSecrets" ];
          destDir = "/run/keys";
          permissions = "0640";
          group = "tetris";
        };
      };
    };

    assertions = [
      {
        assertion = get [ "hosts" name "targetHost" ] != null;
        message = "Missing targetHost for '${name}'. Create secrets/secrets.nix";
      }
    ];

    nixpkgs.system = "aarch64-linux";
  };
}
