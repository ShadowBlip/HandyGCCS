#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.09
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:00:14.0-7/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_ADDRESS = 'usb-0000:00:14.0-5/input0'
    handycon.KEYBOARD_NAME = '  Mouse for Windows'


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM

    ## Loop variables
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        await handycon.emit_events([seed_event])

    # BUTTON 1 (Default: Screenshot)
    if active_keys == [29, 56, 111] and button_on == 1 and button1 not in handycon.event_queue:
        handycon.event_queue.append(button1)
        await handycon.emit_now(seed_event, button1, 1)
    elif active_keys == [] and seed_event.code in [29, 56, 111] and button_on == 0 and button1 in handycon.event_queue:
        handycon.event_queue.remove(button1)
        await handycon.emit_now(seed_event, button1, 0)

    # BUTTON 2 (Default: QAM)
    if active_keys == [1] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
        await handycon.emit_now(seed_event, button2, 1)
    elif active_keys == [] and seed_event.code in [1] and button_on == 0 and button2 in handycon.event_queue:
        handycon.event_queue.remove(button2)
        await handycon.emit_now(seed_event, button2, 0)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False
