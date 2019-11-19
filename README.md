# RLBot Choreography

This project can produce choreographed sequences of car motion in
Rocket League. It's useful for making cool synchronized performances.

![Bots doing the wave](wave.gif)

## Setup

1. Make sure you've installed [Python 3.7 64 bit](https://www.python.org/ftp/python/3.7.4/python-3.7.4-amd64.exe). During installation:
   - Select "Add Python to PATH"
   - Make sure pip is included in the installation
1. Download or clone this repository
1. In a command prompt, run `pip install rlbot`

## Usage

In a command prompt, in this directory, run `python ChoreographyHive`

You can pass in an argument to specify the folder for bot appearances with `python ChoreographyHive --bot-folder=C:/some/path`
Other settings can be customised through the GUI.

- If you have a bunch of bots in your bot folder (e.g. maybe you grabbed https://github.com/RLBot/RLBotPack),
we will find all the bots there and use their appearances for the drones. There will be one drone spawned for each.

## Origins

This is based on 'hivemind' code shared by Viliam Vadocz.
Original code is here: https://github.com/ViliamVadocz/RLBot

The underlying framework is explained at http://www.rlbot.org/