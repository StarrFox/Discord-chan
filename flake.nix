{
  description = "discord chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

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
        };

        app = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
          overrides = [
            pkgs.poetry2nix.defaultPoetryOverrides
            customOverrides
          ];
          groups = [
            "images"
          ];
        };

        packageName = "discord_chan";
      in {
        packages.${packageName} = app;

        defaultPackage = self.packages.${system}.${packageName};

        # we use this wand because it has a patch to the correct image magick
        buildInputs = with pkgs; [ python3Packages.wand ];

        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [ poetry commitizen just python3Packages.wand ];
          inputsFrom = builtins.attrValues self.packages.${system};
        };
      }
    );
}