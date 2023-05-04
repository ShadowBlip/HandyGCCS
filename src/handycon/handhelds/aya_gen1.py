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
from .. import common as com

event_queue = [] # Stores incoming button presses to block spam


def init_handheld():
    com.BUTTON_DELAY = 0.09
    com.CAPTURE_CONTROLLER = True
    com.CAPTURE_KEYBOARD = True
    com.CAPTURE_POWER = True
    com.GAMEPAD_ADDRESS = 'usb-0000:03:00.3-4/input0'
    com.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    com.GYRO_I2C_ADDR = 0x68
    com.GYRO_I2C_BUS = 1
    com.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    com.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global event_queue

    # Button map shortcuts for easy reference.
    button1 = com.button_map["button1"]  # Default Screenshot
    button2 = com.button_map["button2"]  # Default QAM
    button3 = com.button_map["button3"]  # Default ESC
    button4 = com.button_map["button4"]  # Default OSK
    button5 = com.button_map["button5"]  # Default MODE
    button6 = ["RyzenAdj Toggle"]
    button7 = ["Open Chimera"]

    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        events.append(seed_event)

    # BUTTON 1 (Default: Screenshot) WIN button
    # Temporarily RyzenAdj toggle/button6
    if active_keys == [125] and button_on == 1 and button6 not in event_queue and com.shutdown == False:
        event_queue.append(button6)
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and button6 in event_queue:
        event_queue.remove(button6)
        await com.toggle_performance()

    # BUTTON 2 (Default: QAM) TM Button
    if active_keys == [97, 100, 111] and button_on == 1 and button2 not in event_queue:
        event_queue.append(button2)
        await com.emit_now(seed_event, button2, 1)
        await com.do_rumble(0, 150, 1000, 0)
    elif active_keys == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in event_queue:
        event_queue.remove(button2)
        await com.emit_now(seed_event, button2, 0)

    # BUTTON 3 (Default: ESC) ESC Button
    if active_keys == [1] and seed_event.code == 1 and button_on == 1 and button3 not in event_queue:
        event_queue.append(button3)
    elif active_keys == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
        this_button = button3
    # BUTTON 3 SECOND STATE (Default: Toggle Gyro)
    elif seed_event.code == 1 and button_on == 2 and button3 in event_queue and com.gyro_device:
        event_queue.remove(button3)
        await com.toggle_gyro()

    # BUTTON 4 (Default: OSK) KB Button
    if active_keys == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
        event_queue.append(button4)
        await com.emit_now(seed_event, button4, 1)
    elif active_keys == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
        event_queue.remove(button4)
        await com.emit_now(seed_event, button4, 0)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and com.shutdown == True:
        com.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not com.last_button:
        for button_event in this_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 1)
            events.append(event)
        event_queue.remove(this_button)
        com.last_button = this_button

    # Clean up old button presses.
    elif com.last_button and not this_button:
        for button_event in com.last_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 0)
            events.append(event)
        com.last_button = None

    # Push out all events.
    if events != []:
        await com.emit_events(events)
