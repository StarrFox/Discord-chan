# TODO: add multi-system
{
  description = "discord chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    starrpkgs = {
      url = "github:StarrFox/packages";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    starrpkgs,
  }: let
    system = "x86_64-linux";

    pkgs = nixpkgs.legacyPackages.${system};
    spkgs = starrpkgs.packages.${system};

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
      wand = pkgs.python3Packages.wand;
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
    packages.${system} = {
      ${packageName} = app;
      default = self.packages.${system}.${packageName};
    };

    nixosModules = {
      ${packageName} = import ./modules/discord_chan.nix {
        selfpkgs = self.packages.${system};
      };
      default = self.nixosModules.${packageName};
    };

    devShells.${system}.default = pkgs.mkShell {
      name = "discord-chan";
      packages = with pkgs; [poetry spkgs.commitizen just alejandra black isort];
    };
  };
}
