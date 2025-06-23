{
  description = "A modal TUI for viewing Todoist tasks using Textual";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;

        # Override todoist-api-python to use version 3.1.0
        pythonPackages = python.pkgs.overrideScope (
          final: prev: {
            todoist-api-python = prev.todoist-api-python.overridePythonAttrs (oldAttrs: {
              version = "3.1.0";
              src = pkgs.fetchPypi {
                pname = "todoist_api_python";
                version = "3.1.0";
                hash = "sha256-fK1zL1ikvfvRwHOhqL4cG04TrgyL4hC7eED7ugbrmHw=";
              };
              nativeBuildInputs = with final; [ hatchling ];
              propagatedBuildInputs = with final; [
                annotated-types
                dataclass-wizard
              ];
              # Disable pytest check phase since the package has no tests
              doCheck = false;
            });
          }
        );

        tuidoist = pythonPackages.buildPythonApplication {
          pname = "tuidoist";
          version = "0.7.0";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pythonPackages; [
            textual
            todoist-api-python
          ];

          meta = with pkgs.lib; {
            description = "A modal TUI for viewing Todoist tasks using Textual";
            homepage = "https://github.com/jmartin/tuidoist";
            license = licenses.mit;
            maintainers = [ ];
          };
        };
      in
      {
        packages.default = tuidoist;

        apps.default = {
          type = "app";
          program = "${tuidoist}/bin/tuidoist";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pip
            pythonPackages.textual
            pythonPackages.todoist-api-python
          ];

          shellHook = ''
            echo "Development environment for tuidoist"
            echo "Run 'python main.py' to start the application"
          '';
        };
      }
    );
}
