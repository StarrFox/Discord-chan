# Discord Chan

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A general purpose discord bot made with [discord.py](https://github.com/Rapptz/discord.py)

## Installing
```shell script
git clone https://github.com/StarrFox/Discord-chan
cd Discord-chan
poetry install
discord_chan install
```

## Running
```shell script
discord_chan
```

## Monitor
Discord chan has an [aiomonitor](https://pypi.org/projects/aiomonitor) with some helpful commands

you can start the monitor with
```shell script
discord_chan monitor [--host = localhost] [--port = 50101]
```
##### commands
Command | Description
--- | ---
console | Starts an aioconsole with the bot object in locals
cmds | Lists currently loaded commands
extensions | Lists currently loaded extensions
enable | Enable or disable a command

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
