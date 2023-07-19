#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import sys
from asyncio import sleep
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.11
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:64:00.3-3/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM
    button3 = handycon.button_map["button3"]  # Default ESC
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE

    ## Loop variables
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        await handycon.emit_events([seed_event])

    # This device class uses the same active_keys events with different values for AYA SPACE, LC, and RC.
    if active_keys == [29, 125]:

        # LC | Default: Screenshot / Launch Chimera
        if button_on == 102 and handycon.event_queue == []:
            handycon.event_queue.append(button1)
            await handycon.emit_now(seed_event, button1, 1)
        # RC | Default: OSK
        elif button_on == 103 and handycon.event_queue == []:
            handycon.event_queue.append(button4)
            await handycon.emit_now(seed_event, button4, 1)
        # AYA Space | Default: MODE
        elif button_on == 104 and handycon.event_queue == []:
            handycon.event_queue.append(button5)
            await handycon.emit_now(seed_event, button5, 1)

    elif active_keys == [] and seed_event.code in [97, 125] and button_on == 0 and handycon.event_queue != []:
        await sleep(handycon.BUTTON_DELAY)
        if button1 in handycon.event_queue:
            handycon.event_queue.remove(button1)
            await handycon.emit_now(seed_event, button1, 0)
        if button4 in handycon.event_queue:
            handycon.event_queue.remove(button4)
            await handycon.emit_now(seed_event, button4, 0)
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
            await handycon.emit_now(seed_event, button5, 0)

    # Small button | Default: QAM
    if active_keys == [32, 125] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
        await handycon.emit_now(seed_event, button2, 1)
    elif active_keys == [] and seed_event.code in [32, 125] and button_on == 0 and button2 in handycon.event_queue:
        await sleep(handycon.BUTTON_DELAY)
        handycon.event_queue.remove(button2)
        await handycon.emit_now(seed_event, button2, 0)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False
