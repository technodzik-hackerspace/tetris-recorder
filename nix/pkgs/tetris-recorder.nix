{ lib
, stdenv
, python311
, fetchFromGitHub
, fetchPypi
, ffmpeg
, makeWrapper
}:

let
  # Package dynaconf since it's not in nixpkgs
  dynaconf = python311.pkgs.buildPythonPackage rec {
    pname = "dynaconf";
    version = "3.2.4";
    pyproject = true;

    src = fetchPypi {
      inherit pname version;
      hash = "sha256-LmreuqWH9N+SQaFqS+w/2lIRVNJrFfMlj951OlkoMbY=";
    };

    nativeBuildInputs = [ python311.pkgs.setuptools ];
    propagatedBuildInputs = [ python311.pkgs.toml ];

    doCheck = false;
    pythonImportsCheck = [ "dynaconf" ];
  };

  pythonEnv = python311.withPackages (ps: [
    ps.numpy
    ps.aiogram
    ps.opencv4
    dynaconf
  ]);
in
stdenv.mkDerivation rec {
  pname = "tetris-recorder";
  version = "unstable-2024";

  src = fetchFromGitHub {
    owner = "technodzik-hackerspace";
    repo = "tetris-recorder";
    rev = "main";
    hash = "sha256-y0bbsIhBSgHBr2nHcPL1RIq0zQO6CQVJZfjaxQcor1w=";
  };

  nativeBuildInputs = [ makeWrapper ];
  buildInputs = [ pythonEnv ffmpeg ];

  dontBuild = true;

  # Fix deprecated default_settings_paths -> settings_files
  postPatch = ''
    substituteInPlace config.py \
      --replace "default_settings_paths" "settings_files"
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/tetris-recorder
    cp -r . $out/lib/tetris-recorder/

    mkdir -p $out/bin
    makeWrapper ${pythonEnv}/bin/python $out/bin/tetris-recorder \
      --set PYTHONPATH "$out/lib/tetris-recorder" \
      --prefix PATH : "${lib.makeBinPath [ ffmpeg ]}" \
      --add-flags "$out/lib/tetris-recorder/main.py"

    runHook postInstall
  '';

  meta = with lib; {
    description = "Record and post Tetris games to Telegram";
    homepage = "https://github.com/technodzik-hackerspace/tetris-recorder";
    mainProgram = "tetris-recorder";
  };
}
