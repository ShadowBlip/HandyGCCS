#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import asyncio
import logging
import os
import signal
import subprocess
#import sys
import warnings
#
from constants import * 
from common import *
from pathlib import Path
#from shutil import move
from time import sleep, time

logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                    datefmt="%y%m%d_%H:%M:%S",
                    level=logging.INFO
                    )

logger = logging.getLogger(__name__)

# TODO: asyncio is using a deprecated method in its loop, find an alternative.
# Suppress for now to keep journalctl output clean.
warnings.filterwarnings("ignore", category=DeprecationWarning)

HIDE_PATH = Path(HIDE_PATH)

CHIMERA_LAUNCHER_PATH='/usr/share/chimera/bin/chimera-web-launcher'
HAS_CHIMERA_LAUNCHER=os.path.isfile(CHIMERA_LAUNCHER_PATH)

server_address = '/tmp/ryzenadj_socket'

# Capture the username and home path of the user who has been logged in the longest.
USER = None
HOME_PATH = Path('/home')
cmd = "who | awk '{print $1}' | sort | head -1"
while USER is None:
    USER_LIST = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
    for get_first in USER_LIST.stdout:
        name = get_first.decode().strip()
        if name is not None:
            USER = name
        break
    #who = [w.split(' ', maxsplit=1) for w in os.popen('who').read().strip().split('\n')]
    #who = [(w[0], re.search(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", w[1]).groups()[0]) for w in who]
    #who.sort(key=lambda row: row[1])
    #USER = who[0][0]
    sleep(.1)
logger.debug(f"USER: {USER}")
HOME_PATH /= USER
logger.debug(f"HOME_PATH: {HOME_PATH}")
running = True
shutdown = False

def __init__():
    id_system()
    Path(HIDE_PATH).mkdir(parents=True, exist_ok=True)
    get_config()
    make_controller()

# Main loop
def main():
    # Run asyncio loop to capture all events.
    loop = asyncio.get_event_loop()

    # Attach the event loop of each device to the asyncio loop.
    #asyncio.ensure_future(capture_controller_events())
    #asyncio.ensure_future(capture_gyro_events())
    #asyncio.ensure_future(capture_ff_events())
    #asyncio.ensure_future(capture_keyboard_events())
    #asyncio.ensure_future(capture_power_events())
    #asyncio.ensure_future(ryzenadj_control(loop))
    logger.info("Handheld Game Console Controller Service started.")

    # Establish signaling to handle gracefull shutdown.
    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(restore_all(loop)))

    try:
        loop.run_forever()
        exit_code = 0
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt.")
        exit_code = 1
    except Exception as err:
        logger.error(f"{err} | Hit exception condition.")
        exit_code = 2
    finally:
        loop.stop()
        sys.exit(exit_code)

if __name__ == "__main__":
    __init__()
    main()

