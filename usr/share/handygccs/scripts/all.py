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

# TODO: asyncio is using a deprecated method in its loop, find an alternative.
# Suppress for now to keep journalctl output clean.
warnings.filterwarnings("ignore", category=DeprecationWarning)

## Declare globals

# Constants
BUTTON_DELAY = 0.0

# These determine if we take exclusive control of the device or not. Most devices
# will be True, but some like the WinMax devices with full keyboard only need
# gyro support.

CAPTURE_CONTROLLER = False
CAPTURE_KEYBOARD = None
CAPTURE_POWER = None
GAMEPAD_ADDRESS = None
GAMEPAD_NAME = None
GYRO_I2C_ADDR = None
GYRO_I2C_BUS = None
KEYBOARD_ADDRESS = None
KEYBOARD_NAME = None
POWER_BUTTON_PRIMARY = "PNP0C0C/button/input0"
POWER_BUTTON_SECONDARY = "LNXPWRBN/button/input0"

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

#    elif system_id in (
#        "NEXT",
#        "NEXT Pro",
#        "NEXT Advance",
#        "AYANEO NEXT",
#        "AYANEO NEXT Pro",
#        "AYANEO NEXT Advance",
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        system_type = "AYA_GEN2"
#
#    elif system_id in (
#        "AIR",
#        "AIR Pro",
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:04:00.3-4/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        system_type = "AYA_GEN3"
#    
#    elif system_id in (
#        "AYANEO 2",
#        "GEEK",
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:e4:00.3-4/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        system_type = "AYA_GEN4"
#
#
#    ## ONEXPLAYER and AOKZOE devices.
#    # BIOS have incomplete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
#    elif system_id in (
#        "ONE XPLAYER",
#        "ONEXPLAYER",
#        "ONEXPLAYER mini A07",
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        if cpu_vendor == "GenuineIntel":
#            GAMEPAD_ADDRESS = 'usb-0000:00:14.0-9/input0'
#            GAMEPAD_NAME = 'OneXPlayer Gamepad'
#            system_type = "OXP_GEN1"
#        else:
#            GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
#            GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#            system_type = "OXP_GEN2"
#        logger.info(f"Found {system_type} with {GAMEPAD_NAME}.")
#
#    elif system_id in (
#        "ONEXPLAYER Mini Pro",
#        "AOKZOE A1 AR07"
#        ):
#        BUTTON_DELAY = 0.08
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:e3:00.3-4/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        system_type = "OXP_GEN3"
#
#    ## GPD Devices.
#    # Have 2 buttons with 3 modes (left, right, both)
#    elif system_id in (
#        "G1618-03", #Win3
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:00:14.0-7/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        KEYBOARD_ADDRESS = 'usb-0000:00:14.0-5/input0'
#        KEYBOARD_NAME = '  Mouse for Windows'
#        system_type = "GPD_GEN1"
#
#    elif system_id in (
#        "G1618-04", #WinMax2
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:74:00.3-3/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x69
#        GYRO_I2C_BUS = 2
#        KEYBOARD_ADDRESS = 'usb-0000:74:00.3-4/input1'
#        KEYBOARD_NAME = '  Mouse for Windows'
#        system_type = "GPD_GEN2"
#
#    elif system_id in (
#        "G1619-04", #Win4
#        ):
#        BUTTON_DELAY = 0.09
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        GAMEPAD_ADDRESS = 'usb-0000:73:00.3-4/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        GYRO_I2C_ADDR = 0x68
#        GYRO_I2C_BUS = 1
#        KEYBOARD_ADDRESS = 'usb-0000:73:00.4-2/input1'
#        KEYBOARD_NAME = '  Mouse for Windows'
#        system_type = "GPD_GEN3"
#
#    ## ANBERNIC Devices
#    elif system_id in (
#            "Win600",
#            ):
#        CAPTURE_CONTROLLER = True
#        CAPTURE_KEYBOARD = True
#        CAPTURE_POWER = True
#        BUTTON_DELAY = 0.04
#        GAMEPAD_ADDRESS = 'usb-0000:02:00.3-5/input0'
#        GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
#        KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
#        KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
#        system_type = "ABN_GEN1"

