{
  description = "A modal TUI for viewing Todoist tasks using Textual";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
        
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
      });
}