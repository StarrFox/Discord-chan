{
  description = "discord chan chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts/";
    nix-systems.url = "github:nix-systems/default";
    pre-commit-hooks.url = "github:cachix/pre-commit-hooks.nix";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    nix-systems,
    pre-commit-hooks,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      debug = true;
      systems = import nix-systems;
      perSystem = {
        pkgs,
        system,
        self',
        ...
      }: let
        python = pkgs.python311;

        pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);

        discord-ext-menus = python.pkgs.buildPythonPackage {
          pname = "discord-ext-menus";
          version = "1.0.0a0";
          format = "setuptools";
          src = pkgs.fetchFromGitHub {
            owner = "Rapptz";
            repo = "discord-ext-menus";
            rev = "8686b5d1bbc1d3c862292eb436ab630d6e9c9b53";
            hash = "sha256-WsPK+KyBezpKoHZUqOnhRLpMDOpmuIa6JLvqBLFRkXc=";
          };
          pythonImportsCheck = ["discord.ext.menus"];
          nativeBuildInputs = with python.pkgs; [pip];
          propagatedBuildInputs = with python.pkgs; [discordpy];
        };

        uwuify = python.pkgs.buildPythonPackage rec {
          pname = "uwuify";
          version = "1.3.0";
          format = "pyproject";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-t/PduCEJMgPEdCuP1rWh+X68r3RjTQdgu9MH1sGOjI4=";
          };
          pythonImportsCheck = [pname];
          nativeBuildInputs = with python.pkgs; [poetry-core];
          propagatedBuildInputs = with python.pkgs; [click];
        };

        import_expression = python.pkgs.buildPythonPackage rec {
          pname = "import_expression";
          version = "1.1.4";
          format = "setuptools";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-BghqarO/pSixxHjmM9at8rOpkOMUQPZAGw8+oSsGWak=";
          };
          pythonImportsCheck = [pname];
          nativeBuildInputs = with python.pkgs; [pip];
          # tests file not included with release
          doCheck = false;
        };

        jishaku = python.pkgs.buildPythonPackage rec {
          pname = "jishaku";
          version = "2.5.2";
          format = "setuptools";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-VtOMMzA243SB3148noHWAztQl3OPDRcageJ1ISTw31w=";
          };
          pythonImportsCheck = [pname];
          nativeCheckInputs = with python.pkgs; [
            line_profiler
            click
            astunparse
            youtube-dl
          ];
          propagatedBuildInputs = with python.pkgs; [
            discordpy
            braceexpand
            import_expression
          ];
        };
      in {
        packages.discord_chan = python.pkgs.buildPythonPackage rec {
          inherit (pyproject.tool.poetry) version;

          src = ./.;
          pname = "discord_chan";
          format = "pyproject";
          pythonImportsCheck = [pname];
          nativeBuildInputs = [
            python.pkgs.poetry-core
          ];
          propagatedBuildInputs = with python.pkgs; [
            loguru
            discordpy
            wand
            humanize
            pillow
            discord-ext-menus
            asyncpg
            pendulum
            numpy
            uwuify
            parsedatetime
            jishaku
            unidecode
            uvloop
            psutil
            typing-extensions
          ];

          meta.mainProgram = "discord_chan";
        };

        packages.default = self'.packages.discord_chan;

        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              black.enable = true;
              alejandra.enable = true;
              statix.enable = true;
              typos.enable = true;
            };
          };
        };

        devShells.default = pkgs.mkShell {
          name = "discord_chan";
          inherit (self'.checks.pre-commit-check) shellHook;
          packages = with pkgs; [
            (poetry.withPlugins (ps: with ps; [poetry-plugin-up]))
            python
            just
            alejandra
            python.pkgs.black
            python.pkgs.isort
            python.pkgs.python-lsp-server
            python.pkgs.mypy
          ];
        };
      };
      flake = {
        nixosModules.discord_chan = import ./modules/discord_chan.nix {
          # packages.system is taken from pkgs.system
          selfpkgs = self.packages;
        };

        nixosModules.default = self.nixosModules.discord_chan;
      };
    };
}
