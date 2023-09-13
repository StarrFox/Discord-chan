{
  description = "discord chan chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts/";
    nix-systems.url = "github:nix-systems/default";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    nix-systems,
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

        customOverrides = self: super: {
          uwuify = super.uwuify.overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.poetry];
            }
          );
          attrs = super.attrs.overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.hatchling super.hatch-fancy-pypi-readme super.hatch-vcs];
            }
          );
          import-expression = super."import-expression".overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.setuptools];
            }
          );
          jishaku = super.jishaku.overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.setuptools];
              propagatedBuildInputs = (old.propagatedBuildInputs or []) ++ [super.setuptools];
            }
          );
          discord-ext-menus = super.discord-ext-menus.overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.setuptools];
            }
          );
          "discord-py" = python.pkgs.discordpy;
          # this wand version patched the imageMagick library path
          wand = python.pkgs.wand;
        };
      in {
        # TODO: set meta.mainProgram to remove a warning with lib.getExe
        # should be discord_chan after the poetry2nix removal pr is merged
        packages.discord_chan = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
          python = python;
          overrides = [
            pkgs.poetry2nix.defaultPoetryOverrides
            customOverrides
          ];
          groups = ["images"];
        };

        packages.default = self'.packages.discord_chan;

        devShells.default = pkgs.mkShell {
          name = "discord_chan";
          packages = with pkgs; [
            (poetry.withPlugins (ps: with ps; [poetry-plugin-up]))
            python311
            just
            alejandra
            python311.pkgs.black
            python311.pkgs.isort
            python311.pkgs.vulture
            python311.pkgs.python-lsp-server
            python311.pkgs.mypy
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
