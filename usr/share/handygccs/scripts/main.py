#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import asyncio
import os
import signal
import subprocess
import sys
import warnings

import constants as cons
import common as com
from pathlib import Path
#from shutil import move
from time import sleep, time

# TODO: asyncio is using a deprecated method in its loop, find an alternative.
# Suppress for now to keep journalctl output clean.
warnings.filterwarnings("ignore", category=DeprecationWarning)

def __init__():
    global HAS_CHIMERA_LAUNCHER
    global running
    com.running = True

    com.get_user()
    com.HAS_CHIMERA_LAUNCHER=os.path.isfile(cons.CHIMERA_LAUNCHER_PATH)
    com.id_system()
    Path(cons.HIDE_PATH).mkdir(parents=True, exist_ok=True)
    com.get_config()
    com.make_controller()

# Main loop
def main():

    # Run asyncio loop to capture all events.
    loop = asyncio.get_event_loop()

    # Attach the event loop of each device to the asyncio loop.
    asyncio.ensure_future(com.capture_controller_events())
    asyncio.ensure_future(com.capture_gyro_events())
    asyncio.ensure_future(com.capture_ff_events())
    asyncio.ensure_future(com.capture_keyboard_events())
    asyncio.ensure_future(com.capture_power_events())
    asyncio.ensure_future(com.ryzenadj_control(loop))
    com.logger.info("Handheld Game Console Controller Service started.")

    # Establish signaling to handle gracefull shutdown.
    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(com.restore_all(loop)))

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

