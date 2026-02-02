{ pkgs ? import <nixpkgs> {} }:

let
  # Package dynaconf since it's not in nixpkgs
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
    # Runtime dependencies
    ps.numpy
    ps.aiogram
    ps.opencv4
    dynaconf

    # Dev dependencies
    ps.pytest
    ps.pytest-asyncio
    ps.isort
    ps.coverage
    ps.black
  ]);
in
pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.ffmpeg
    pkgs.v4l-utils
  ];

  shellHook = ''
    echo "Tetris Recorder development environment"
    echo "Python: $(python --version)"
    echo ""
    echo "Commands:"
    echo "  python main.py     - Run the application"
    echo "  pytest             - Run tests"
    echo "  pytest -v          - Run tests (verbose)"
    echo "  coverage run -m pytest && coverage report - Run tests with coverage"
  '';
}
