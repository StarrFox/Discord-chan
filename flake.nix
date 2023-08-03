{
  description = "discord chan chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-parts.url = "github:hercules-ci/flake-parts/";
    nix-systems.url = "github:nix-systems/default";
    starrpkgs = {
      url = "github:StarrFox/packages";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-parts.follows = "flake-parts";
        nix-systems.follows = "nix-systems";
      };
    };
  };

  outputs = inputs @ {
    self,
    flake-parts,
    nix-systems,
    starrpkgs,
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
        spkgs = starrpkgs.packages.${system};

        # python311Optimized = pkgs.python311.override {
        #     enableOptimizations = true;
        #     reproducibleBuild = false;
        #     self = python311Optimized;
        # };

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
          "discord-py" = super."discord-py".overridePythonAttrs (
            old: {
              buildInputs = (old.buildInputs or []) ++ [super.setuptools];
            }
          );
          # this wand version patched the imageMagick library path
          wand = pkgs.python311.pkgs.wand;
        };
      in {
        packages.discord_chan = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
          python = pkgs.python311;
          overrides = [
            pkgs.poetry2nix.defaultPoetryOverrides
            customOverrides
          ];
          groups = ["images"];
          # I can't figure out how to give it a dictonary
          #buildInputs = with pkgs; [hunspell hunspellDicts.en_US];
        };

        packages.default = self'.packages.discord_chan;

        devShells.default = pkgs.mkShell {
          name = "discord-chan";
          packages = with pkgs; [
            (poetry.withPlugins(ps: with ps; [poetry-plugin-up]))
            python311
            spkgs.commitizen
            just
            alejandra
            python311.pkgs.black
            python311.pkgs.isort
            python311.pkgs.vulture
            python311.pkgs.python-lsp-server
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
