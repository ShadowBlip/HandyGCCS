#!/usr/bin/env python3
# This file is part of Handheld Game Console Controlelr System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import sys
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
    handycon.GAMEPAD_ADDRESS = 'usb-0000:00:14.0-9/input0'
    handycon.GAMEPAD_NAME = 'OneXPlayer Gamepad'
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'


async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM
    button3 = handycon.button_map["button3"]  # Default ESC
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE
    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        await handycon.emit_events([seed_event])

    # BUTTON 1 (Possible dangerous fan activity!) Short press orange + |||||
    if active_keys == [99, 125] and button_on == 1 and button1 not in handycon.event_queue:
        handycon.event_queue.append(button1)
    elif active_keys == [] and seed_event.code in [99, 125] and button_on == 0 and button1 in handycon.event_queue:
        this_button - button1

    # BUTTON 2 (Default: QAM) Short press orange
    if active_keys == [32, 125] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
    elif active_keys == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in handycon.event_queue:
        this_button = button2
        await handycon.do_rumble(0, 150, 1000, 0)

    # BUTTON 3 (Default: ESC) Short press orange + KB
    if active_keys == [97, 100, 111] and button_on == 1 and button3 not in handycon.event_queue:
        handycon.event_queue.append(button3)
    elif active_keys == [] and seed_event.code in [100, 111] and button_on == 0 and button3 in handycon.event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Short press KB
    if active_keys == [24, 97, 125] and button_on == 1 and button4 not in handycon.event_queue:
        handycon.event_queue.append(button4)
    elif active_keys == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in handycon.event_queue:
        this_button = button4

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not handycon.last_button:
        handycon.event_queue.remove(this_button)
        handycon.last_button = this_button
        await handycon.emit_now(seed_event, this_button, 1)

    # Clean up old button presses.
    elif handycon.last_button and not this_button:
        await handycon.emit_now(seed_event, handycon.last_button, 0)
        handycon.last_button = None
