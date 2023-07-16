#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

# Python Modules
import asyncio
import logging
import os
import signal
import sys
import warnings

## Local modules
from .constants import *
from .devices import *
from .utilities import *

## Partial imports
from pathlib import Path


warnings.filterwarnings("ignore", category=DeprecationWarning)
class HandheldController:
    # Logging
    logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                        datefmt="%y%m%d_%H:%M:%S",
                        level=logging.DEBUG
                        )
    logger= logging.getLogger(__name__)
    
    # Session Variables
    button_map = {}
    event_queue = [] # Stores inng button presses to block spam
    last_button = None
    last_x_val = 0
    last_y_val = 0
    running = False
    shutdown = False
    
    # Handheld Config
    BUTTON_DELAY = 0.00
    CAPTURE_CONTROLLER = False
    CAPTURE_KEYBOARD = False
    CAPTURE_POWER = False
    GAMEPAD_ADDRESS = ''
    GAMEPAD_NAME = ''
    KEYBOARD_ADDRESS = ''
    KEYBOARD_NAME = ''
    KEYBOARD_2_ADDRESS = ''
    KEYBOARD_2_NAME = ''
    POWER_BUTTON_PRIMARY = "LNXPWRBN/button/input0"
    POWER_BUTTON_SECONDARY = "PNP0C0C/button/input0"
    
    # Enviroment Variables
    HAS_CHIMERA_LAUNCHER = False
    USER = None
    HOME_PATH = None
    
    # UInput Devices
    controller_device = None
    #gyro_device = None
    keyboard_device = None
    keyboard_2_device = None
    power_device = None
    power_device_2 = None
    
    # Paths
    controller_event = None
    controller_path = None
    keyboard_event = None
    keyboard_path = None
    keyboard_2_event = None
    keyboard_2_path = None
    
    # Performance settings
    performance_mode = "--power-saving"
    thermal_mode = "0"
    
    def __init__(self):
        self.running = True
        self.logger.info("Starting Handhend Game Console Controller Service...") 
        get_user()
        self.HAS_CHIMERA_LAUNCHER=os.path.isfile(CHIMERA_LAUNCHER_PATH)
        id_system()
        Path(HIDE_PATH).mkdir(parents=True, exist_ok=True)
        get_config()
        make_controller()
    
        # Run asyncio loop to capture all events.
        self.loop = asyncio.get_event_loop()
    
        # Attach the event loop of each device to the asyncio loop.
        asyncio.ensure_future(capture_controller_events())
        asyncio.ensure_future(capture_ff_events())
        asyncio.ensure_future(capture_keyboard_events())
        if self.KEYBOARD_2_NAME != '' and self.KEYBOARD_2_ADDRESS != '':
            asyncio.ensure_future(capture_keyboard_2_events())

        asyncio.ensure_future(capture_power_events())
        self.logger.info("Handheld Game Console Controller Service started.")
    
        # Establish signaling to handle gracefull shutdown.
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
            self.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(self.exit()))
    
        try:
            self.loop.run_forever()
            exit_code = 0
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt.")
            exit_code = 1
        except Exception as err:
            self.logger.error(f"{err} | Hit exception condition.")
            exit_code = 2
        finally:
            self.loop.stop()
            sys.exit(exit_code)

    # Gracefull shutdown.
    async def exit(self):
        self.logger.info("Receved exit signal. Restoring devices.")
        self.running = False
    
        if self.controller_device:
            try:
                self.controller_device.ungrab()
            except IOError as err:
                pass
            restore_device(self.controller_event, self.controller_path)
        if self.keyboard_device:
            try:
                self.keyboard_device.ungrab()
            except IOError as err:
                pass
            restore_device(self.keyboard_event, self.keyboard_path)
        if self.keyboard_2_device:
            try:
                self.keyboard_2_device.ungrab()
            except IOError as err:
                pass
            restore_device(self.keyboard_2_event, self.keyboard_2_path)
        if self.power_device and self.CAPTURE_POWER:
            try:
                self.power_device.ungrab()
            except IOError as err:
                pass
        if self.power_device_2 and self.CAPTURE_POWER:
            try:
                self.power_device_2.ungrab()
            except IOError as err:
                pass
        self.logger.info("Devices restored.")
    
        # Kill all tasks. They are infinite loops so we will wait forver.
        for task in [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.loop.stop()
        self.logger.info("Handheld Game Console Controller Service stopped.")
    
    
def main():
    handycon = HandheldController()

