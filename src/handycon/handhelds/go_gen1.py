#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.2
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:c2:00.3-3/input0'
    handycon.GAMEPAD_NAME = 'Generic X-Box pad'
    handycon.KEYBOARD_ADDRESS = 'usb-0000:c2:00.3-3/input3'
    handycon.KEYBOARD_NAME = '  Legion Controller for Windows  Keyboard'

# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button2 = handycon.button_map["button2"]  # Default QAM
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE

    ## Loop variables
    button_on = seed_event.value

    # Legion + a = QAM
    if active_keys == [29, 56, 111] and button_on == 1 and button2 not in handycon.event_queue:
        await handycon.handle_key_down(seed_event, button2)
    elif active_keys == [] and seed_event.code in [29, 56, 111] and button_on == 0 and button2 in handycon.event_queue:
        await handycon.handle_key_up(seed_event, button2)

    # Legion + x = keyboard
    if active_keys == [99] and button_on == 1 and button4 not in handycon.event_queue:
        await handycon.handle_key_down(seed_event, button4)
    elif active_keys == [] and seed_event.code in [99] and button_on == 0 and button4 in handycon.event_queue:
        await handycon.handle_key_up(seed_event, button4)

    # Legion + B = MODE
    if active_keys == [24, 29, 125] and button_on == 1 and button5 not in handycon.event_queue:
        await handycon.handle_key_down(seed_event, button5)
    elif active_keys == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button5 in handycon.event_queue:
        await handycon.handle_key_up(seed_event, button5)

    if handycon.last_button:
        await handycon.handle_key_up(seed_event, handycon.last_button)