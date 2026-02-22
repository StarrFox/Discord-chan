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
        python = pkgs.python314;

        pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);

        discordpy_patched = (python.pkgs.discordpy.override {withVoice = false;}).overrideAttrs {
          patches = [
            (pkgs.fetchpatch {
              url = "https://github.com/Rapptz/discord.py/commit/6d19bc763c540a36b83429f8e9c6bb3dd8e16c7d.patch";
              hash = "sha256-zSf23KUi9IsqAOkgvC4KYGI/ZYvMOgdenu4dXSvCmkw=";
            })
            (pkgs.fetchpatch {
              url = "https://github.com/Rapptz/discord.py/commit/c342db853486ef6e26d72b10bf901e951c4b4d8e.patch";
              hash = "sha256-OwonE4WHCdvuiTmjK3hJTxrkVjPEGvHmfu0ftJL1/H8=";
            })
          ];
        };

        aexaroton = python.pkgs.buildPythonPackage rec {
          pname = "aexaroton";
          version = "0.2.0";
          format = "pyproject";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-3ONnH3zUATVxf8qlaTDZIGw1kfdH9XQ1QsjOKHGKkKc=";
          };
          pythonImportsCheck = [pname];
          nativeBuildInputs = with python.pkgs; [uv-build];
          propagatedBuildInputs = with python.pkgs; [aiohttp yarl pydantic];
        };

        loguru-logging-intercept = python.pkgs.buildPythonPackage rec {
          pname = "loguru-logging-intercept";
          version = "0.1.4";
          format = "setuptools";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-ORPBqXtQdMqK0v6n+lBFbLUPR2SEpCpvj8w2KlBjAGQ=";
          };
          pythonImportsCheck = ["loguru_logging_intercept"];
          propagatedBuildInputs = with python.pkgs; [loguru];
        };

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
          propagatedBuildInputs = with python.pkgs; [discordpy_patched];
        };

        uwuify = python.pkgs.buildPythonPackage rec {
          pname = "uwuify";
          version = "1.3.1";
          format = "pyproject";
          src = python.pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-uQbODHvWBez29DOOgbTamLoq6l08Jq5y/liV60zMx/4=";
          };
          pythonImportsCheck = [pname];
          nativeBuildInputs = with python.pkgs; [poetry-core];
          propagatedBuildInputs = with python.pkgs; [click];
        };
      in {
        packages.discord_chan = python.pkgs.buildPythonPackage rec {
          inherit (pyproject.project) version;

          src = ./.;
          pname = "discord_chan";
          format = "pyproject";
          pythonImportsCheck = [pname];
          nativeBuildInputs = [
            python.pkgs.uv-build
            python.pkgs.pythonRelaxDepsHook
          ];
          # disable cuck mode
          pythonRelaxDeps = true;
          pythonRemoveDeps = ["discord-ext-menus"];
          propagatedBuildInputs = with python.pkgs; [
            loguru
            discordpy_patched
            wand
            humanize
            pillow
            discord-ext-menus
            asyncpg
            pendulum
            numpy
            uwuify
            parsedatetime
            (jishaku.override {discordpy = discordpy_patched;})
            unidecode
            uvloop
            psutil
            typing-extensions
            loguru-logging-intercept
            aexaroton
            audioop-lts
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
            uv
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
        nixosModules.discord_chan = import ./nix/discord_chan.nix {
          # packages.system is taken from pkgs.system
          selfpkgs = self.packages;
        };

        nixosModules.default = self.nixosModules.discord_chan;
      };
    };
}