# Captures keyboard events and translates them to virtual device events.
async def capture_aya_gen1_events(event):
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
    #active = keyboard_device.active_keys()
    #events = []
    #this_button = None
    #button_on = seed_event.value

    ## Debugging variables
    #if active != []:
    #    logging.debug(f"Active Keys: {active}, Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
    #    logging.debug(f"Queued events: {event_queue}")
    #elif active == [] and event_queue != []:
    #    logging.debug(f"Queued events: {event_queue}")

    ## Automatically pass default keycodes we dont intend to replace.
    #if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
    #    events.append(seed_event)
    #match system_type:

    #    case "AYA_GEN1":
    #        # BUTTON 1 (Default: Screenshot) WIN button
    #        # Temporarily RyzenAdj toggle/button6
    #        if active == [125] and button_on == 1 and button6 not in event_queue and shutdown == False:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await toggle_performance()

    #        # BUTTON 2 (Default: QAM) TM Button
    #        if active == [97, 100, 111] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #            await do_rumble(0, 150, 1000, 0)

    #        # BUTTON 3 (Default: ESC) ESC Button
    #        if active == [1] and seed_event.code == 1 and button_on == 1 and button3 not in event_queue:
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
    #            this_button = button3
    #        # BUTTON 3 SECOND STATE (Default: Toggle Gyro)
    #        elif seed_event.code == 1 and button_on == 2 and button3 in event_queue and gyro_device:
    #            event_queue.remove(button3)
    #            gyro_enabled = not gyro_enabled
    #            if gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)

    #        # BUTTON 4 (Default: OSK) KB Button
    #        if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
    #            event_queue.append(button4)
    #        elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
    #            this_button = button4

    #        # Handle L_META from power button
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
    #            shutdown = False

    #    case "AYA_GEN2" | "AYA_GEN3":
    #        # BUTTON 1 (Default: Screenshot/Launch Chiumera) LC Button
    #        if active == [87, 97, 125] and button_on == 1 and button1 not in event_queue and shutdown == False:
    #            if HAS_CHIMERA_LAUNCHER:
    #                event_queue.append(button7)
    #            else:
    #                event_queue.append(button1)
    #        elif active == [] and seed_event.code in [87, 97, 125] and button_on == 0 and button1 in event_queue:
    #            this_button = button1
    #        elif active == [] and seed_event.code in [87, 97, 125] and button_on == 0 and button7 in event_queue:
    #            event_queue.remove(button7)
    #            launch_chimera()

    #        # BUTTON 2 (Default: QAM) Small button
    #        if active in [[40, 133], [32, 125]] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [32, 40, 125, 133] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #            await do_rumble(0, 150, 1000, 0)

    #        # BUTTON 3 (Default: Toggle Gyro) RC + LC Buttons
    #        if active == [68, 87, 97, 125] and button_on == 1 and button3 not in event_queue and gyro_device:
    #            event_queue.append(button3)
    #            if button1 in event_queue:
    #                event_queue.remove(button1)
    #            if button4 in event_queue:
    #                event_queue.remove(button4)

    #        elif active == [] and seed_event.code in [68, 87, 97, 125] and button_on == 0 and button3 in event_queue and gyro_device:
    #            event_queue.remove(button3)
    #            gyro_enabled = not gyro_enabled
    #            if gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)

    #        # BUTTON 4 (Default: OSK) RC Button
    #        if active == [68, 97, 125] and button_on == 1 and button4 not in event_queue:
    #            event_queue.append(button4)
    #        elif active == [] and seed_event.code in [68, 97, 125] and button_on == 0 and button4 in event_queue:
    #            this_button = button4

    #        # BUTTON 5 (Default: MODE) Big button
    #        if active in [[96, 105, 133], [88, 97, 125]] and button_on == 1 and button5 not in event_queue:
    #            event_queue.append(button5)
    #        elif active == [] and seed_event.code in [88, 96, 97, 105, 125, 133] and button_on == 0 and button5 in event_queue:
    #            this_button = button5

    #        # BUTTON 6 (Default: Toggle RyzenAdj) Big button + Small Button
    #        if active == [32, 88, 97, 125] and button_on == 1 and button6 not in event_queue:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [32, 88, 97, 125] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await toggle_performance()

    #        # Handle L_META from power button
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
    #            shutdown = False

    #    case "AYA_GEN4":
    #        # This device class uses the same active events with different values for AYA SPACE, LC, and RC.
    #        if active == [97, 125]:

    #            # LC | Default: Screenshot / Launch Chimera
    #            if button_on == 102 and event_queue == []:
    #                if HAS_CHIMERA_LAUNCHER:
    #                    event_queue.append(button7)
    #                else:
    #                    event_queue.append(button1)
    #            # RC | Default: OSK
    #            elif button_on == 103 and event_queue == []:
    #                event_queue.append(button4)
    #            # AYA Space | Default: MODE
    #            elif button_on == 104 and event_queue == []:
    #                event_queue.append(button5)
    #        elif active == [] and seed_event.code in [97, 125] and button_on == 0 and event_queue != []:
    #            if button7 in event_queue:
    #                event_queue.remove(button7)
    #                launch_chimera()
    #            if button1 in event_queue:
    #                this_button = button1
    #            if button4 in event_queue:
    #                this_button = button4
    #            if button5 in event_queue:
    #                this_button = button5

    #        # Small button | Default: QAM
    #        if active == [32, 125] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [32, 125] and button_on == 0 and button2 in event_queue:
    #            this_button = button2

    #        # Small Button + big button | Default: Toggle Gyro
    #        if active == [32, 97, 125] and button_on == 1 and button3 not in event_queue:
    #            if button2 in event_queue:
    #                event_queue.remove(button2)
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code in [32, 97, 125] and button_on == 0 and button3 in event_queue:
    #            event_queue.remove(button3)
    #            gyro_enabled = not gyro_enabled
    #            if gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)

    #    case "OXP_GEN1": # Intel Models
    #        # BUTTON 1 (Possible dangerous fan activity!) Short press orange + |||||
    #        # UNUSED
    #        if active == [99, 125] and button_on == 1 and button6 not in event_queue:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [99, 125] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)

    #        # BUTTON 2 (Default: QAM) Short press orange
    #        if active == [32, 125] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #            await do_rumble(0, 150, 1000, 0)

    #        # BUTTON 3 (Default: Toggle Gyro) Short press orange + KB
    #        if active == [97, 100, 111] and button_on == 1 and button3 not in event_queue and gyro_device:
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code in [100, 111] and button_on == 0 and button3 in event_queue and gyro_device:
    #            event_queue.remove(button3)
    #            gyro_enabled = not gyro_enabled
    #            if gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)

    #        # BUTTON 4 (Default: OSK) Short press KB
    #        if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
    #            event_queue.append(button4)
    #        elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
    #            this_button = button4

    #        # Handle L_META from power button
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
    #            shutdown = False

    #    case "OXP_GEN2" | "OXP_GEN3": # AMD Models
    #        # BUTTON 1 (Possible dangerous fan activity!) Short press orange + |||||
    #        # Temporarily RyzenAdj toggle/button6
    #        if active == [99, 125] and button_on == 1 and button6 not in event_queue:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [99, 125] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await toggle_performance()

    #        # BUTTON 2 (Default: QAM) Long press orange
    #        if active == [34, 125] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in event_queue:
    #            this_button = button2

    #        # BUTTON 3 (Default: Toggle Gyro) Short press orange + KB
    #        if active == [97, 100, 111] and button_on == 1 and button3 not in event_queue and gyro_device:
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code in [100, 111] and button_on == 0 and button3 in event_queue and gyro_device:
    #            event_queue.remove(button3)
    #            gyro_enabled = not gyro_enabled
    #            if gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)

    #        # BUTTON 4 (Default: OSK) Short press KB
    #        if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
    #            event_queue.append(button4)
    #        elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
    #            this_button = button4

    #        # BUTTON 5 (Default: MODE) Short press orange
    #        if active == [32, 125] and button_on == 1 and button5 not in event_queue:
    #            event_queue.append(button5)
    #        elif active == [] and seed_event.code in [32, 125] and button_on == 0 and button5 in event_queue:
    #            this_button = button5
    #            await do_rumble(0, 150, 1000, 0)

    #        # Handle L_META from power button
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
    #            shutdown = False

    #    case "GPD_GEN1":
    #        # BUTTON 1 (Default: Screenshot)
    #        if active == [29, 56, 111] and button_on == 1 and button1 not in event_queue:
    #            event_queue.append(button1)
    #        elif active == [] and seed_event.code in [29, 56, 111] and button_on == 0 and button1 in event_queue:
    #            this_button = button1

    #        # BUTTON 2 (Default: QAM)
    #        if active == [1] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [1] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #    
    #        # BUTTON 6 (Default: Nothing)
    #        if active == [1, 29, 56, 111] and button_on == 1 and button6 not in event_queue:
    #            if button1 in event_queue:
    #                event_queue.remove(button1)
    #            if button2 in event_queue:
    #                event_queue.remove(button2)
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [1, 29, 56, 111] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)

    #    case "GPD_GEN2":
    #        # BUTTON 2 (Default: QAM)
    #        if active == [10] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [10] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #            await do_rumble(0, 150, 1000, 0)

    #        # BUTTON 3 Toggle gyro.
    #        if active == [11] and button_on == 1 and button3 not in event_queue:
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code in [11] and button_on == 0 and button3 in event_queue:
    #            logger.debug(f"gyro_enabled: {not gyro_enabled}")
    #            if gyro_enabled := not gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)
    #            continue

    #        # BUTTON 6 (Both buttons pressed, Default: Toggle RyzenAdj)
    #        if active == [10, 11] and button_on == 1 and button6 not in event_queue:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [10, 11] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await toggle_performance()

    #    case "GPD_GEN3":
    #        # BUTTON 2 (Default: QAM)
    #        if active == [99] and button_on == 1 and button2 not in event_queue:
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [99] and button_on == 0 and button2 in event_queue:
    #            this_button = button2
    #            await do_rumble(0, 150, 1000, 0)

    #        # BUTTON 3 Toggle gyro.
    #        if active == [119] and button_on == 1 and button3 not in event_queue:
    #            event_queue.append(button3)
    #        elif active == [] and seed_event.code in [119] and button_on == 0 and button3 in event_queue:
    #            logger.debug(f"gyro_enabled: {not gyro_enabled}")
    #            if gyro_enabled := not gyro_enabled:
    #                await do_rumble(0, 250, 1000, 0)
    #            else:
    #                await do_rumble(0, 100, 1000, 0)
    #                await asyncio.sleep(FF_DELAY)
    #                await do_rumble(0, 100, 1000, 0)
    #            continue

    #        # BUTTON 6 (Both buttons pressed, Default: Toggle RyzenAdj)
    #        if active == [99, 119] and button_on == 1 and button6 not in event_queue:
    #            event_queue.append(button6)
    #        elif active == [] and seed_event.code in [99, 119] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await toggle_performance()

    #    case "ABN_GEN1":

    #        # BUTTON 1 (BUTTON 4 ALT Mode) (Default: Screenshot) Long press KB
    #        if active == [24, 29, 125] and button_on == 2 and button1 not in event_queue:
    #            if button4 in event_queue:
    #                event_queue.remove(button4)
    #            if button5 in event_queue:
    #                event_queue.remove(button5)
    #            event_queue.append(button1)
    #        elif active == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button1 in event_queue:
    #            this_button = button1

    #        # BUTTON 2 (Default: QAM) Home key.
    #        if active == [34, 125] and button_on == 1 and button2 not in event_queue:
    #            if button5 in event_queue:
    #                event_queue.remove(button5)
    #            event_queue.append(button2)
    #        elif active == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in event_queue:
    #            this_button = button2

    #        # BUTTON 3, BUTTON 2 ALt mode (Defalt ESC)
    #        elif active == [1] and button_on == 1 and button3 not in event_queue:
    #            if button2 in event_queue:
    #                event_queue.remove(button2)
    #            event_queue.append(button3)
    #            await do_rumble(0, 75, 1000, 0)
    #        elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
    #            this_button = button3

    #        # BUTTON 4 (Default: OSK) Short press KB
    #        if active == [24, 29, 125] and button_on == 1 and button4 not in event_queue:
    #            if button5 in event_queue:
    #                event_queue.remove(button5)
    #            event_queue.append(button4)
    #        elif active == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button4 in event_queue:
    #            this_button = button4

    #        # BUTTON 5 (Default: GUIDE) Meta/Windows key.
    #        if active == [125] and button_on == 1 and button5 not in event_queue:
    #            event_queue.append(button5)
    #        elif active == [] and seed_event.code == 125 and button_on == 0 and button5 in event_queue:
    #            this_button = button5

    #        # BUTTON 5 ALT mode, toggle performance_mode
    #        if active == [1, 29, 42] and button_on == 1 and button6 not in event_queue:
    #            if button5 in event_queue:
    #                event_queue.remove(button5)
    #            event_queue.append(button6)
    #            await toggle_performance()

    #        elif active == [] and seed_event in [1, 29, 42] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #        
    #        # BUTTON 6 (UNUSED)
    #        if active == [24, 29, 34, 125] and button_on == 1 and button6 not in event_queue:
    #            if button2 in event_queue:
    #                event_queue.remove(button2)
    #            if button4 in event_queue:
    #                event_queue.remove(button4)
    #            if button5 in event_queue:
    #                event_queue.remove(button5)

    #            event_queue.append(button6)
    #            await do_rumble(0, 75, 1000, 0)
    #        elif active == [] and seed_event.code in [24, 29, 34, 125] and button_on == 0 and button6 in event_queue:
    #            event_queue.remove(button6)
    #            await do_rumble(0, 75, 1000, 0)
    #            await(FF_DELAY * 2)
    #            await do_rumble(0, 75, 1000, 0)

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

