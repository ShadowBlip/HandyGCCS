#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import os
from evdev import ecodes as e

handycon = None


def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.09
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:c4:00.3-4/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'
    if os.path.exists('/sys/devices/platform/oxp-platform/tt_toggle'):
        command = f'echo 1 > /sys/devices/platform/oxp-platform/tt_toggle'
        os.popen(command, 'r', 1).read().strip()
        handycon.logger.info(f'Turbo button takeover enabled')
    else:
        handycon.logger.warn(
            f'Turbo takeover failed. Ensure you have the latest oxp-sensors driver installed.')


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]
    button2 = handycon.button_map["button2"]
    button3 = handycon.button_map["button3"]
    button4 = handycon.button_map["button4"]
    button5 = handycon.button_map["button5"]
    button6 = handycon.button_map["button6"]

    # Loop variables
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        handycon.emit_event(seed_event)

    # Handle missed keys.
    if active_keys == [] and handycon.event_queue != []:
        this_button = handycon.event_queue[0]

    # BUTTON 1 Short press orange + turbo
    if active_keys == [99, 125] and button_on == 1 and button1 not in handycon.event_queue:
        handycon.event_queue.append(button1)
    elif active_keys == [] and seed_event.code in [99] and button_on == 0 and button1 in handycon.event_queue:
        this_button = button1

    # BUTTON 2 (Default: QAM) Turbo Button
    if active_keys == [29, 56, 125] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
    elif active_keys == [] and seed_event.code in [29, 56] and button_on == 0 and button2 in handycon.event_queue:
        this_button = button2

    # BUTTON 3 (Default: ESC) Short press orange + KB
    if active_keys == [97, 100, 111] and button_on == 1 and button3 not in handycon.event_queue:
        handycon.event_queue.append(button3)
    elif active_keys == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button3 in handycon.event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Short press KB
    if active_keys == [24, 97, 125] and button_on == 1 and button4 not in handycon.event_queue:
        handycon.event_queue.append(button4)
    elif active_keys == [] and seed_event.code in [24, 97] and button_on == 0 and button4 in handycon.event_queue:
        this_button = button4

    # BUTTON 5 (Default: MODE) Short press orange
    if active_keys == [32, 125] and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
    elif active_keys == [] and seed_event.code in [32] and button_on == 0 and button5 in handycon.event_queue:
        this_button = button5

    # BUTTON 6 (Default: Launch Chimera) Long press orange
    if active_keys == [34, 125] and button_on == 1 and button6 not in handycon.event_queue:
        handycon.event_queue.append(button6)
    elif active_keys == [] and seed_event.code in [34] and button_on == 0 and button6 in handycon.event_queue:
        this_button = button6

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and handycon.event_queue == [] and handycon.shutdown == True:
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
