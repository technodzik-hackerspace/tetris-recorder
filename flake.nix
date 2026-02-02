{
  description = "Tetris Recorder - Record and post Tetris games to Telegram";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        dynaconf = pkgs.python311Packages.buildPythonPackage rec {
          pname = "dynaconf";
          version = "3.2.4";
          pyproject = true;

          src = pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-LmreuqWH9N+SQaFqS+w/2lIRVNJrFfMlj951OlkoMbY=";
          };

          nativeBuildInputs = [ pkgs.python311Packages.setuptools ];
          propagatedBuildInputs = [ pkgs.python311Packages.toml ];

          doCheck = false;
        };

        pythonEnv = pkgs.python311.withPackages (ps: [
          ps.numpy
          ps.aiogram
          ps.opencv4
          dynaconf
          ps.pytest
          ps.pytest-asyncio
          ps.isort
          ps.coverage
          ps.black
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.ffmpeg
            pkgs.v4l-utils
          ];

          shellHook = ''
            echo "Tetris Recorder development environment"
            echo "Python: $(python --version)"
          '';
        };

        packages.default = pkgs.callPackage ./nix/pkgs/tetris-recorder.nix { };
      }
    );
}
