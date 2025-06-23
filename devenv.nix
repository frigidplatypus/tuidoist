{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";
  dotenv.enable = true;

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.sqlite
    pkgs.act
    # pkgs.postgresql # Uncomment if you use PostgreSQL
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    venv.enable = true;
    uv.enable = true;
    uv.sync.enable = true;
  };

  # Optionally specify Python version (uncomment to pin)
  # languages.python.version = "3.11";

  # Add a note for TUI app dependencies
  # To use textual and Todoist API, add them to pyproject.toml:
  #   textual
  #   todoist-api-python
  # Or install with: uv pip install textual todoist-api-python

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  enterShell = ''
    hello

  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
