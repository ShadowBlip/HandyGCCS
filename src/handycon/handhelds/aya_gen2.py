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
    handycon.BUTTON_DELAY = 0.10
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button2 = handycon.button_map["button2"]  # Default QAM
    button5 = handycon.button_map["button5"]  # Default MODE

    ## Loop variables
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        await handycon.emit_events([seed_event])

    # BUTTON 2 (Default: QAM) Small Button
    if active_keys in [[40, 133], [32, 125]] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
        await handycon.emit_now(seed_event, button2, 1)
        await handycon.do_rumble(0, 150, 1000, 0)
    elif active_keys == [] and seed_event.code in [32, 40, 125, 133] and button_on == 0 and button2 in handycon.event_queue:
        handycon.event_queue.remove(button2)
        await handycon.emit_now(seed_event, button2, 0)

    # BUTTON 5 (Default: MODE) Big button
    if active_keys in [[96, 105, 133], [88, 97, 125]] and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
        await handycon.emit_now(seed_event, button2, 1)
    elif active == [] and seed_event.code in [88, 96, 97, 105, 125, 133] and button_on == 0 and button5 in handycon.event_queue:
        handycon.event_queue.remove(button5)
        await handycon.emit_now(seed_event, button5, 1)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False
