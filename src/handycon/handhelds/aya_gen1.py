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
    handycon.GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
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

    # BUTTON 1 (Default: Screenshot) WIN button
    if active_keys == [125] and button_on == 1 and button1 not in handycon.event_queue and handycon.shutdown == False:
        handycon.event_queue.append(button1)
        await handycon.emit_now(seed_event, button1, 1)
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and button6 in handycon.event_queue:
        handycon.event_queue.remove(button1)
        await handycon.emit_now(seed_event, button1, 0)

    # BUTTON 2 (Default: QAM) TM Button
    if active_keys == [97, 100, 111] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
        await handycon.emit_now(seed_event, button2, 1)
        await handycon.do_rumble(0, 150, 1000, 0)
    elif active_keys == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in handycon.event_queue:
        handycon.event_queue.remove(button2)
        await handycon.emit_now(seed_event, button2, 0)

    # BUTTON 3 (Default: ESC) ESC Button
    if active_keys == [1] and seed_event.code == 1 and button_on == 1 and button3 not in handycon.event_queue:
        handycon.event_queue.append(button3)
        await handycon.emit_now(seed_event, button3, 1)
    elif active_keys == [] and seed_event.code == 1 and button_on == 0 and button3 in handycon.event_queue:
        handycon.event_queue.remove(button3)
        await handycon.emit_now(seed_event, button3, 1)
    # BUTTON 3 SECOND STATE
    elif seed_event.code == 1 and button_on == 2 and button3 in handycon.event_queue and handycon.gyro_device:
        await handycon.emit_now(seed_event, button3, 2)

    # BUTTON 4 (Default: OSK) KB Button
    if active_keys == [24, 97, 125] and button_on == 1 and button4 not in handycon.event_queue:
        handycon.event_queue.append(button4)
        await handycon.emit_now(seed_event, button4, 1)
    elif active_keys == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in handycon.event_queue:
        handycon.event_queue.remove(button4)
        await handycon.emit_now(seed_event, button4, 0)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False
