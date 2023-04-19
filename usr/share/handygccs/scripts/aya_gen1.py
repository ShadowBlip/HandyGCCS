#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

#import asyncio
#import configparser
#import logging
#import os
#import platform
#import re
#import signal
#import subprocess
#import sys
#import warnings
#
#from constants import CONTROLLER_EVENTS, DETECT_DELAY, EVENT_ALT_TAB, EVENT_ESC, EVENT_MODE, EVENT_KILL, EVENT_OSK, EVENT_QAM, EVENT_SCR, FF_DELAY, HIDE_PATH, JOY_MAX, JOY_MIN
#from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff
#from pathlib import Path
#from shutil import move
#from time import sleep, time

logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                    datefmt="%y%m%d_%H:%M:%S",
                    level=logging.INFO
                    )

logger = logging.getLogger(__name__)

## Declare globals
# Functionality Variables
event_queue = [] # Stores incoming button presses to block spam

# Devices
controller_device = None
gyro_device = None
keyboard_device = None
power_device = None
power_device_extra = None

# Paths
controller_event = None
controller_path = None
keyboard_event = None
keyboard_path = None

# Constants
BUTTON_DELAY = 0.09
CAPTURE_CONTROLLER = True
CAPTURE_KEYBOARD = True
CAPTURE_POWER = True
GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
GYRO_I2C_ADDR = 0x68
GYRO_I2C_BUS = 1
KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
POWER_BUTTON_PRIMARY = "PNP0C0C/button/input0"
POWER_BUTTON_SECONDARY = "LNXPWRBN/button/input0"

# Captures keyboard events and translates them to virtual device events.
async def capture_aya_gen1_events(seed_event):
    # Get access to global variables. These are globalized because the function
    # is instanciated twice and need to persist accross both instances.
    global button_map
    global event_queue
    global gyro_device
    global gyro_enabled
    global keyboard_device
    global shutdown

    # Button map shortcuts for easy reference.
    button1 = button_map["button1"]  # Default Screenshot
    button2 = button_map["button2"]  # Default QAM
    button3 = button_map["button3"]  # Default ESC
    button4 = button_map["button4"]  # Default OSK
    button5 = button_map["button5"]  # Default MODE
    button6 = ["RyzenAdj Toggle"]
    button7 = ["Open Chimera"]
    last_button = None

    ## Loop variables
    active = keyboard_device.active_keys()
    events = []
    this_button = None
    button_on = seed_event.value

    ## Debugging variables
    if active != []:
        logging.debug(f"Active Keys: {active}, Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
        logging.debug(f"Queued events: {event_queue}")
    elif active == [] and event_queue != []:
        logging.debug(f"Queued events: {event_queue}")

    ## Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        events.append(seed_event)
    match system_type:

    # BUTTON 1 (Default: Screenshot) WIN button
    # Temporarily RyzenAdj toggle/button6
    if active == [125] and button_on == 1 and button6 not in event_queue and shutdown == False:
        event_queue.append(button6)
    elif active == [] and seed_event.code == 125 and button_on == 0 and button6 in event_queue:
        event_queue.remove(button6)
        await toggle_performance()

    # BUTTON 2 (Default: QAM) TM Button
    if active == [97, 100, 111] and button_on == 1 and button2 not in event_queue:
        event_queue.append(button2)
    elif active == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in event_queue:
        this_button = button2
        await do_rumble(0, 150, 1000, 0)

    # BUTTON 3 (Default: ESC) ESC Button
    if active == [1] and seed_event.code == 1 and button_on == 1 and button3 not in event_queue:
        event_queue.append(button3)
    elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
        this_button = button3
    # BUTTON 3 SECOND STATE (Default: Toggle Gyro)
    elif seed_event.code == 1 and button_on == 2 and button3 in event_queue and gyro_device:
        event_queue.remove(button3)
        gyro_enabled = not gyro_enabled
        if gyro_enabled:
            await do_rumble(0, 250, 1000, 0)
        else:
            await do_rumble(0, 100, 1000, 0)
            await asyncio.sleep(FF_DELAY)
            await do_rumble(0, 100, 1000, 0)

    # BUTTON 4 (Default: OSK) KB Button
    if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
        event_queue.append(button4)
    elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
        this_button = button4

    # Handle L_META from power button
    elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
        shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not last_button:
        for button_event in this_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 1)
            events.append(event)
        event_queue.remove(this_button)
        last_button = this_button

    # Clean up old button presses.
    elif last_button and not this_button:
        for button_event in last_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 0)
            events.append(event)
        last_button = None

    # Push out all events.
    if events != []:
        await emit_events(events)

