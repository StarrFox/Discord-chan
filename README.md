# Discord Chan

A general purpose discord bot made with [discord.py](https://github.com/Rapptz/discord.py)

## Running

```shell script
nix run github:StarrFox/Discord-chan
```

you can pass a path to your own token file with --secret

## NixOS module

there is also a nixos module you can use

include the module with

```nix
{
  inputs.discord_chan.url = "github:StarrFox/Discord-chan";

  outputs = { self, nixpkgs, discord_chan }: {
    # change `yourhostname` to your actual hostname
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      # change to your system:
      system = "x86_64-linux";
      modules = [
        ./configuration.nix
        discord_chan.nixosModules.default
      ];
    };
  };
}
```

then use it like

```nix
services.discord_chan = {
    enable = true;
    tokenFile = "path/to/token_file";
};
```
