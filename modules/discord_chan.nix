# TODO: make database name option
{selfpkgs, ...}: {
  config,
  lib,
  pkgs,
  ...
}:
with lib; let
  cfg = config.services.discord_chan;
  defaultUser = "discord_chan";
  spkgs = selfpkgs.${pkgs.system};
in {
  # used for debugging
  _file = "discord_chan.nix";

  options.services.discord_chan = {
    enable = mkEnableOption "discord_chan service";
    user = mkOption {
      default = defaultUser;
      example = "alice";
      type = types.str;
      description = lib.mdDoc ''
        Name of an existing user that owns bot process
        creates a user named discord_chan by default
      '';
    };
    group = mkOption {
      default = defaultUser;
      example = "users";
      type = types.str;
      description = lib.mdDoc ''
        Name of an existing group that owns the bot process
        creates a group named discord_chan by default
      '';
    };
    tokenFile = mkOption {
      type = types.path;
      example = literalExpression "~/discord_token";
      description = lib.mdDoc ''
        file with discord token to be used by the bot
      '';
    };
    exarotonTokenFile = mkOption {
      type = types.path;
      example = literalExpression "~/exaroton_token";
      description = lib.mdDoc ''
        file with exaroton token to be used by the bot
      '';
      default = null;
    };
  };
  config = mkIf cfg.enable {
    systemd.services.discord_chan = {
      description = "Discord chan bot";
      wantedBy = ["multi-user.target"];
      after = ["network-online.target"];
      wants = ["network-online.target"];
      serviceConfig = {
        User = cfg.user;
        Group = cfg.group;
        Restart = "always";
        ExecStart = "${lib.getExe spkgs.discord_chan} --secret ${cfg.tokenFile} ${if cfg.exarotonTokenFile == null then '' else '--exaroton ${cfg.exarotonTokenFile}'}";
      };
    };

    users.users = optionalAttrs (cfg.user == defaultUser) {
      ${defaultUser} = {
        description = "discord chan process owner";
        group = defaultUser;
        isSystemUser = true;
      };
    };

    users.groups = optionalAttrs (cfg.user == defaultUser) {
      ${defaultUser} = {
        members = [defaultUser];
      };
    };
  };
}
