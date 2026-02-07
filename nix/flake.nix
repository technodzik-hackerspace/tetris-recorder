{
  description = "Tetris Recorder NixOS deployment with Colmena";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    colmena = {
      url = "github:zhaofengli/colmena";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, colmena, ... }:
  {
    colmena = import ./hive.nix { inherit nixpkgs; };

    nixosConfigurations.nix-tetris-recorder = nixpkgs.lib.nixosSystem {
      system = "aarch64-linux";
      modules = [ ./hosts/nix-tetris-recorder.nix ];
    };
  };
}
