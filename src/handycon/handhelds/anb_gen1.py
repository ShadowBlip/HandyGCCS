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
    handycon.BUTTON_DELAY = 0.04
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:02:00.3-5/input0'
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
    button6 = ["RyzenAdj Toggle"]
    button7 = ["Open Chimera"]

    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        events.append(seed_event)

    # BUTTON 1 (BUTTON 4 ALT Mode) (Default: Screenshot) Long press KB
    if active_keys == [24, 29, 125] and button_on == 2 and button1 not in handycon.event_queue:
        if button4 in handycon.event_queue:
            handycon.event_queue.remove(button4)
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
        handycon.event_queue.append(button1)
    elif active_keys == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button1 in handycon.event_queue:
        this_button = button1

    # BUTTON 2 (Default: QAM) Home key.
    if active_keys == [34, 125] and button_on == 1 and button2 not in handycon.event_queue:
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
        handycon.event_queue.append(button2)
    elif active_keys == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in handycon.event_queue:
        this_button = button2

    # BUTTON 3, BUTTON 2 ALt mode (Defalt ESC)
    elif active_keys == [1] and button_on == 1 and button3 not in handycon.event_queue:
        if button2 in handycon.event_queue:
            handycon.event_queue.remove(button2)
        handycon.event_queue.append(button3)
        await handycon.do_rumble(0, 75, 1000, 0)
    elif active_keys == [] and seed_event.code == 1 and button_on == 0 and button3 in handycon.event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Short press KB
    if active_keys == [24, 29, 125] and button_on == 1 and button4 not in handycon.event_queue:
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
        handycon.event_queue.append(button4)
    elif active_keys == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button4 in handycon.event_queue:
        this_button = button4

    # BUTTON 5 (Default: GUIDE) Meta/Windows key.
    if active_keys == [125] and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and button5 in handycon.event_queue:
        this_button = button5

    # BUTTON 5 ALT mode, toggle performance_mode
    if active_keys == [1, 29, 42] and button_on == 1 and button6 not in handycon.event_queue:
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
        handycon.event_queue.append(button6)
        await handycon.toggle_performance()

    elif active_keys == [] and seed_event in [1, 29, 42] and button_on == 0 and button6 in handycon.event_queue:
        handycon.event_queue.remove(button6)
    

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not handycon.last_button:
        for button_event in this_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 1)
            events.append(event)
        handycon.event_queue.remove(this_button)
        handycon.last_button = this_button

    # Clean up old button presses.
    elif handycon.last_button and not this_button:
        for button_event in handycon.last_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 0)
            events.append(event)
        handycon.last_button = None

    # Push out all events.
    if events != []:
        await handycon.emit_events(events)
