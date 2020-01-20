# Discord Chan
A general purpose discord bot made with [discord.py](https://github.com/Rapptz/discord.py)

## Installing
```shell script
pip install git+https://github.com/StarrFox/discord-chan@master
discord_chan install [--config path/to/config = config.ini] [--no-sql = True]
```

## Running
```shell script
discord_chan [--config path/to/config = config.ini] [--debug = False]
```

## Command highlights
Command | Description
--- | ---
[snipe][snipe] | Snipes deleted and edited messages
[snipe2][snipe] | Like snipe but with command-line args
[raw][info] | View raw discord objects
[wallemoji][wallemojis] | Creates multiple pictures out of one

## Jishaku flags
Jishaku flags allow you to customize how Jishaku runs

Flag | Description
--- | ---
JISHAKU_HIDE | If the jishaku cog should be hidden from help
JISHAKU_NO_DM_TRACEBACK | If tracebacks should be sent to channel
JISHAKU_NO_UNDERSCORE | If builtin args such as _ctx should lose the _
JISHAKU_RETAIN | If retain should be on by default

These flags can be set either in the config or through some other way of accessing
the enviroment variables.
If you wish to set them yourself make sure to disable the 'load enviroment' option
in the config file.

[wallemojis]: /discord_chan/extensions/commands/images.py
[info]: /discord_chan/extensions/commands/meta.py
[snipe]: /discord_chan/extensions/commands/snipe.py